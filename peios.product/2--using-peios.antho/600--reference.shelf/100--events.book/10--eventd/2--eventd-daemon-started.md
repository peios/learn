---
title: "eventd.daemon.started"
description: "The record that eventd started, attached to KMES and decided where to resume reading each CPU's ring."
---

- **Event type:** `eventd.daemon.started`
- **Defined in:** `eventd.evman`
- **Tier:** essential
- **Gating:** none — written on every start
- **Cardinality:** once per start of eventd

The record that eventd started, attached to KMES and decided where to resume
reading each CPU's ring. Like the other four types eventd writes about
itself (`eventd.daemon.stopped`, `eventd.events.lost`,
`eventd.store.quarantined` and `eventd.config.changed`), eventd writes it
straight into its event store and never through KMES. It
therefore has no `event.sequence` and no `emitter.*`: only `event.type`,
`event.time` (when eventd wrote it) and `event.boot.guid`.

Essential because the audit store starting is rare, and a start with no
matching stop is the evidence that eventd crashed. No emission policy
applies to it or to the other four: eventd is their emitter, and an
essential type is always written (PGSS <span>§</span>6.9). No KMES event of any of the
five types is stored, so `event.type` alone marks a record eventd wrote.

Replaces `synthetic.startup` (PEI-617). It carries no boot ID of its own,
because that is always the record's `event.boot.guid` (PEI-1390).

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`store.restarted`](~peios/events/field-index/fields-store#store.restarted) | `bool` | required | Whether this boot's events were already in the store when eventd started, which is to say eventd had already run during this boot and this start is a restart. |
| [`store.shard-count`](~peios/events/field-index/fields-store#store.shard-count) | `uint` | required | How many active event-store shards eventd is running with, after resolving its configured shard count. |
| [`store.resume.cpus`](~peios/events/field-index/fields-store#store.resume.cpus) | `uint[]` | required | The CPUs whose KMES rings eventd resumed reading at startup, one entry per logical CPU in ascending order. |
| [`store.resume.sequences`](~peios/events/field-index/fields-store#store.resume.sequences) | `uint[]` | required | For each CPU in `store.resume.cpus`, the highest event sequence of this boot already committed with no gap before it, which is where eventd resumed reading that CPU's ring. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `eventd.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
