---
title: "store.*"
description: "Every field the evman catalogue defines under store: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `store`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="store.committed.cpus"></a>`store.committed.cpus`

- **Type:** `uint[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `eventd.evman`

The CPUs whose KMES rings eventd was reading when it shut down, one entry per
logical CPU in ascending order. Parallel to `store.committed.sequences`.

**Carried by:**

No event carries this field yet.

## <a id="store.committed.sequences"></a>`store.committed.sequences`

- **Type:** `uint[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `eventd.evman`

For each CPU in `store.committed.cpus`, the highest event sequence of this
boot committed with no gap before it, taken during a graceful shutdown after
eventd had stopped reading the rings and committed everything it had read.
Parallel to `store.committed.cpus`. It is diagnostic only: when
eventd next starts it works out where to resume from the store itself, never
from this record.

**0 does not always mean nothing was committed.** It means no unbroken run
from sequence 1 exists for that CPU, as in `store.resume.sequences`, but
eventd also writes 0 for every CPU when it cannot read its record of what was
committed at shutdown. A shutdown record whose sequences are all 0 after a
busy boot is that failure, not an empty store.

**Carried by:**

No event carries this field yet.

## <a id="store.kind"></a>`store.kind`

- **Type:** `str.enum`
- **Values:** `event` · `log` · `metric`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `eventd.evman`

Which of eventd's stores a record is about: the sharded event store, the log
store or the metric store. On a storage error this is the store eventd found
corrupt and quarantined, and with `store.shard` it is the field worth alerting
on. The set is open because the store eventd keeps its own metadata in may be
reported on separately later.

**Carried by:**

No event carries this field yet.

## <a id="store.restarted"></a>`store.restarted`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `eventd.evman`

Whether this boot's events were already in the store when eventd started,
which is to say eventd had already run during this boot and this start is a
restart. It is false on eventd's first start in a boot. Counting the records
where it is true answers how often eventd restarted during a boot, without
inferring it from gaps.

A historical shard that cannot be opened at startup is left out of the
decision, so on a damaged store a restart can be reported as false.

**Carried by:**

No event carries this field yet.

## <a id="store.resume.cpus"></a>`store.resume.cpus`

- **Type:** `uint[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `eventd.evman`

The CPUs whose KMES rings eventd resumed reading at startup, one entry per
logical CPU in ascending order. Parallel to `store.resume.sequences`: entry
`i` of that array is where reading resumed for the CPU in entry `i` of this
one.

**Carried by:**

No event carries this field yet.

## <a id="store.resume.sequences"></a>`store.resume.sequences`

- **Type:** `uint[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `eventd.evman`

For each CPU in `store.resume.cpus`, the highest event sequence of this boot
already committed with no gap before it, which is where eventd resumed
reading that CPU's ring. Parallel to `store.resume.cpus`.

**0 is a value, not an absence.** It means no unbroken run of committed
events starting at sequence 1 exists for that CPU in this boot: nothing was
committed yet, or the first events were lost. Events committed after a gap
are not reflected here.

**Carried by:**

No event carries this field yet.

## <a id="store.shard"></a>`store.shard`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `eventd.evman`

The index of the event-store shard a record is about, counting from 0.
Present only when `store.kind` is `event`; the log and metric stores are not
sharded, so a record about either has no shard.

**Carried by:**

No event carries this field yet.

## <a id="store.shard-count"></a>`store.shard-count`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `eventd.evman`

How many active event-store shards eventd is running with, after resolving
its configured shard count. Historical shards kept only for reading are not
counted.

**Carried by:**

No event carries this field yet.

*Generated from `eventd.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
