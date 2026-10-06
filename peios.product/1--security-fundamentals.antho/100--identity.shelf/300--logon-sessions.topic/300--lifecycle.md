---
title: Session lifecycle
type: concept
description: A logon session is created by authd at successful authentication and destroyed when its last token reference drops — there is no kernel revocation primitive, so authd signs a session out by ending its processes.
related:
  - peios/logon-sessions/overview
  - peios/logon-sessions/logon-types
  - peios/security-fundamentals/tokens/lifecycle
  - peios/auditing/overview
  - peios/inspecting/overview
---

A session's life is bracketed by two kernel events: a successful `kacs_create_logon_session` call that brings it into existence, and the implicit drop of its last token reference that destroys it. There is nothing in between — no resize, no rename, no kernel-side timeout. Sessions are simple objects whose lifecycle is driven entirely by the tokens attached to them.

This page covers the three phases that matter: creation, destruction, and forced sign-out (ending a session before the person signs out themselves, which authd does on request).

## Creation

A session is created by `kacs_create_logon_session`. The call requires `SeTcbPrivilege`, so in practice the only callers are **authd** (every interactive and network sign-in) and **peinit** (services launched during boot before authd is available).

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

The session now exists but has no tokens. It is in a transient state: any subsequent `kacs_create_token` call that references this `session_id` in its `auth_id` field bumps the count, and the session is "live".

authd's flow is "create session, then mint primary token referencing it". Between those two calls the session has no tokens, and a strict "destroy when refcount hits zero" rule would tear it down before authd's second call. So the kernel only destroys a session on a refcount that transitions from positive to zero, not on one that has been zero since creation. After a successful first attachment, normal destruction rules apply.

The consequence is that a session no token ever attaches to is **never reaped**. Nothing times it out. If authd's mint fails after it created the session, authd rolls the session back itself with `kacs_destroy_empty_logon_session`, which refuses any session that has a live token. An empty session left by some other caller stays in the listing until the machine restarts, or until a caller holding `SeTcbPrivilege` destroys it — `logonse destroy` does exactly that.

## The boot sessions

Two sessions exist without ever passing through `kacs_create_logon_session`:

| Session | ID | Created by |
|---|---|---|
| **SYSTEM session** | 999 | Direct kernel init |
| **Anonymous session** | 998 | Direct kernel init |

Both are constructed in early boot, before any process exists. The SYSTEM session is attached to the kernel's bootstrap SYSTEM token, which init inherits and which propagates through every process until authd assigns real tokens. The Anonymous session backs the well-known Anonymous token used by Anonymous-level impersonation.

Neither is ever destroyed during the running system's lifetime. They are reference-counted like any other session, but their references never drop to zero — the SYSTEM token always has at least one attachment somewhere, and the Anonymous token is a kernel-internal singleton.

## Destruction

A session is destroyed when its token reference count, having been positive, drops to zero. The kernel:

1. Removes the session from the session table.
2. Tears down any linked-pair association it was holding (see [Elevation and linked tokens](~peios/security-fundamentals/tokens/elevation)).
3. Emits a `kacs.session.destroyed` event through KMES.

The event carries enough information for consumers to clean up downstream state:

| Field | What it is |
|---|---|
| `object.session.id` | The destroyed session's ID. |
| `object.session.user.sid` | The principal. |
| `object.session.logon-type` | The type, by name: `interactive`, `network`, `batch`, `service`, `network-cleartext`, `new-credentials` or `remote-interactive`. |
| `object.session.auth-package` | The auth package string. |
| `object.session.logon-time` | The session's creation time, in nanoseconds. |

The consumers are audit pipelines, accounting tools and session-aware services. **authd is not one of them**: it keeps no per-session state — no tickets, no cached credentials, no handle on the tokens it mints — so there is nothing of its own for it to release when a session goes. An authority that did hold session-scoped state would subscribe here to learn when to drop it.

The event is fire-and-forget — there is no acknowledgement, no retry, no replay. A consumer that misses an event misses it.

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

For an ordinary logout, this happens naturally: the user's shell exits, its child processes exit, and anything that was handed a descriptor for one of the session's tokens closes it. Once all of those happen, the kernel sees refcount zero, fires the event, frees the session. (authd holds nothing: it closes its descriptor for a token the moment it has handed the token over.)

## Forced sign-out: there is no kernel call

There is **no syscall** to forcibly end a session. No `kacs_destroy_session`, no `kacs_kill_session`. The session model is reference-counted, and the only way to end one is to ensure every reference drops. (The one destroy syscall that exists, `kacs_destroy_empty_logon_session`, is a rollback primitive for empty sessions only — it refuses with `-EBUSY` any session that still has live tokens. This is what `logonse destroy` wraps.)

