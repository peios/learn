---
title: Synthetic Events
description: The records eventd generates about itself, written straight to a shard and never through KMES — which shard, what the timestamp means, and what has no event at all.
---

Synthetic events are records eventd generates **about itself**. They are
written straight into a shard database and never touch KMES.

They carry no KMES header: no identity stamps, no sequence number, no
origin class. What they have is a wall-clock timestamp taken when eventd
generated the record, and a type string prefixed `synthetic.`, which is
what distinguishes them in the `events` table — there is no separate
record-type column.

| Condition | Type |
|---|---|
| Lost events detected on a CPU | `synthetic.gap` |
| eventd started and attached to KMES | `synthetic.startup` |
| Graceful shutdown beginning | `synthetic.shutdown` |
| A write to any store failed | `synthetic.storage_error` |
| A configuration value changed at runtime | `synthetic.config_change` |

Five, and no more. Payload schemas are in the eventd manual §3.2.

## There is no event for bad input

Deliberately. Log and metric datagrams arrive unauthenticated from
arbitrary local processes, and emitting a durable record per bad
datagram would hand every process an amplification primitive
(PSPU §3.4).

These five are conditions eventd observed **about itself**, not
reactions to what it was sent.

## Which shard they land in

**CPU-specific** — `synthetic.gap` — goes to the shard assigned to the
CPU that generated it, handed to that writer thread alongside that CPU's
ordinary events. A gap record travels with the events it describes.

**Daemon-wide** — startup, shutdown, config changes, storage errors — go
to shard 0 when shard 0 is writable, otherwise to the lowest-numbered
writable active shard. If no shard is writable, the event is skipped and
the failure is logged to standard error.

A storage error is why the fallback exists. It describes a failure on
one shard but is itself a daemon-wide notification, so it is not written
to the failing shard unless that shard has since been replaced and is
writable again. Writing the record of a shard's failure into that shard
would lose it exactly when it matters.

## The timestamp is when eventd noticed

Not when the condition occurred.

A `synthetic.gap` is stamped at **detection**, which may be long after
the events it describes were overwritten — and after a restart it may be
the first thing written in a new boot about events lost in the previous
one.

An investigation that treats a gap record's timestamp as the time of the
loss will look in the wrong window.

## Storage and ordering

Synthetic events live in the same shard databases as KMES events and
take part in the same batching, retention and queries. Access control
treats their types like any other, so
`Machine\System\eventd\Security\Events\synthetic` governs them.

They are ordered by their eventd-assigned timestamp and take no part in
per-CPU sequence numbering.
