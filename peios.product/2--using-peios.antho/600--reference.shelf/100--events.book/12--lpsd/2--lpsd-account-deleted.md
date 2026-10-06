---
title: "lpsd.account.deleted"
description: "The record that an administrator deleted a local account with lps, or tried to."
---

- **Event type:** `lpsd.account.deleted`
- **Defined in:** `lpsd.evman`
- **Tier:** essential
- **Gating:** none — every request to delete an account is recorded
- **Cardinality:** once per request

The record that an administrator deleted a local account with `lps`, or
tried to.

Essential because deleting an account is irreversible and rare: its SID is
never issued again, and every descriptor naming it names nobody.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | required | The administrator. |
| [`object.account.sid`](~peios/events/field-index/fields-object#object.account.sid) | `bin.sid` | optional | The account. Absent when no account had the name asked for. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | Whether the operation succeeded. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | when `outcome.success == false` | `invalid` is a deletion the store refuses, such as of the last administrator.<br><br>Values here (open set): `not-found` · `invalid` · `internal` · `not-saved`. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `lpsd.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
