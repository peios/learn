---
title: "eventd.store.quarantined"
description: "The record that eventd found one of its stores corrupt, moved it aside and started a new one in its place."
---

- **Event type:** `eventd.store.quarantined`
- **Defined in:** `eventd.evman`
- **Tier:** essential
- **Gating:** none — every quarantine is recorded
- **Cardinality:** once per store or shard quarantined

The record that eventd found one of its stores corrupt, moved it aside and
started a new one in its place. Whatever the quarantined file held is no
longer queryable. This is what an operator alerts on.

It is written only for a quarantine. A store that is full, or a write that
fails for any other reason, writes none. The record goes to shard 0, else to
the lowest-numbered writable event shard, and never to a failed shard
until it has been replaced.

Replaces `synthetic.storage_error` (PEI-617).

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`store.kind`](~peios/events/field-index/fields-store#store.kind) | `str.enum` | required | Which of eventd's stores a record is about: the sharded event store, the log store or the metric store. |
| [`store.shard`](~peios/events/field-index/fields-store#store.shard) | `uint` | when `store.kind == event` | Absent for the log and metric stores, which are not sharded (PEI-1394). |
| [`outcome.detail`](~peios/events/field-index/fields-outcome#outcome.detail) | `str` | required | The error eventd found, as it describes it. Its wording is not stable. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `eventd.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
