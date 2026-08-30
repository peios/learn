---
title: Boot Partitioning
description: Every stored record carries a boot_id — what it is for, where it is stored, how uniqueness is assured, and how a boundary is detected.
---

Every record eventd stores — every event, every log line, every raw
metric sample — carries a `boot_id`: a 16-byte GUID identifying the boot
that produced it. Linux assigns it at boot; eventd reads
`/proc/sys/kernel/random/boot_id` at startup, validates the UUID text,
and stores the corresponding PCDS-layout GUID.

## What it is for

**Disambiguation.** KMES per-CPU sequence numbers restart at zero each
boot. Without a boot ID, sequence 42 from one boot is indistinguishable
from sequence 42 from the next, and every gap calculation across a
reboot would be wrong.

**Lifecycle.** Retention can delete a whole boot as a unit rather than
scanning by timestamp, and a boot is the natural unit to delete: its
events, its gaps and its startup record go together (§3.6).

## Where it is stored

| Store | Column |
|---|---|
| Event | `events.boot_id`, every row |
| Log | `logs.boot_id`, every row |
| Metric | `samples.boot_id`, every row |

The log store records it because log output can mean different things
across boots — a service configured differently at boot time says
different things.

The metric store records it **per sample** but does not make it part of
series identity (§5.2). A time series stays continuous across a reboot,
which is what a chart of CPU usage across a restart should show, and a
query that wants one boot's worth filters for it explicitly
(PSPU §3.25).

## Uniqueness

Within one boot an event is uniquely identified by
`(cpu_id, sequence)`. Across boots, `boot_id` supplies the
disambiguating dimension, and the triple
`(boot_id, cpu_id, sequence)` is globally unique.

## Detecting the boundary

At startup eventd reads the kernel boot ID, then searches every readable
event shard database — historical shards included — for committed rows
or receipt ranges carrying it.

**No committed rows or receipts for this boot.** This is the boot's
first successful eventd start. Coverage for every CPU begins before
sequence 1, the new boot ID is used for subsequent writes to all three
stores, and `synthetic.startup` carries `restart` false.

**Committed rows or receipts exist.** eventd was previously ready in the
same boot. It merges receipt coverage per `(boot_id, cpu_id)`, reconciles
that coverage with surviving ring records (§2.2), continues under the
same boot ID, and emits `synthetic.startup` with `restart` true.

The two cases are distinguished by the data itself rather than by any
flag eventd persisted. That is the point: a flag would have to be
written at a moment eventd might not reach, and a crash is precisely the
case where it did not.

Committed receipt ranges are the sequence authority. Committed event
rows still establish that eventd previously ran when no receipt was yet
needed. The metadata database's sequence checkpoints and the previous
`synthetic.shutdown` payload are diagnostic — neither is consulted for
recovery (§2.2, §3.5).

The receipt key is sound only while KMES sequence numbers do not restart
under one kernel boot ID. v0.23 therefore requires KMES to remain
initialised for the whole boot. A future KMES ABI may add a stream
generation GUID to make module reloads distinguishable without relying
on that lifecycle invariant.
