---
title: LogonSessions and Revocation
---

## LogonSessions

A LogonSession is a lightweight kernel object identified by a LUID (`auth_id`). Every token references a LogonSession.

- **Creation** — authd creates a LogonSession (via KACS syscall) at authentication time, before creating the token. The LogonSession object contains: LogonSession ID (LUID), logon type (Interactive, Network, Service, etc.), user SID, authentication package name (e.g., "Kerberos", "Negotiate"), and creation timestamp. A logon SID (`S-1-5-5-X-Y`) is derived from the LogonSession ID.
- **Association** — each token's `auth_id` references its LogonSession. Multiple tokens MAY share a LogonSession (linked pairs, tokens derived via duplication).
- **Cleanup** — when the last token referencing a LogonSession is freed (refcount drops to zero), the kernel destroys the LogonSession object and emits a LogonSession-destroyed event via the event subsystem (`event_emit`). authd subscribes to these events and uses them to clean up associated credentials (cached Kerberos tickets, etc.).

LogonSessions are bookkeeping. No access control decision depends on the LogonSession — AccessCheck MUST NOT consult `auth_id`. The `interactivity_scope` field is similarly metadata; the kernel stores it and returns it on query but no kernel security mechanism evaluates it.

## Token expiration

The token's `expiration` field carries a timestamp. In v0.20, this field MUST NOT be enforced by AccessCheck — it is informational only.

Token lifetime is governed by reference counting, not by the expiration timestamp. Tokens exist as long as at least one reference (process credential or open file descriptor) exists.

## LogonSession invalidation

A LogonSession MAY be marked dead via `kacs_invalidate_logon_session`. This is a kernel-level revocation primitive.

### Mechanism

The LogonSession object carries a `dead` flag, initially false. `kacs_invalidate_logon_session(auth_id)` sets this flag atomically. The flag is one-way — a dead LogonSession cannot be revived.

### Effects

- **AccessCheck.** EvaluateSecurityDescriptor checks `token.logon_session.dead` before the impersonation level gate (step 0). If the LogonSession is dead, AccessCheck returns `ERROR_ACCESS_DENIED` immediately. This blocks all live access checks: new opens, path-based operations, O_PATH live checks, process SD evaluations.
- **Snapshot checks.** Use-time operations that check the fd's cached granted mask are NOT affected. An already-open fd continues working until the fd is closed or the process terminates. The handle model applies: authority is on the handle.
- **Token creation.** `kacs_create_token` rejects an `auth_id` that references a dead LogonSession. No new tokens can enter the system referencing a dead LogonSession.
- **Token installation.** `KACS_IOC_INSTALL` rejects tokens whose LogonSession is dead. A dead-LogonSession token cannot become a process's primary token.
- **Token operations.** Query, adjust, duplicate, and filter continue to work on tokens referencing dead LogonSessions. These operations are not access-control decisions.
- **Event.** When a LogonSession is invalidated, the kernel emits a LogonSession-invalidated event via `event_emit`.

### Revocation workflow

1. authd decides a LogonSession must end (admin request, security incident, account deletion, or user-initiated logoff).
2. authd calls `kacs_invalidate_logon_session(auth_id)`. All future access checks against the LogonSession's tokens fail immediately.
3. authd enumerates processes whose tokens carry the target `auth_id` or `interactivity_scope` by walking `/proc/*/token` and inspecting TokenStatistics (which includes `auth_id`). No dedicated enumeration syscall is needed.
4. authd requests process termination — via peinit for supervised services, via signals for user processes.
5. Processes terminate, dropping their token references.
6. When the last reference drops, the LogonSession object is cleaned up.

Step 2 closes the SCM_RIGHTS gap: even if a token fd is passed to a process in another LogonSession (before or after enumeration), all live access checks against that token fail. The handle model means existing open fds retain their cached grants, but no new resource access can be established.

> [!INFORMATIVE]
> Token file descriptors can be passed between processes via IPC. A token reference held by a process outside the target LogonSession will survive the LogonSession's process termination. The LogonSession-dead check ensures these orphaned tokens cannot be used for new access checks, even though existing open fds retain their cached granted masks.
