---
title: "counter.*"
description: "Every field the evman catalogue defines under counter: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `counter`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="counter.name"></a>`counter.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The name of a counter stream, as the policy author wrote it in `COUNT` and
`Counter.<name>`. At most 63 bytes.

**Carried by:**

No event carries this field yet.

## <a id="counter.partition"></a>`counter.partition`

- **Type:** `uint.flags`
- **Values:** `0x1 source-address` · `0x2 destination-address` · `0x4 interface`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

Which packet facts a counter view is partitioned by: one cell per distinct
value of the facts set here. Zero is a single cell for the whole machine. A
packet that lacks a partitioning fact, such as non-IP traffic in a view
partitioned by address, counts nowhere.

**Carried by:**

No event carries this field yet.

## <a id="counter.threshold"></a>`counter.threshold`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The threshold a rule's counter condition compared `counter.value` against.
The two together are the whole content of a crossing.

**Carried by:**

No event carries this field yet.

## <a id="counter.value"></a>`counter.value`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The value held in a counter cell for the window a rule read. Its unit is
whatever the stream counts: emissions of `COUNT`, or bytes where the rule
counts `Length`, which is the length the stack saw and not the wire's.

**Carried by:**

No event carries this field yet.

## <a id="counter.windows"></a>`counter.windows`

- **Type:** `uint.duration[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The sliding-window lengths a counter table answers, at most eight. The
kernel holds them to the whole second and approximates each window with
eight buckets of an eighth of its length, so a window's value is accurate
only to that bucket.

**Carried by:**

No event carries this field yet.

*Generated from `ntfe.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
