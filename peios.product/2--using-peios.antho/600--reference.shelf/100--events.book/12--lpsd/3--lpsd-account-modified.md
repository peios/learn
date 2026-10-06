---
title: "lpsd.account.modified"
description: "The record that an account was changed: by an administrator with lps, or by the principal themselves where the self socket allows it."
---

- **Event type:** `lpsd.account.modified`
- **Defined in:** `lpsd.evman`
- **Tier:** essential
- **Gating:** none — every administrative change to an account, and every change of one's own display name, is recorded; a request that changes nothing is not
- **Cardinality:** once per request that changes something or fails

The record that an account was changed: by an administrator with `lps`,
or by the principal themselves where the self socket allows it. Which
change it was is `operation.name`.

A request that would leave the account as it was, such as enabling an
enabled account, changes nothing and writes no record.

Essential because an account's settings decide who can sign in and as
what, and they change rarely.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | required | The principal that asked: an administrator, or the account itself for `set-display-name`. |
| [`object.account.sid`](~peios/events/field-index/fields-object#object.account.sid) | `bin.sid` | optional | The account changed. Absent when no account had the name asked for. |
| [`object.group.sid`](~peios/events/field-index/fields-object#object.group.sid) | `bin.sid` | optional | For `set-primary-group`, the group made the account's primary group. |
| [`operation.name`](~peios/events/field-index/fields-operation#operation.name) | `str.enum` | required | The change, as `lps` names its command. `set-display-name` is the principal's own, through the self socket.<br><br>Values here (open set): `set-enabled` · `set-password` · `set-profile` · `set-display-name` · `set-primary-group` · `set-claim` · `remove-claim` · `rename` · `set-logon-types` · `key-add` · `key-remove` · `set-credential-policy`. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | Whether the operation succeeded. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | when `outcome.success == false` | `denied` is a disabled account changing its own display name.<br><br>Values here (open set): `not-found` · `exists` · `invalid` · `internal` · `denied` · `not-saved`. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `lpsd.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
