---
title: The Envelope
description: The packed binary header in front of every KMES payload — the fields the kernel stamps, the layout, and what ordering you get.
---

Every KMES event is a packed binary header followed immediately by its
msgpack payload, delivered as one contiguous byte sequence with no
padding anywhere.

The emitter supplies only two things: the **event type string** and the
**payload**. Everything else in the header is stamped by KMES itself,
which is what makes the identity fields trustworthy — an emitter cannot
forge them.

## Fields KMES stamps

| Field | Meaning |
|---|---|
| `timestamp` | Wall clock at the moment KMES accepted the event, nanoseconds since the Unix epoch. |
| `sequence` | The emitting CPU's per-boot counter. The first event on each CPU gets 1. |
| `cpu_id` | The CPU whose ring buffer holds the event. |
| `origin_class` | 0 for syscall emission, unconditionally. For kernel emission, the value the calling subsystem passed. |
| identity GUIDs | The effective, true and process token GUIDs of the task that caused the event. |

The identity stamps matter for reading this book: **several events carry
no caller in their payload at all**, because the envelope already
names one. StrataFS copy-up records are the clearest case — nothing in
the payload names a token, and the caller is recovered from the header.

`event_size`, `header_size` and `type_len` are structural, computed by
KMES during construction.

## Layout

All fields before the event type string sit at fixed offsets. The type
string begins at offset 77, with its `u16` length at offset 75, so the
header is exactly `77 + type_len` bytes. The payload runs from
`header_size` to `event_size`, and the next event begins at
`event_size` from the start of the current one.

All multi-byte header integers are little-endian. The identity GUIDs are
opaque 16-byte values.

The full field-by-field layout is normative in PSPK §2, the KMES event
stream specification. This summary is enough to walk a stream; it is not
enough to implement one.

## Ordering

`timestamp` is captured before `sequence` is assigned, so two events
with the same timestamp on the same CPU are ordered by sequence.

Across CPUs there is no global order. Two events on different CPUs with
close timestamps may have been observed in either order.