Forced sign-out — an administrator deciding that a person should not be signed in any more, or a person signing themselves out everywhere — is therefore a userspace operation, and **authd** performs it. A program that signs somebody out — a task manager, a command-line tool — asks with a `SessionEnd` request on `/run/logon.sock` ([PGSS §2.22](~peios/logon/ending-a-session)) and does none of the work itself. authd:

1. Checks that the caller may. Anyone may end their own session, when they are a person signed in as themselves. Ending anyone else's needs the right granted by the `SessionEndSecurity` descriptor on `Machine\Generic\Authn\Policy` — by default SYSTEM and Administrators have it. Nobody may end SYSTEM's session (999), Anonymous's (998), or a service's: a service is stopped through the service manager.
2. Finds every process whose **primary** token belongs to the session: it walks `/proc`, opens each process by pidfd, and reads `auth_id` from that process's primary token. A thread that is only impersonating a token of the session — a service answering the person's request — is not in the session, and is left alone.
3. Sends each `SIGTERM` through its pidfd, so the signal reaches the process whose token was read even if its pid has since been reused. It waits up to five seconds for them to exit, then sends `SIGKILL` to what is left.
4. Walks again, because a process may have forked during the grace period, and repeats — at most three rounds.
5. Answers with how many processes it ended and how many still hold the session, and records the request, who made it and the result as an `authd.session.ended` event.

Once the last process exits, the session reaches refcount zero, the event fires, and the person is signed out.

### What the audit trail shows

A forced sign-out leaves two records, from two components:

- **`authd.session.ended`**, written by authd when it has finished the rounds. It names who asked (`subject.token.sid`), the session (`object.session.id`), whose session it was (`object.session.user.sid`) and its logon type. `outcome.success` is false, with `outcome.reason` `processes-remaining`, when something still held the session after the last round. It is an essential event, so the emission policy cannot switch it off.
- **`kacs.session.destroyed`**, written by the kernel when the last reference drops. It cannot say who asked: only authd knows that.

A **refused** request is not an authd event. Whether a caller may end another principal's session is an access check against the `SessionEndSecurity` descriptor, and KACS records that decision as `kacs.audit.access.checked`, with `object.kind` `authd-session-end`, when the descriptor's SACL asks it to. To audit refused sign-outs, give the descriptor a failure-audit ACE, such as `S:(AU;FA;0x1;;;WD)`. Ending one's own session needs no grant, so it runs no check. Neither does a request for SYSTEM's, Anonymous's or a service's session, which is always refused.

A program that ends the session it is itself running in is ended with it. authd therefore answers such a request **first**, saying how many processes it found, and does the work afterwards.

What this cannot reach:

- **A token descriptor held outside the session.** Token descriptors can be passed between processes; a process outside the session holding one keeps the session alive after every process in it has gone. authd walks processes, not descriptors, so it neither finds nor counts these.
- **A thread impersonating a token of the session**, by design (step 2). The session lasts until that thread reverts.
- **A process that has exited but not been reaped.** It holds its token until its parent reaps it, and counts as remaining until then.

There are two reasons the kernel does not provide a direct revoke:

- **No graceful path.** A "kill the session" syscall would need to choose between killing every process holding any of its tokens (loss of work, possible data corruption) and merely refusing future operations, which leaves running processes with stale identity. User-space can stage the teardown — send SIGTERM, wait, escalate — in a way the kernel cannot.
- **Reference-counted identity is the simpler model.** The rule "a session exists if and only if a token exists referencing it" has one fewer transition than "a session exists if and only if its tokens exist AND no revocation has been requested". Fewer transitions, fewer corner cases.

The cost is that revocation is observable: a thread can detect that its session is about to die (its parent process getting a TERM) before the kernel sees the session as gone. Anything that wants to enforce immediate revocation needs to design around that — typically by minimising the work a thread can do between receiving a signal and actually exiting.

## Inspecting active sessions

The kernel exposes the active session list at `/sys/kernel/security/kacs/sessions`. The file is a text listing, one session per line:

```
logon_session_id=1042 user_sid=<hex-encoded SID> logon_type=2 auth_package=<hex-encoded name> created_at=...
```

Lines are stable in their leading fields; new fields may be appended in a future version, so consumers must ignore unknown trailing fields. The file's own SD grants read to `BUILTIN\Administrators` and `SYSTEM` only.

This is the canonical way to enumerate sessions. Other tools — `eventd` consumers, `who`-equivalents, session monitors — can read it directly or through helpers that wrap it. See [Inspecting tokens, sessions, and processes](~peios/inspecting/overview).

## Where to go next

For the token-side half of the same story — the references whose rise and fall drive a session's life — read [Token lifecycle](~peios/security-fundamentals/tokens/lifecycle).

To list, create, and destroy sessions from a shell, read [The logonse command](~peios/logon-sessions/logonse-command).
