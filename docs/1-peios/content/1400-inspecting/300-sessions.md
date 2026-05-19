---
title: Inspecting sessions
type: concept
description: Active logon sessions are exposed at /sys/kernel/security/kacs/sessions as a text listing. Each token references its session via auth_id, so finding the session associated with a process means querying its primary token's auth_id and looking up that ID in the listing. This page covers the listing format, the lookup pattern, and how to track session lifecycle.
related:
  - peios/inspecting/overview
  - peios/inspecting/tokens
  - peios/logon-sessions/overview
  - peios/logon-sessions/lifecycle
---

Logon sessions are the kernel's records of authentication events. Every token belongs to one session; every running thread is acting under a token; therefore every running thread is associated with a session. Inspecting the system's active sessions tells you who is currently signed in, in what mode, when, and which authentication mechanism brought them in.

The primary inspection surface is **`/sys/kernel/security/kacs/sessions`** — a text-format pseudo-file that lists every active session. This page covers the listing format, the standard pattern for finding a session from a token, and how to track session lifecycle through the audit stream.

## The sessions pseudo-file

`/sys/kernel/security/kacs/sessions` is a text file produced by the kernel on each read. Each line describes one active session:

```
session_id=<decimal-u64> user_sid=<lowercase-hex-sid> logon_type=<decimal-u32> auth_package=<lowercase-hex-utf8> created_at=<decimal-u64>
```

Fields are space-separated, in `key=value` form. The format is stable for the listed fields; consumers should **ignore unknown additional fields**, which future versions may append.

| Field | Type | Meaning |
|---|---|---|
| `session_id` | decimal u64 | The session's LUID. Same as the `auth_id` recorded on every token belonging to this session. |
| `user_sid` | lowercase hex | The SID of the principal who signed in. |
| `logon_type` | decimal u32 | The logon type. See [Logon types](~peios/logon-sessions/logon-types). |
| `auth_package` | lowercase hex of UTF-8 | The auth-package name (e.g. "Kerberos", "NTLM", "local") encoded as lowercase hex of the UTF-8 bytes. |
| `created_at` | decimal u64 | Creation timestamp (kernel-internal monotonic units). |

The `user_sid` and `auth_package` fields are hex-encoded for parser stability — the SID is a binary structure, and the auth-package name could in principle contain characters that complicate text parsing. Hex encoding is uniform.

### Access rule

The file's SD grants read to `BUILTIN\Administrators` and `SYSTEM` only. A non-administrative caller will get `EACCES` on `open()`. This is intentional: the listing reveals every active session on the machine, including their identities and timestamps, which is information you do not want a low-privileged process to read.

For a sysadmin running as `root` (which projects to a token in the administrative group), reading the file is straightforward. For service accounts that need session enumeration capability, the right approach is to grant the relevant SID access via the file's SD, not to weaken the default protection.

### Bootstrap sessions

Two sessions exist before authd is up:

| Session ID | Use |
|---|---|
| 0 | The SYSTEM session. Attached to init, inherited by every early-boot process. Stays present for the lifetime of the system. |
| 998 | The Anonymous session. Backs the singleton Anonymous token. |

Both appear in the listing. They are not bugs; their presence is the normal state of any running system.

## Finding a session from a token

The standard pattern: given a thread or process, find its session.

