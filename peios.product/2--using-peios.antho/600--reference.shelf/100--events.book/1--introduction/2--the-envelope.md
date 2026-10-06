---
title: The Envelope
description: The packed binary header in front of every KMES payload — the fields the kernel stamps, the names a consumer exposes them under, the layout, and what ordering you get.
---

Every KMES event is a packed binary header followed immediately by its
MessagePack payload, delivered as one contiguous byte sequence with no
padding anywhere.

The emitter supplies only two things: the **event type** and the
**payload**. Everything else in the header is stamped by KMES itself,
which is what makes the identity fields trustworthy — an emitter cannot
forge them.

## Fields KMES stamps

A consumer that exposes header values by name exposes them under these
field paths (PGSS §6.4). They are fields like any other, defined in the
catalogue and listed in the field index under `event` and `emitter`, but
they live in the header, and **no payload repeats them**.

| Field | Header field | Meaning |
|---|---|---|
| `event.type` | `type` | The event type, as the emitter named it. |
| `event.time` | `timestamp` | Wall clock at the moment KMES accepted the event, nanoseconds since the Unix epoch. |
| `event.sequence` | `sequence` | The emitting CPU's per-boot counter. The first event on each CPU gets 1, and the numbers on one ring are contiguous. |
| `event.cpu` | `cpu_id` | The CPU whose ring buffer holds the event. |
| `event.boot.guid` | — | The boot the record belongs to. Not in the header: the consumer supplies the boot it read the record in. |
| `emitter.class` | `origin_class` | The emission path that wrote the record: `0` userspace, `1` kmes, `2` kacs, `3` lcs, `4` ntfe. |
| `emitter.token.guid` | `effective_token_guid` | The effective token of the task that caused the event. |
| `emitter.true-token.guid` | `true_token_guid` | That task's own token, before any impersonation. |
| `emitter.process.guid` | `process_guid` | The process the record was written from. |

`emitter.class` is set by the kernel, never by the emitter. A record
whose type names a kernel root but whose class is `0` was written by a
program, whatever its type says. The class is the path, not the type's
root: StrataFS records are written through KACS and carry class `2`.

The identity stamps matter for reading this book: **several events carry
no caller in their payload at all**, because the envelope already names
one. StrataFS copy-up records are the clearest case — nothing in the
payload names a token, and the caller is recovered from the header. A
record written outside task context has zero GUIDs, and
`emitter.stamp-failure` in its payload says why.

`event_size`, `header_size` and `type_len` are structural, computed by
KMES during construction, and are not exposed as fields.

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

`event.time` is captured before `event.sequence` is assigned, so two
events with the same time on the same CPU are ordered by sequence.
`event.cpu` and `event.sequence` together identify a record within a
boot, and with `event.boot.guid` across boots.

Across CPUs there is no global order. Two events on different CPUs with
close timestamps may have been observed in either order.
