---
title: Password and Lockout Policy
---

The password and lockout policy governs how credentials may be set and
how repeated failures are handled. The policy is held on the domain
object (§3.1); this section defines its fields and where they are
enforced. There is one policy per local namespace.

## Policy fields

The domain object's policy (§3.1) MUST define at least:

- **minimum length** and **complexity** requirements for a new password;
- **history depth** — how many prior verifiers are retained and refused
  on change (reuse prevention, via the `pw_history` records of §3.2);
- **maximum age** — after which a password is expired and MUST be
  changed before a token is minted (the `must_change_password` flow of
  §5.1);
- **lockout threshold** — the number of consecutive failed
  verifications that locks an account; and
- **lockout duration** — how long a locked account stays locked.

The normative default value for every field above is given in §9. For
this version there are **no composition rules** — strength is length- and
breach-list-based only — and the lockout counter resets on a successful
verification or once the lockout duration has elapsed.

## Enforcement points

Policy is enforced at two points.

**At set-password time** (administrative SetPassword or self-service
ChangePassword — §7.2). lpsd MUST reject (`POLICY_VIOLATION`) a new
password that violates the length/complexity requirements, matches any
retained `pw_history` verifier within the history depth, or appears in the
deployment's configured common/breached-password list (which MAY be
empty). On acceptance, lpsd records the new
verifier, appends the previous one to `pw_history` (evicting entries
beyond the depth), and stamps `pw_last_set`.

**At verify time** (the logon path — §5.1). lpsd MUST:

- treat a password older than the maximum age as expired and return
  `must_change_password` (§5.1) rather than `ok`;
- refuse verification for an account whose `lockout_until` is in the
  future, returning `denied` (§5.1); and
- maintain the **lockout accounting**: on a failed verification,
  increment `bad_pw_count` and stamp `last_bad_pw_time`; when
  `bad_pw_count` reaches the lockout threshold, set `lockout_until` to
  the current time plus the lockout duration; on a successful
  verification, reset `bad_pw_count` and clear `lockout_until`.

The built-in Administrator (RID 500) and any account on the recovery path
MUST be exempt from **remote-induced** lockout, so an attacker cannot deny
the recovery surface by failing logons against it (§8.2); local-console
attempts MAY still count.

## argon2id parameters and lazy upgrade

The argon2id cost parameters (§3.3) are themselves policy. When the
policy's parameters are stronger than those recorded in a stored
verifier, lpsd SHOULD **lazily re-wrap** the verifier — recompute it
with the current parameters — on the next successful verification (§5.1),
so verifiers strengthen over time without forcing a password reset.
Re-wrap MUST NOT change the password; it changes only the stored
representation.
