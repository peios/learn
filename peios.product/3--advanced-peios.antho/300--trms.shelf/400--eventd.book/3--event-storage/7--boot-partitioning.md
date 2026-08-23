---
title: Boot Partitioning
description: Every stored record carries a boot_id — what it is for, where it is stored, how uniqueness is assured, and how a boundary is detected.
---

Every record eventd stores — every event, every log line, every raw
metric sample — carries a `boot_id`: a 16-byte GUID identifying the boot
that produced it. peinit assigns it at each boot and eventd reads it at
startup.

Derived metric rollups are the exception. They are boot-agnostic
aggregates and carry no `boot_id` (§5.6).

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
(PSPU §3.25). Rollups stay boot-agnostic scalars, so a boot-filtered
metric query is served from raw samples and never from a rollup.

## Uniqueness

Within one boot an event is uniquely identified by
`(cpu_id, sequence)`. Across boots, `boot_id` supplies the
disambiguating dimension, and the triple
`(boot_id, cpu_id, sequence)` is globally unique.

## Detecting the boundary

At startup eventd reads the current boot ID from peinit, then searches
every readable event shard database — historical shards included — for
committed rows carrying it.

**No committed rows for this boot.** This is the boot's first eventd
start. eventd resets every per-CPU sequence tracker to 0, records the
new boot ID for all subsequent writes to all three stores, and emits
`synthetic.startup` with `restart` false.

**Committed rows exist.** eventd crashed and peinit restarted it within
the same boot. eventd restores each CPU's tracker from the maximum
non-null `sequence` for `(boot_id, cpu_id)` across every readable shard,
with CPUs having no rows resuming at 0; continues writing under the
existing boot ID; and emits `synthetic.startup` with `restart` true.

The two cases are distinguished by the data itself rather than by any
flag eventd persisted. That is the point: a flag would have to be
written at a moment eventd might not reach, and a crash is precisely the
case where it did not.

Committed rows are the authority throughout. The metadata database's
sequence checkpoints and the previous `synthetic.shutdown` payload
record the same numbers, and both are diagnostic — neither is consulted
for resumption (§2.2, §3.5).
