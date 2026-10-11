---
title: "clock.*"
description: "Every field the evman catalogue defines under clock: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `clock`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="clock.time"></a>`clock.time`

- **Type:** `uint.time`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `timed.evman`

The wall clock's reading just after timed moved it. Every record written
after this one is stamped on the clock as it now reads, so this is the
point from which their times count.

Read just after the change, not computed from it, so it includes the few
microseconds the change itself took.

**Carried by:**

- [`timed.clock.stepped`](~peios/events/timed/timed-clock-stepped)

## <a id="clock.time-previous"></a>`clock.time-previous`

- **Type:** `uint.time`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `timed.evman`

The wall clock's reading just before timed moved it, the counterpart of
`clock.time`. The difference between the two is the size of the step, and
records stamped between `clock.time-previous` and `clock.time` on either
side of this one were not written in the order their times suggest.

Absent when the clock read before the Unix epoch, which a `uint.time`
cannot hold; that happens on a machine whose hardware clock has failed,
and it is exactly the case the boot floor exists for.

**Carried by:**

- [`timed.clock.stepped`](~peios/events/timed/timed-clock-stepped)

*Generated from `timed.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
