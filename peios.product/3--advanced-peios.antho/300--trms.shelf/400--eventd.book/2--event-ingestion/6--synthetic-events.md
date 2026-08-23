---
title: Synthetic Events
description: Records eventd generates about itself, written straight to a shard and never through KMES — when, where and in what order.
---

Synthetic events are records eventd generates about itself. They are
written straight to a shard database and never touch KMES.

They carry no KMES header: no identity stamps, no sequence number, no
origin class. What they have is a wall-clock timestamp taken when eventd
generated the record, and an event type string prefixed `synthetic.`
which is what distinguishes them in the `events` table — no separate
record-type column exists (§3.1).

## When they are generated

| Condition | Type |
|---|---|
| Lost events detected on a CPU | `synthetic.gap` (§2.5) |
| eventd started and attached to KMES | `synthetic.startup` |
| Graceful shutdown beginning | `synthetic.shutdown` |
| A write to any store failed | `synthetic.storage_error` |
| A configuration value changed at runtime | `synthetic.config_change` |

Payload schemas for all five are in §3.2.

Note what is absent: there is no synthetic event for malformed
ingestion input. Log and metric datagrams arrive unauthenticated from
arbitrary local processes, and emitting a durable record per bad
datagram would hand every process an amplification primitive
(PSPU §3.4). These five are conditions eventd observed about itself, not
reactions to what it was sent.

## Which shard

**CPU-specific** synthetic events — gap records — go to the shard
assigned to the CPU that generated them, handed to that writer thread
alongside that CPU's ordinary events. A gap record travels with the
events it describes.

**Daemon-wide** ones — startup, shutdown, configuration changes, storage
errors — go to shard 0 when shard 0 is writable, and otherwise to the
lowest-numbered writable active shard. If no shard is writable at all
the event is skipped, with the failure logged to standard error.

A storage error is the case that needs the fallback. It describes a
failure on one particular shard but is itself a daemon-wide
notification, so it is not written to the failing shard unless that
shard has since been replaced and is writable again (§9.2) — writing the
record of a shard's failure into that shard would lose it exactly when
it matters.

These events are infrequent enough that concentrating them on shard 0
costs nothing measurable in balance.

## Storage and ordering

Synthetic events live in the same shard databases as KMES events and
participate in the same batching, the same retention and the same
queries. Access control treats their types like any other (§7.2), so
`Machine\System\eventd\Security\Events\synthetic` governs them.

They are ordered by their eventd-assigned timestamp and take no part in
per-CPU sequence numbering.

That timestamp is when eventd **noticed**, not when the condition
occurred. A gap record is stamped at detection, which may be long after
the events it describes were overwritten — and after a restart, may be
the first thing written in a new boot about events lost in the previous
one.
