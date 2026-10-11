---
title: "kmes.buffer.swap.failed"
description: "The record that KMES could not resize its per-CPU ring buffers and kept the capacity it had."
---

- **Event type:** `kmes.buffer.swap.failed`
- **Defined in:** `kmes.evman`
- **Tier:** standard
- **Gating:** none — every failed swap is recorded, whatever the error
- **Cardinality:** once per failed swap

The record that KMES could not resize its per-CPU ring buffers and kept the
capacity it had. A capacity change is a swap — new buffers at the new size,
surviving events copied across, writers switched over — and this is what
happens when that swap cannot be completed.

The failure is usually memory pressure, which makes it self-reinforcing in
a way worth recognising: an administrator typically raises capacity because
the system is dropping events, and the allocation most likely to fail is
the one made while the system is already short of memory.

The other failures are rarer and more serious. `EIO` means the migration
found a ring whose framing was corrupt and abandoned the swap rather than
copy it; any other error is the kernel refusing to quiesce the CPUs for
the switch-over. In every case the old rings stay live and nothing was
lost by the attempt.

The swap is system-wide rather than per-ring, so no CPU or ring is named.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`buffer.capacity-requested`](~peios/events/field-index/fields-buffer#buffer.capacity-requested) | `uint.bytes` | required | The per-CPU ring buffer capacity that was asked for. |
| [`buffer.capacity`](~peios/events/field-index/fields-buffer#buffer.capacity) | `uint.bytes` | required | The capacity kept. |
| [`outcome.errno`](~peios/events/field-index/fields-outcome#outcome.errno) | `int.errno` | required | `-ENOMEM` when the new rings could not be allocated, `-EIO` when the migration met a corrupt ring. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `kmes.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
