---
title: "lpsd.account.created"
description: "The record that an administrator created a local account with lps, or tried to."
---

- **Event type:** `lpsd.account.created`
- **Defined in:** `lpsd.evman`
- **Tier:** essential
- **Gating:** none — every request to create an account is recorded
- **Cardinality:** once per request

The record that an administrator created a local account with `lps`, or
tried to. The first account on a new machine is created this way too, by
the boot-time service that provisions it.

Essential because a new account is a new way in, and it is rare.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | required | The administrator: the user SID of the token that asked. |
| [`object.account.sid`](~peios/events/field-index/fields-object#object.account.sid) | `bin.sid` | when `outcome.success == true` | The new account. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | True once the account is durable. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | when `outcome.success == false` | The failure `lps` was told: `not-found` names a group that does not exist, `exists` an account name already in use, `invalid` a value the store refuses, `not-saved` a change that could not be made durable.<br><br>Values here (open set): `not-found` · `exists` · `invalid` · `internal` · `not-saved`. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `lpsd.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
