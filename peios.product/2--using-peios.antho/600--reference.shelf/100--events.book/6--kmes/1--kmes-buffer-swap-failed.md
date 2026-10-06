---
title: "kmes.buffer.swap.failed"
description: "The record that KMES could not resize its per-CPU ring buffers and kept the capacity it had."
---

- **Event type:** `kmes.buffer.swap.failed`
- **Defined in:** `kmes.evman`
- **Tier:** standard
- **Gating:** only when the swap failed with ENOMEM
- **Cardinality:** once per failed swap

The record that KMES could not resize its per-CPU ring buffers and kept the
capacity it had. A capacity change is a swap — new buffers at the new size,
surviving events copied across, writers switched over — and this is what
happens when that swap cannot be completed.

The failure is usually memory pressure, which makes it self-reinforcing in
a way worth recognising: an administrator typically raises capacity because
the system is dropping events, and the allocation most likely to fail is
the one made while the system is already short of memory.

The swap is system-wide rather than per-ring, so no CPU or ring is named.

**Only `ENOMEM` produces a record.** A swap that fails for any other reason
retains the old capacity and emits nothing, so absence of this event is not
evidence that a capacity change took effect.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`buffer.capacity-requested`](~peios/events/field-index/fields-buffer#buffer.capacity-requested) | `uint.bytes` | required | The per-CPU ring buffer capacity that was asked for. |
| [`buffer.capacity`](~peios/events/field-index/fields-buffer#buffer.capacity) | `uint.bytes` | required | The capacity kept. |
| [`outcome.errno`](~peios/events/field-index/fields-outcome#outcome.errno) | `int.errno` | required | The error the operation failed with, as a negative errno. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `kmes.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
