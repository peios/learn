---
title: Synthetic Events
description: Records eventd generates about itself, written straight to a shard and never through KMES — when, where and in what order.
---

Synthetic events are records eventd generates about itself. They are
written straight to a shard database and never touch KMES.
[*synthetic.synthetic-events-are-written-straight-to-a-shard-and-never-touch-kmes]

They carry no KMES header: no identity stamps, no sequence number, no
origin class. [*synthetic.synthetic-events-carry-no-kmes-header] What
they have is a wall-clock timestamp taken when eventd generated the
record, and an event type string prefixed `synthetic.` which is what
distinguishes them in the `events` table — no separate record-type
column exists (§3.1).
[*synthetic.a-synthetic-event-has-a-generation-timestamp-and-a-synthetic-prefixed-type]

## When they are generated

| Condition | Type |
|---|---|
| Lost events detected on a CPU | `synthetic.gap` (§2.5) [*synthetic.lost-events-on-a-cpu-emit-synthetic-gap] |
| eventd started and attached to KMES | `synthetic.startup` [*synthetic.starting-and-attaching-to-kmes-emits-synthetic-startup] |
| Graceful shutdown beginning | `synthetic.shutdown` [*synthetic.the-start-of-graceful-shutdown-emits-synthetic-shutdown] |
| A write to any store failed | `synthetic.storage_error` [*synthetic.a-failed-write-to-any-store-emits-synthetic-storage-error] |
| A configuration value changed at runtime | `synthetic.config_change` [*synthetic.a-runtime-configuration-change-emits-synthetic-config-change] |

Payload schemas for all five are in §3.2.

Note what is absent: there is no synthetic event for malformed
ingestion input.
[*synthetic.malformed-ingestion-input-emits-no-synthetic-event]
Authentication does not make admitted input trustworthy,
and emitting a durable record per bad datagram would hand a producer an
amplification primitive (PSPU §3.4). These five are conditions eventd
observed about itself, not reactions to what it was sent.

## Which shard

**CPU-specific** synthetic events — gap records — go to the shard
assigned to the CPU that generated them, handed to that writer thread
alongside that CPU's ordinary events.
[*synthetic.a-gap-record-goes-to-a-shard-of-the-cpu-that-generated-it] A
gap record travels with the events it describes.

**Daemon-wide** ones — startup, shutdown, configuration changes, storage
errors — go to shard 0 when shard 0 is writable, and otherwise to the
lowest-numbered writable active shard.
[*synthetic.daemon-wide-events-go-to-shard-0-else-the-lowest-numbered-writable-active-shard]
If no shard is writable at all the event is skipped, with the failure
logged to standard error.
[*synthetic.with-no-writable-shard-a-daemon-wide-event-is-skipped-and-logged-to-stderr]

A storage error is the case that needs the fallback. It describes a
failure on one particular shard but is itself a daemon-wide
notification, so it is not written to the failing shard unless that
shard has since been replaced and is writable again (§9.2) — writing the
record of a shard's failure into that shard would lose it exactly when
it matters.
[*synthetic.a-storage-error-skips-the-failing-shard-unless-it-is-writable-again]

These events are infrequent enough that concentrating them on shard 0
costs nothing measurable in balance.

## Storage and ordering

Synthetic events live in the same shard databases as KMES events and
participate in the same batching, the same retention and the same
queries.
[*synthetic.synthetic-events-share-the-shards-batching-retention-and-queries-of-kmes-events]
Access control treats their types like any other (§7.2), so
`Machine\System\eventd\Security\Events\synthetic` governs them.
[*synthetic.access-to-synthetic-events-is-governed-by-the-synthetic-events-key]

They are ordered by their eventd-assigned timestamp and take no part in
per-CPU sequence numbering.
[*synthetic.synthetic-events-are-ordered-by-timestamp-and-take-no-sequence-number]

That timestamp is when eventd **noticed**, not when the condition
occurred. [*synthetic.the-timestamp-records-when-eventd-noticed-not-when-it-occurred]
A gap record is stamped at detection, which may be long after
the events it describes were overwritten — and after a restart, may be
the first thing written in a new boot about events lost in the previous
one.
