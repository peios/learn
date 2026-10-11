---
title: "lpsd.group.member.added"
description: "The record that an administrator added an account to a group with lps, or tried to."
---

- **Event type:** `lpsd.group.member.added`
- **Defined in:** `lpsd.evman`
- **Tier:** essential
- **Gating:** none — every request to add a membership is recorded; one that already held is not
- **Cardinality:** once per request that changes something or fails

The record that an administrator added an account to a group with `lps`,
or tried to. The group may be a well-known one: adding an account to
`BUILTIN\Administrators` is recorded here.

Essential because a membership is a grant of everything granted to the
group, and memberships change rarely.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | required | The administrator. |
| [`object.account.sid`](~peios/events/field-index/fields-object#object.account.sid) | `bin.sid` | optional | The account. Absent when no account had the name asked for. |
| [`object.group.sid`](~peios/events/field-index/fields-object#object.group.sid) | `bin.sid` | optional | The group. Absent when no group had the name asked for. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | Whether the operation succeeded. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | when `outcome.success == false` | Why the operation resolved the way it did.<br><br>Values here (open set): `not-found` · `invalid` · `internal` · `not-saved`. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `lpsd.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
