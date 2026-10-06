---
title: "loss.*"
description: "Every field the evman catalogue defines under loss: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `loss`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="loss.bytes"></a>`loss.bytes`

- **Type:** `uint.bytes`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The bytes of events a loss discarded. Reported in bytes where KMES cannot
count events: when a ring's framing is found corrupt, everything pending
is dropped at once without being parsed, and when a capacity swap skips
an event too large for the smaller ring, only its size is known.

**Carried by:**

No event carries this field yet.

## <a id="loss.class"></a>`loss.class`

- **Type:** `uint.enum`
- **Values:** `0 userspace` · `1 kmes` · `2 kacs` · `3 lcs` · `4 ntfe`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The emission path of the events that were lost, numbered as `emitter.class`
numbers it: the kernel subsystem, or userspace, that was writing them. A
loss record is written by KMES, so its own `emitter.class` is always
`kmes`; this is the field that says whose events went missing.

**Carried by:**

No event carries this field yet.

## <a id="loss.count"></a>`loss.count`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The number of events lost in one occurrence. For a gap found in the
sequence numbers, the size of that gap: `loss.sequence-last` minus
`loss.sequence`, plus one.

**Carried by:**

No event carries this field yet.

## <a id="loss.preceding-time"></a>`loss.preceding-time`

- **Type:** `uint.time`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The time of the last record received before a gap, in nanoseconds since
the Unix epoch. With the time of the record that revealed the gap, it
bounds when the lost events were written. Absent when no record preceded
the gap on that ring, as at the start of a boot.

**Carried by:**

No event carries this field yet.

## <a id="loss.sequence"></a>`loss.sequence`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The first sequence number a loss covers. Sequence numbers are contiguous
per CPU ring, so with `buffer.cpu` this locates the gap exactly, and it is
the field that reconciles a loss KMES reports with a gap a consumer infers
from `event.sequence`.

**Not every loss has one.** An event dropped because its CPU had no usable
ring, an event emitted before KMES started, and an emit refused at the
system call consume no sequence number and leave no gap to point at.

**Carried by:**

No event carries this field yet.

## <a id="loss.sequence-last"></a>`loss.sequence-last`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The last sequence number of a gap, where `loss.sequence` is the first.
Both ends are included in the loss.

**Carried by:**

No event carries this field yet.

## <a id="loss.total"></a>`loss.total`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The cumulative count of events a ring has dropped. **Not emitted today.**
KMES keeps the counter, but it is not in the ring's metadata page and
nothing outside the kernel's own tests reads it, so no emitter has it to
report. It also under-reports: a corrupt-ring discard, an event skipped by
a capacity swap and an event lost for want of a usable ring are never
added to it, so even once it is emitted it is a lower bound rather than a
total.

**Carried by:**

No event carries this field yet.

*Generated from `kmes.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
