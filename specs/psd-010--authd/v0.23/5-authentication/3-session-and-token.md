---
title: Session and Token Mint
---

With the token spec assembled (§5.2), authd mints the logon session and
the token via the KACS syscalls of PSD-004. Only authd performs these
calls (§2.1).

## Order: session before token

authd MUST create the session before the token, because the token
references the session:

1. **`kacs_create_logon_session`** with `{ logon_type, auth_package, user_sid }`
   (lpsd's `auth_package` is `"Peios.Local"` — §9). This requires
   `SeTcbPrivilege`. The kernel allocates a session id
   (LUID), derives the logon SID, and returns the session id. The
   session begins at token-reference-count zero, protected by the
   kernel's creation grace period (PSD-004).
2. authd sets the token spec's `auth_id` to the new session id.
3. **`kacs_create_token`** with the assembled spec. This requires
   `SeCreateTokenPrivilege`. The kernel validates the spec, injects the
   logon SID into the group list, assigns the token id, and returns a
   token fd. The first token referencing the session takes its
   reference count positive, ending the grace period.

authd MUST NOT supply the logon SID in the token spec; the kernel
injects it.

## Rollback

If `kacs_create_token` fails after `kacs_create_logon_session` has succeeded,
authd MUST roll the session back with **`kacs_destroy_empty_logon_session`**
so that no empty session is leaked. authd MUST treat the logon as failed
and audit it accordingly.

## Token spec defaults

Unless overridden by the resolved principal or policy, authd MUST set the
following on the token spec (values consolidated in §9): `default_dacl` =
`ACCESS_ALLOWED` ACEs (each `AceFlags` = 0) in the order **owner, SYSTEM,
then `Administrators`** — the last only when the token carries
`S-1-5-32-544` — each granting `GENERIC_ALL`; the DACL sets only
`SE_DACL_PRESENT` (no other control flags, notably not
`SE_DACL_PROTECTED`); `owner` = the user SID;
`primary_group` from the principal's `primary_group_rid`; and
`mandatory_policy` = `NO_WRITE_UP`. The privilege set and its
enabled-states come from §5.2, the integrity level from §5.2/§9, and the
POSIX projection from the idmap (§3.6): `projected_uid` = the principal's
id; `projected_gid` = the **primary group's** id; and
`projected_supplementary_gids` = the projection to ids of the token's
**group** SIDs only — the primary group, the resolved principal's groups,
and the local and implicit groups authd added in §5.2 step 2 — and
**never** the user SID. That
list is **de-duplicated, sorted ascending by id, includes the primary
group's id, and omits any SID on the no-id list (§9)** (no-id SIDs never
receive a fallback id). If the assembled group set — the token's group
SIDs **excluding** the kernel-injected logon SID — exceeds **1023**
(PSD-004's 1024-entry limit less the kernel's reserved logon-SID slot),
authd MUST fail the logon with `TOKEN_TOO_LARGE` (§6.4) **before** calling
`kacs_create_logon_session` (so no session is created or rolled back), and
MUST NOT silently truncate it.

## Returning the token; the requester launches

authd MUST return the token to the client as a **token fd passed over
the client socket** (`SCM_RIGHTS`), together with the session id and any
advisory fields (e.g. `must_change_password` is handled earlier; a
password-expiry warning MAY be returned alongside `ok`). The returned fd
carries `TOKEN_ALL_ACCESS` (PSD-004); the requester MUST install it
promptly, close its own copy, and MUST NOT pass it across a privilege
boundary.

The **requester**, not authd, installs the token and launches: a login
frontend installs the returned token as the primary token of the user's
first process and execs it; peinit installs a service's token on the
service it launches. authd MUST NOT launch processes itself. After
handing off the fd, authd drops its own reference; the running process's
attachment is what keeps the session alive.

## Session-scoped state

For a local password logon authd holds no per-session secret. authd
MUST nonetheless subscribe to the `logon-session-destroyed` event
(PSD-004) so that the uniform per-session cleanup hook exists; for a
local logon the handler is effectively empty. (Domain sessions, which
hold Kerberos tickets, are deferred — §8.)
