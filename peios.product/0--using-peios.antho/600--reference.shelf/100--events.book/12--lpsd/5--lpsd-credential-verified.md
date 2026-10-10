---
title: "lpsd.credential.verified"
description: "The record that lpsd checked a credential for a logon authd relayed to it, and what it found."
---

- **Event type:** `lpsd.credential.verified`
- **Defined in:** `lpsd.evman`
- **Tier:** standard
- **Gating:** none — every credential lpsd checks for a logon is recorded
- **Cardinality:** once per logon lpsd decides; probing which SSH keys an account would accept writes none

The record that lpsd checked a credential for a logon authd relayed to it,
and what it found. It says what the wire must not: authd and the
originator are told only "authentication failed" whether the account does
not exist or the credential was wrong, and `outcome.reason` here tells
them apart for whoever may read the audit trail.

The account is named by SID when it exists. The name the caller typed is
never recorded, so a failure against a name lpsd does not hold carries no
account at all; `authd.logon.attempted` is the same logon as the authority
saw it.

Standard rather than essential because a machine exposed to a network can
be asked to check credentials far more often than it signs anyone in.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | required | lpsd itself, the principal that checked the credential: the user SID of lpsd's own token, which is its service account. |
| [`object.account.sid`](~peios/events/field-index/fields-object#object.account.sid) | `bin.sid` | optional | The account the credential was checked for. Absent when lpsd holds no account by the name it was asked about. |
| [`operation.name`](~peios/events/field-index/fields-operation#operation.name) | `str.enum` | required | What was checked. `none` is an account whose policy is that it signs in with no credential, asserted without asking for one.<br><br>Values here (open set): `password` · `ssh-key` · `none`. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | True when lpsd told authd who the principal is. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | when `outcome.success == false` | `not-permitted` is an account whose credential policy does not allow the kind of credential offered, or a key the account does not hold.<br><br>Values here (open set): `no-such-account` · `wrong-credential` · `disabled` · `not-permitted`. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `lpsd.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
