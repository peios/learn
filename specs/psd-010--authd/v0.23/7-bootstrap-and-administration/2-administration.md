---
title: Account Administration
---

Account administration is **source-shaped** and therefore goes directly
to a source (§2.2), except for the source-transparent self-service verbs
that the broker forwards. For lpsd, administration is served on
`/run/lpsd.sock` (§6.1).

## Administration operations

lpsd's administration interface MUST provide at least:

- **CreateUser** — allocate a RID from `rid_counter`, assign an
  `object_guid` and POSIX projection, write the user record (§3.2).
- **SetPassword** (administrative reset) — set the `password` factor
  without the old password, subject to the password policy (§3.4).
- **CreateGroup**, **AddMember**, **RemoveMember** — manage groups and
  membership (§3.2).
- **EnableAccount** / **DisableAccount** — toggle `account_flags`.

Each operation is gated against the peer token (§6.2) by an
**account-admin privilege**. Administration clients route between sources
by namespace via a shared client library (§2.2); a domain source serves
the corresponding directory operations, which need not match lpsd's
shape.

## ChangePassword (self-service, forwarded)

ChangePassword is source-transparent and is forwarded by authd (§2.2,
§6.3). lpsd's self-service ChangePassword verb MUST be authorized by one
of:

- **knowledge of the old password** — the request carries old and new
  passwords; lpsd verifies the old before applying the new (open to any
  caller, consistent with the knowledge-gates model of §6.3); or
- **an account-admin privilege** — administrative reset without the old
  password.

This single verb serves both ordinary password changes and the
`must_change_password` flow (§5.1): a TCB login frontend relays the
user's old and new passwords after a `must_change_password` result, and
lpsd's verification of the old password is the authorization — no
special privilege is required.

## Propagation

Administrative changes take effect at the principal's **next logon**: a
token reflects logon-time identity and is immutable (PSD-004). Live
sessions are unaffected until re-logon or forced logout (§6.3). authd
and the administration interface therefore need no coupling for
propagation.
