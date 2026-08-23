---
title: Event Format
description: An event is one contiguous record — the packed header layout, the payload, event types, origin class, identity fields and ordering.
---

An event is an indivisible record: a packed binary header followed
immediately by a payload. Header and payload are always stored,
delivered, and consumed as one contiguous byte sequence, and neither
is meaningful alone.

## Header layout

The header fields are laid out sequentially with no padding and no
alignment gaps. All multi-byte integers are little-endian.

| Offset | Size | Type | Field | Description |
|---|---|---|---|---|
| 0 | 4 | `u32` | `event_size` | Total size of the event, header plus payload, in bytes. |
| 4 | 4 | `u32` | `header_size` | Size of the header in bytes. |
| 8 | 8 | `u64` | `timestamp` | Wall clock time at emission, in nanoseconds since the Unix epoch. |
| 16 | 8 | `u64` | `sequence` | Per-CPU, per-boot monotonic sequence number. |
| 24 | 2 | `u16` | `cpu_id` | The CPU on which the event was emitted, identifying the ring buffer that carries it. |
| 26 | 1 | `u8` | `origin_class` | The emission path that produced the event. |
| 27 | 16 | `GUID` | `effective_token_guid` | GUID of the effective token of the emitting thread. Null GUID if unavailable. |
| 43 | 16 | `GUID` | `true_token_guid` | GUID of the emitting process's primary token. Null GUID if unavailable. |
| 59 | 16 | `GUID` | `process_guid` | GUID of the emitting process. Null GUID if unavailable. |
| 75 | 2 | `u16` | `type_len` | Length of the event type string in bytes. |
| 77 | `type_len` | `[u8]` | `type` | Event type string, UTF-8, not null-terminated. |

GUIDs use the binary format defined in PCDS and are opaque 16 bytes to
this contract. The **null GUID** is sixteen zero bytes and means the
field is not applicable or was not available.

`header_size` is `77 + type_len` in this version of the format. A
consumer MUST use `header_size` to locate the payload and MUST NOT
compute the payload offset from `77 + type_len` or from any other
constant, so that a future header extension does not break it. All
fields before `type` are at fixed offsets and will remain so.

The payload occupies the bytes from `header_size` to `event_size`. The
next event in a ring buffer begins `event_size` bytes after the start
of the current one, with no alignment padding between events.

## Payload

The payload is exactly one MessagePack value, and its structure is
defined by the emitter. KMES does not interpret it.

A consumer MUST NOT assume a payload is present: an event emitted by a
kernel subsystem MAY have `event_size == header_size`, meaning a
header and no payload at all. Events emitted through the system calls
always carry a payload, because an empty byte sequence is not a valid
MessagePack value and is rejected at the syscall boundary.

Note that MessagePack encodes its own length prefixes big-endian,
whereas every integer in the event header is little-endian. Both
appear in one event.

## Event types

The event type is an arbitrary UTF-8 string. KMES imposes no
structure, namespace, or naming convention on it, and applies no case
folding or normalisation. Consumers MUST compare event types as raw
byte sequences.

## Origin class

| Value | Origin |
|---|---|
| 0 | Userspace, via system call |
| 1 | KMES |
| 2 | KACS |
| 3 | LCS |

Values 4–255 are unassigned. A consumer MUST tolerate an unrecognised
origin class rather than rejecting the event, so that a kernel
subsystem added later does not break it.

Events with origin class 0 were emitted through the system call
interface, and their origin class is set by the kernel, not by the
caller. A userspace emitter cannot claim to be a kernel subsystem.

## Identity fields

The three identity GUIDs are captured by the kernel at the moment the
event is written to the ring buffer, not when the emitting call began.

- `effective_token_guid` is the token governing the emitting thread's
  access rights. If the thread was impersonating, this is the
  impersonation token; otherwise it equals `true_token_guid`.
- `true_token_guid` is the emitting process's primary token,
  regardless of impersonation.
- `process_guid` identifies the emitting process. It is assigned when
  the process is created and does not change across `exec`.

Any of the three MAY be the null GUID, meaning the kernel had no
identity to record — emission before the access control subsystem
initialised, or from a context with no associated process such as a
kernel worker thread. A consumer MUST treat a null identity as
"unattributed" and MUST NOT treat it as a valid GUID value that could
match a real token or process.

## Ordering

Events from different CPUs are ordered by `timestamp`. Events with
identical timestamps from different CPUs were genuinely concurrent and
have no defined relative order.

Within a single CPU, `sequence` is the ordering primitive. It is
monotonic across wall clock discontinuities, which `timestamp` is not:
a clock adjustment can move timestamps backwards, and a consumer that
requires monotonic ordering within a CPU MUST use `sequence`. Events
with identical timestamps on the same CPU are ordered by `sequence`.

Each CPU numbers independently and there is no global sequence. The
counter starts at zero when the kernel module loads and is incremented
before a value is taken, so the first event on a CPU carries sequence
number 1 and **sequence 0 is never assigned**. The pair
(`cpu_id`, `sequence`) uniquely identifies an event within one boot.

A gap in the sequence for a given CPU means events were lost — either
overwritten before the consumer read them, or dropped by the kernel
before they reached the buffer. Sequence numbers are continuous across
a buffer replacement, so a generation change does not itself produce a
gap.
