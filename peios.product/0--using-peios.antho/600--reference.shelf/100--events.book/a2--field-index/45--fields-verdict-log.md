---
title: "verdict-log.*"
description: "Every field the evman catalogue defines under verdict-log: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `verdict-log`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="verdict-log.capacity"></a>`verdict-log.capacity`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

How many verdict records NTFE's private ring holds before the oldest is
overwritten.

**Carried by:**

No event carries this field yet.

## <a id="verdict-log.lost"></a>`verdict-log.lost`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

How many verdict records the private ring has destroyed by overrun since
boot. With no reader attached the ring wraps within moments under real
traffic, so a large count usually means nothing was reading rather than
that something was slow.

**Carried by:**

No event carries this field yet.

## <a id="verdict-log.sequence"></a>`verdict-log.sequence`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The sequence number of a verdict record on NTFE's private ring. It rises
by one per record from boot, so a gap is the confessed evidence of
records lost to overrun, visible only to a reader that was present to see
it.

**Carried by:**

No event carries this field yet.

*Generated from `ntfe.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