1. **Open the token.** For a thread, use `/proc/<pid>/task/<tid>/token`. For a process's primary, use `/proc/<pid>/token`. For yourself, use `kacs_open_self_token` or `/sys/kernel/security/kacs/self`.
2. **Query `TokenStatistics`** via `KACS_IOC_QUERY`. The response includes `auth_id` (the session's LUID).
3. **Look up `auth_id`** in `/sys/kernel/security/kacs/sessions` to find the matching `session_id`. The line gives you the session's full details.

This is the standard "which session is this process in" query. The session ID is the key; the listing has the rest.

For programmatic enumeration ("for each running process, which session is it in"):

```
for each pid in /proc/*:
  for each tid in /proc/<pid>/task/*:
    open /proc/<pid>/task/<tid>/token
    query TokenStatistics, get auth_id
    cross-reference with the sessions listing
```

This produces a complete picture of which thread is in which session. The [`logonse`](~peios/logon-sessions/logonse-command) command uses exactly this pattern — it walks the running processes to render which processes belong to which session.

## Tracking session lifecycle

Sessions are created and destroyed dynamically. The listing always reflects the *current* state; to track changes over time you need to either poll the listing or subscribe to session lifecycle events.

### Session creation

The kernel does not emit a kernel-level event when a session is created — there is no `logon-session-created` event in v0.20 audit. Tracking creations requires either:

- Periodic polling of `/sys/kernel/security/kacs/sessions` and comparing against the previous snapshot.
- Hooking into authd, which is the only thing that creates sessions and could in principle emit a higher-level event. (This is an authd integration concern, not a kernel one.)
- Listening for the audit events that fire on successful authentications — these are emitted by authd and consumed via KMES.

For most monitoring purposes, the audit stream from authd is the right source. The kernel-level sessions listing tells you "what is right now"; the audit stream tells you "what happened recently".

### Session destruction

The kernel **does** emit a `logon-session-destroyed` event when a session loses its last token reference. The event includes the session ID, the user SID, the logon type, the auth-package name, and the creation timestamp — enough to reconstruct what the session was.

The event is documented in [Events and transport](~peios/auditing/events-and-transport). Tools that want to track session lifecycle subscribe to this event via KMES and write a record on each occurrence.

The pattern: at session creation (detected via authd or via polling), record the start; at the `logon-session-destroyed` event, record the end. The two together give you a complete session log.

## Inspecting an individual session

A session ID is a small thing — a u64 — but the listing line gives you everything currently knowable about the session from the kernel's perspective. There is no separate "session detail" query that returns more than what the listing provides.

If you need detail beyond what the listing offers (the privileges granted at sign-in, the policy that applied, the auth-package's specific authentication flow), the source is authd's own state, accessible via authd's APIs. The kernel records the session existence and minimal metadata; authd records the rest.

This separation is the standard kernel/userspace split. The kernel knows the session exists, who it is for, when it was created, and what auth-package created it. authd knows what happened during authentication.

## Counting tokens per session

A session can have many tokens. The number of tokens belonging to a session is the count of:

- Primary tokens attached to processes whose `auth_id` matches.
- Impersonation tokens currently installed on threads whose `auth_id` matches.
- Token fds open against tokens with that `auth_id`.

Counting these from the outside is awkward — there is no "tokens per session" query. The standard way is to walk `/proc/*/token` and `/proc/*/task/*/token`, query `TokenStatistics` on each, and count matches. This is what session-revocation tooling does (authd specifically).

The reason for the awkward enumeration: each token is a separate kernel object, and there is no per-session index. The kernel knows tokens reference sessions (via `auth_id`); it does not maintain a reverse index of which tokens reference which session. Walking the running processes is the way to find tokens that exist.

A token held only by a file descriptor with no associated running process — e.g., a token fd passed via SCM_RIGHTS to a recipient that hasn't installed it — is not enumerable by walking `/proc`. Such tokens still keep the session alive (refcount), but their existence is not visible to a session-enumeration tool. They will reveal themselves only when the holding process tries to use them.

## Session expiry

A session's `created_at` is set at creation; there is no `expires_at` in the listing. Sessions do not expire on a kernel timer. A session lives as long as its tokens have references; it ends when the last token reference drops.

Token `expiration` (a field on each token) is set by authd but **not enforced by the kernel** in v0.20. A token can have an expiration time in the past and still be valid for AccessCheck. The token's session continues to exist regardless of any token's expiration value.

If a deployment needs strict session timeouts, the enforcement is in userspace. authd can monitor `created_at` against a policy maximum and revoke sessions whose age exceeds the limit. Revocation is the userspace-coordinated process described in [Session lifecycle](~peios/logon-sessions/lifecycle): authd walks `/proc/*/token`, finds tokens with the target `auth_id`, kills the holding processes.

The lack of kernel-side timer enforcement is a deliberate simplification. Adding kernel timers for session expiry would push expiry policy into the kernel; keeping it in userspace lets administrators define their own rules.
