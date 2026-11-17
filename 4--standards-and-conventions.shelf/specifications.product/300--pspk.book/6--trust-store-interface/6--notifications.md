---
title: Notifications
description: The fixed-size records a store keeper reads from the device,
  telling it that a certificate was verified for the first time or that
  it has to list again.
---

The kernel tells a store keeper of events by records it reads from the
device descriptor.

A `read()` returns one or more whole `ktrust_notification` records and
never part of one. A blocking read waits for a record. Under
`O_NONBLOCK`, a read with nothing queued fails `EAGAIN`. The descriptor
supports `poll()`.

| Field | Type | Description |
|---|---|---|
| `type` | `u32` | What happened |
| `_pad` | `u32` | Reserved |
| `hash` | `u8[64]` | The object the record concerns, or zero |

| `type` | Name | Meaning |
|---|---|---|
| 1 | First seen | A certificate was verified for the first time since boot. `hash` is its object hash |
| 2 | Overflow | Records were dropped, or the record of seen certificates is full. `hash` is zero |

The enumeration is closed (§6.7).

The kernel queues a bounded number of records (§6.A). If the queue
fills, the kernel drops records and queues one Overflow in their place.
A store keeper that reads an Overflow MUST list the seen certificates
again to learn what it missed.

A store keeper that is not attached misses nothing it cannot recover:
the record of seen certificates is complete since boot, whenever the
store keeper attaches.

> [!NOTE]
> A notification is a hint to look, not a log. The kernel reports
> verification outcomes as events, and a store keeper that wants a
> history reads them there.
