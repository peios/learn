---
title: "lpsd.group.created"
description: "The record that an administrator created a local group with lps, or tried to."
---

- **Event type:** `lpsd.group.created`
- **Defined in:** `lpsd.evman`
- **Tier:** essential
- **Gating:** none — every request to create a group is recorded
- **Cardinality:** once per request

The record that an administrator created a local group with `lps`, or
tried to.

Essential because groups are what descriptors grant to, and they are
created rarely.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | required | The administrator. |
| [`object.group.sid`](~peios/events/field-index/fields-object#object.group.sid) | `bin.sid` | when `outcome.success == true` | The new group. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | Whether the operation succeeded. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | when `outcome.success == false` | Why the operation resolved the way it did.<br><br>Values here (open set): `exists` · `invalid` · `internal` · `not-saved`. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `lpsd.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
