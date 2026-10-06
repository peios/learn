---
title: "event.*"
description: "Every field the evman catalogue defines under event: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `event`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="event.boot.guid"></a>`event.boot.guid`

- **Type:** `bin.guid`
- **Asserted:** no
- **Carried in:** the header
- **Defined in:** `kernel.evman`

The boot the record belongs to. Not in the record itself: the consumer
supplies the boot it read the record in, which is what makes
`event.sequence` unique across reboots.

**Carried by:**

Every record, in the header.

## <a id="event.cpu"></a>`event.cpu`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the header
- **Defined in:** `kernel.evman`

The CPU whose ring carried the record. Sequence numbers are per CPU, so
`event.cpu` and `event.sequence` together identify a record within a boot.

**Carried by:**

Every record, in the header.

## <a id="event.sequence"></a>`event.sequence`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the header
- **Defined in:** `kernel.evman`

The record's sequence number within its CPU's ring for this boot.
Sequence numbers on one ring are contiguous, so a gap between two records
read from it is a count of records lost.

**Carried by:**

Every record, in the header.

## <a id="event.time"></a>`event.time`

- **Type:** `uint.time`
- **Asserted:** no
- **Carried in:** the header
- **Defined in:** `kernel.evman`

When the record was made, in nanoseconds since the Unix epoch. Stamped by
the kernel at emission, so a payload never repeats it: an event carrying
its own timestamp is carrying a second, forgeable one.

**Carried by:**

Every record, in the header.

## <a id="event.type"></a>`event.type`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the header
- **Defined in:** `kernel.evman`

The event type, such as `kacs.audit.access.checked`. Stamped from the
emitter's argument, so it names what the emitter claims happened; the
`emitter.*` header fields are the evidence of who wrote it.

**Carried by:**

Every record, in the header.

*Generated from `kernel.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
