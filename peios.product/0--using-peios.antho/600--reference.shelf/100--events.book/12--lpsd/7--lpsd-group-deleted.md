---
title: "lpsd.group.deleted"
description: "The record that an administrator deleted a local group with lps, or tried to."
---

- **Event type:** `lpsd.group.deleted`
- **Defined in:** `lpsd.evman`
- **Tier:** essential
- **Gating:** none — every request to delete a group is recorded
- **Cardinality:** once per request

The record that an administrator deleted a local group with `lps`, or
tried to.

Essential because deleting a group removes every grant made to it, and it
is rare.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | required | The administrator. |
| [`object.group.sid`](~peios/events/field-index/fields-object#object.group.sid) | `bin.sid` | optional | The group. Absent when no group had the name asked for. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | Whether the operation succeeded. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | when `outcome.success == false` | Why the operation resolved the way it did.<br><br>Values here (open set): `not-found` · `invalid` · `internal` · `not-saved`. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `lpsd.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
