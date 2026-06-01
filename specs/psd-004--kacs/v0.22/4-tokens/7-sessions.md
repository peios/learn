---
title: LogonSessions and Revocation
---

## LogonSessions

A LogonSession is a lightweight kernel object identified by a LUID (`auth_id`). Every token references a LogonSession.

- **Creation** — authd creates a LogonSession (via KACS syscall) at authentication time, before creating the token. The LogonSession object contains: LogonSession ID (LUID), logon type (Interactive, Network, Service, etc.), user SID, authentication package name (e.g., "Kerberos", "Negotiate"), and creation timestamp. A logon SID (`S-1-5-5-X-Y`) is derived from the LogonSession ID.
- **Association** — each token's `auth_id` references its LogonSession. Multiple tokens MAY share a LogonSession (linked pairs, tokens derived via duplication).
- **Cleanup** — when the last token referencing a LogonSession is freed (refcount drops to zero), the kernel destroys the LogonSession object and emits a `logon-session-destroyed` event through KMES. authd subscribes to these events and uses them to clean up associated credentials (cached Kerberos tickets, etc.).
- **Empty-LogonSession rollback** — if authd creates a LogonSession but no token ever becomes live for that LogonSession, authd MAY call `kacs_destroy_empty_logon_session`. The kernel MUST require SeTcbPrivilege. The call MUST succeed only if the LogonSession exists, has zero live tokens, has no linked-token state, and has no other in-flight kernel references. On success, the kernel destroys the LogonSession object and emits the same `logon-session-destroyed` event used for normal last-token cleanup. A nonexistent LogonSession MUST fail with `-ENOENT`. A LogonSession with any live token, linked-token state, or other in-flight kernel reference MUST fail with `-EBUSY`.

LogonSessions are bookkeeping. No access control decision depends on the LogonSession — AccessCheck MUST NOT consult `auth_id`. The `interactivity_scope` field is similarly metadata; the kernel stores it and returns it on query but no kernel security mechanism evaluates it.

## Token expiration

The token's `expiration` field carries a timestamp. In v0.20, this field MUST NOT be enforced by AccessCheck — it is informational only.

Token lifetime is governed by reference counting, not by the expiration timestamp. Tokens exist as long as at least one reference (process credential or open file descriptor) exists.

## Revocation

KACS does not provide a token revocation primitive. There is no "invalidate token X" syscall, and there is no syscall that destroys a LogonSession while tokens still reference it. `kacs_destroy_empty_logon_session` is only an authd rollback primitive for a LogonSession that has not acquired live tokens.

LogonSession termination is userspace coordination:

1. authd decides a LogonSession must end (admin request, security incident, account deletion, or user-initiated logoff).
2. authd enumerates processes whose tokens carry the target `auth_id` or `interactivity_scope` by walking `/proc/*/token`, opening each node's query-only inspection handle, and inspecting `TokenStatistics` (which includes `auth_id`). No dedicated enumeration syscall is needed.
3. authd requests process termination — via peinit for supervised services, via signals for user processes.
4. Processes terminate, dropping their token references.
5. When the last reference drops, the LogonSession object is cleaned up.

> [!INFORMATIVE]
> Token file descriptors can be passed between processes via IPC. A token reference held by a process outside the target LogonSession will survive the LogonSession's process termination. authd must account for this when enumerating token holders.

> [!INFORMATIVE]
> Kernel-side LogonSession invalidation (marking a LogonSession as dead so that new access checks against its tokens fail immediately) is a future enhancement. The mechanism would be a dead flag on the LogonSession object, checked during AccessCheck. This is not part of v0.22.
