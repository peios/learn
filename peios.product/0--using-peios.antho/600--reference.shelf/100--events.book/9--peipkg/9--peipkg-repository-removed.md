---
title: "peipkg.repository.removed"
description: "The record that peipkg removed a repository from its configuration and database, or tried to and failed."
---

- **Event type:** `peipkg.repository.removed`
- **Defined in:** `peipkg.evman`
- **Tier:** essential
- **Gating:** none — every repository removal is recorded
- **Cardinality:** once per repository remove

The record that peipkg removed a repository from its configuration and
database, or tried to and failed. Removing a repository that is not
configured succeeds.

Replaces `peipkg.repo-remove`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | required | The user SID of the effective token the operation ran under. |
| [`object.repository.name`](~peios/events/field-index/fields-object#object.repository.name) | `str` | required | The repository the event is about, by the name it is configured under. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | Whether the operation succeeded. |
| [`outcome.detail`](~peios/events/field-index/fields-outcome#outcome.detail) | `str` | optional | The error as peipkg reported it to the operator. Absent on success. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peipkg.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
