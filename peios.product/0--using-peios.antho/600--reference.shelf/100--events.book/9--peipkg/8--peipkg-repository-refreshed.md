---
title: "peipkg.repository.refreshed"
description: "The record that peipkg refreshed the metadata of its configured repositories."
---

- **Event type:** `peipkg.repository.refreshed`
- **Defined in:** `peipkg.evman`
- **Tier:** standard
- **Gating:** none
- **Cardinality:** once per refresh command

The record that peipkg refreshed the metadata of its configured
repositories. One refresh covers every repository it was asked to; a failure
of one does not stop the others, so a refresh can partly succeed. A refresh
that fails before it reaches any repository writes nothing.

Replaces `peipkg.refresh`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | required | The user SID of the effective token the operation ran under. |
| [`operation.succeeded-count`](~peios/events/field-index/fields-operation#operation.succeeded-count) | `uint` | required | Repositories refreshed. |
| [`operation.failed-count`](~peios/events/field-index/fields-operation#operation.failed-count) | `uint` | required | Repositories whose refresh failed. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | False when any repository failed to refresh. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peipkg.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
