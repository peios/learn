---
title: Session lifecycle
type: concept
description: A logon session is created by authd at successful authentication and destroyed when its last token reference drops. This page covers the creation path, the destruction event, and how userspace implements forced logout — there is no kernel revocation primitive.
related:
  - peios/logon-sessions/overview
  - peios/logon-sessions/logon-types
  - peios/tokens/lifecycle
  - peios/auditing/overview
  - peios/inspecting/overview
---

A session's life is bracketed by two kernel events: a successful `kacs_create_session` call that brings it into existence, and the implicit drop of its last token reference that destroys it. There is nothing in between — no resize, no rename, no kernel-side timeout. Sessions are simple objects whose lifecycle is driven entirely by the tokens attached to them.

This page covers the three phases that matter: creation, destruction, and revocation (the userspace pattern for forcing a session to end before the user logs out voluntarily).

## Creation

A session is created by `kacs_create_session`. The call requires `SeTcbPrivilege`, so in practice the only callers are **authd** (every interactive and network sign-in) and **peinit** (services launched during boot before authd is available).

The call takes a wire-format specification with three fields:

| Field | Meaning |
|---|---|
| `logon_type` | The type — Interactive, Network, Service, Batch, etc. See [Logon types](~peios/logon-sessions/logon-types). |
| `auth_package` | A string identifying the authentication mechanism (informational). |
| `user_sid` | The principal who signed in. |

The kernel:

1. Validates the inputs (well-formed SID, recognised logon type, sane string lengths).
2. Allocates a session object with a fresh `session_id` LUID.
3. Stamps `created_at`.
4. Derives the logon SID `S-1-5-5-X-Y` from the session ID.
5. Initialises the session's token reference count at zero.
6. Returns the new session ID to the caller.

The session now exists but has no tokens. It is in a transient state: any subsequent `kacs_create_token` call that references this `session_id` in its `auth_id` field bumps the count, and the session is "live". If no token is ever created against the session — vanishingly rare — the session stays at refcount zero and is reaped after a brief grace period.

The grace period is what avoids a race: authd's flow is "create session, then mint primary token referencing it". Between those two calls the session has no tokens, and a strict "destroy when refcount hits zero" rule would tear it down before authd's second call. The kernel solves this by only triggering destruction on a refcount that *transitions* from positive to zero, not on a refcount that has been zero since creation. After a successful first attachment, normal destruction rules apply.

## The boot sessions

Two sessions exist without ever passing through `kacs_create_session`:

| Session | ID | Created by |
|---|---|---|
| **SYSTEM session** | 0 | Direct kernel init |
| **Anonymous session** | 998 | Direct kernel init |

Both are constructed in early boot, before any process exists. The SYSTEM session is attached to the kernel's bootstrap SYSTEM token, which init inherits and which propagates through every process until authd assigns real tokens. The Anonymous session backs the well-known Anonymous token used by Anonymous-level impersonation.

Neither is ever destroyed during the running system's lifetime. They are reference-counted like any other session, but their references never drop to zero — the SYSTEM token always has at least one attachment somewhere, and the Anonymous token is a kernel-internal singleton.

## Destruction

A session is destroyed when its token reference count, having been positive, drops to zero. The kernel:

1. Removes the session from the session table.
2. Tears down any linked-pair association it was holding (see [Elevation and linked tokens](~peios/tokens/elevation)).
3. Emits a `logon-session-destroyed` event through KMES.

The event carries enough information for consumers to clean up downstream state:

| Field | What it is |
|---|---|
| `session_id` | The destroyed session's ID. |
| `user_sid` | The principal. |
| `logon_type` | The type. |
| `auth_package` | The auth package string. |
| `created_at` | The session's creation timestamp. |

The most important consumer of this event is **authd itself**. authd subscribes to `logon-session-destroyed` because it needs to release session-scoped state of its own: Kerberos tickets, cached directory data, any per-session credentials it has been holding. Without the subscription, authd would have no way to know that a session it created is gone.

Other consumers (audit pipelines, accounting tools, session-aware services) may also subscribe. The event is fire-and-forget — there is no acknowledgement, no retry, no replay. A consumer that misses an event misses it.

## What ends a session

A session ends only when every reference to it drops. The references are:

- Every primary token attached to a process with `auth_id = session_id`.
- Every impersonation token currently installed on any thread.
- Every token fd open on a process's behalf.
- The linked-pair association, while it exists.

Practically, this means a session ends when:

1. Every process running on a token of the session has exited.
2. Every thread that was impersonating a token of the session has reverted or exited.
3. Every fd held on a token of the session has been closed.
4. The linked pair, if any, has been dissolved.

The fourth condition is satisfied automatically when the session reaches refcount zero — the kernel dissolves the pair as part of destruction. The first three are user-space's responsibility.

For an ordinary logout, this happens naturally: the user's shell exits, child processes exit, the authority broker process closes its hold on the Full token. Once all of those happen, the kernel sees refcount zero, fires the event, frees the session.

## Revocation: there is no kernel call

There is **no syscall** to forcibly end a session. No `kacs_destroy_session`, no `kacs_kill_session`. The session model is reference-counted, and the only way to end one is to ensure every reference drops.

Forced logout — an administrator deciding that user X should not be signed in any more — is therefore a userspace operation. The pattern, implemented by authd:

1. Walk `/proc/*/token` to find tokens whose `auth_id` matches the target session.
2. For each matching token, identify the process holding it.
3. Send the appropriate signal to terminate the process (typically SIGTERM with a grace period, then SIGKILL if needed).
4. Continue until no processes hold any token of the session.

Once the last process exits, the session reaches refcount zero, the event fires, and the user is logged out.

The kernel cooperates by exposing `auth_id` through token query interfaces (specifically the `TokenStatistics` query class via `KACS_IOC_QUERY`) and by providing the per-PID token handles at `/proc/<pid>/token`. authd uses both to do the walk.

There are two reasons the kernel does not provide a direct revoke:

- **No graceful path.** A "kill the session" syscall would need to choose between killing every process holding any of its tokens (loss of work, possible data corruption) and merely refusing future operations (which leaves running processes with stale identity, also bad). User-space can stage the teardown — send SIGTERM, wait, escalate — in a way the kernel cannot.
- **Reference-counted identity is the simpler model.** The rule "a session exists iff a token exists referencing it" has one fewer transition than "a session exists iff its tokens exist AND no revocation has been requested". Fewer transitions, fewer corner cases.

The cost is that revocation is observable: a thread can detect that its session is about to die (its parent process getting a TERM) before the kernel sees the session as gone. Anything that wants to enforce immediate revocation needs to design around that — typically by minimising the work a thread can do between receiving signal and actually exiting.

## Inspecting active sessions

The kernel exposes the active session list at `/sys/kernel/security/kacs/sessions`. The file is a text listing, one session per line:

```
session_id=42 user_sid=s-1-5-21-... logon_type=2 auth_package=Kerberos created_at=...
```

Lines are stable in their leading fields; new fields may be appended to a future version, so consumers must ignore unknown trailing fields. The file's own SD grants read to `BUILTIN\Administrators` and `SYSTEM` only.

This is the canonical way to enumerate sessions. Other tools — `eventd` consumers, `who`-equivalents, session monitors — can read it directly or through helpers that wrap it. See [Inspecting tokens, sessions, and processes](~peios/inspecting/overview).
