---
title: "lpsd.credential.changed"
description: "The record that a principal changed their own password, or added or removed one of their own SSH keys, through authd (PSPU §2.21, §2.23), or tried to and was refused."
---

- **Event type:** `lpsd.credential.changed`
- **Defined in:** `lpsd.evman`
- **Tier:** essential
- **Gating:** none — every change of an account's own credential is recorded, and every refusal once the account is known
- **Cardinality:** once per change conversation that reaches the account

The record that a principal changed their own password, or added or
removed one of their own SSH keys, through authd (PSPU <span>§</span>2.21, <span>§</span>2.23), or
tried to and was refused. A change an administrator makes with `lps` is
`lpsd.account.modified`.

Essential because a changed credential is how an account changes hands,
and it is rare.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | required | The principal that asked, as authd vouched for them from their token. The same SID as `object.account.sid`: only one's own credential can be changed this way. |
| [`object.account.sid`](~peios/events/field-index/fields-object#object.account.sid) | `bin.sid` | required | The SID of the account a record is about: a principal a principal source holds, whose credential was checked or changed, or which was created, deleted or modified. |
| [`operation.name`](~peios/events/field-index/fields-operation#operation.name) | `str.enum` | required | Which operation was attempted.<br><br>Values here (open set): `password` · `ssh-key-added` · `ssh-key-removed`. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | True once the change is durable. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | when `outcome.success == false` | `no-credential` is an account with no password to prove itself with; `superseded` a password that changed between the rounds of the conversation; `rejected` a new password or key the store refused; `conversation-limit` too many unusable new passwords; `not-saved` a change the store could not make durable, so it was not applied.<br><br>Values here (open set): `no-such-account` · `disabled` · `no-credential` · `wrong-credential` · `superseded` · `rejected` · `conversation-limit` · `not-saved`. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `lpsd.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
