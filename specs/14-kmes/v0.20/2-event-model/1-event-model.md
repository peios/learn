---
title: Event Model
---

## Structure

An event is an indivisible record consisting of a header followed by a payload. The header is a packed binary structure with no padding between fields. The payload is a msgpack-encoded blob. Header and payload are always stored, transmitted, and consumed as a single contiguous byte sequence.

## Header layout

The header fields are laid out sequentially with no padding or alignment gaps.

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 4 | `event_size` | Total size of the event (header + payload) in bytes. `u32`, little-endian. |
| 4 | 4 | `header_size` | Size of the header in bytes. `u32`, little-endian. |
| 8 | 8 | `timestamp` | Wall clock time at emission. Nanoseconds since Unix epoch. `u64`, little-endian. |
| 16 | 8 | `sequence` | Per-CPU, per-boot monotonic sequence number. `u64`, little-endian. Used for gap detection: a gap in the sequence on a given CPU indicates lost events. |
| 24 | 2 | `cpu_id` | The CPU on which the event was emitted. `u16`, little-endian. Identifies which per-CPU ring buffer contains this event. |
| 26 | 1 | `origin_class` | Origin of the event. `u8`. |
| 27 | 2 | `type_len` | Length of the event type string in bytes. `u16`, little-endian. |
| 29 | `type_len` | `type` | Event type string. UTF-8 encoded. Not null-terminated. |

The payload begins at offset `header_size` from the start of the event. The next event in the ring buffer begins at offset `event_size` from the start of the current event.

In v0.20, `header_size` is exactly `29 + type_len` -- the minimum size with no reserved space. Future versions MAY increase `header_size` to accommodate identity stamp fields. Consumers MUST use `header_size` to locate the payload, not the end of the event type string, to ensure forward compatibility.

There is no separate limit on event type string length. The event type length is constrained only by the total event size limits (MaxEventSize for syscall emitters, 50% of ring buffer capacity for all emitters).

## Stamp fields

KMES populates the following header fields at emission time. The emitter does not provide these -- they are set by KMES unconditionally.

- `timestamp` -- captured from the wall clock (`CLOCK_REALTIME`) at the moment KMES accepts the event.
- `sequence` -- assigned by incrementing the emitting CPU's per-boot monotonic counter (initialized to zero) and taking the new value. The first event on each CPU receives sequence number 1; sequence 0 is never assigned.
- `cpu_id` -- the CPU on which the event was emitted.
- `origin_class` -- for syscall emission, set unconditionally to 0 (userspace) by KMES. For kernel emission, set to the value provided by the calling subsystem.

`event_size`, `header_size`, and `type_len` are structural fields set by KMES during event construction.

The emitter provides the event type string and the msgpack payload. KMES does not modify either.

## Ordering

For cross-CPU ordering, events are ordered by `timestamp` (wall clock). Events with identical timestamps from different CPUs were genuinely concurrent and have no defined relative order. Within a single CPU, the `sequence` number provides reliable monotonic ordering even across clock discontinuities. Events with identical timestamps from the same CPU are ordered by `sequence`.

There is no global sequence number. Each CPU maintains its own independent sequence counter. The pair (`cpu_id`, `sequence`) uniquely identifies an event within a single boot.

### Future identity stamp fields

A future version of this specification will define additional stamp fields carrying process and identity information about the emitter. These fields will be added to the header between the event type string and the payload boundary, extending `header_size`. The specific fields are deferred to avoid specification conflicts with KACS, which owns process identity primitives.

Consumers MUST NOT assume that `header_size` equals the minimum header size. Consumers MUST use `header_size` to locate the payload.

## Origin class values

| Value | Origin |
|---|---|
| 0 | Userspace (syscall) |
| 1 | KMES |
| 2 | KACS |
| 3 | LCS |

Values 4--255 are reserved for future kernel subsystems.

## Payload

The payload is a single msgpack-encoded value occupying the bytes from offset `header_size` to offset `event_size`. KMES does not interpret or modify the payload. The payload's structure is defined by the emitter and understood by consumers.

The payload MUST be valid msgpack. A zero-length payload (`event_size == header_size`) is valid for kernel emitters -- the event consists of a header with no payload data. For syscall emitters, a zero-length payload fails msgpack validation (an empty byte sequence is not a valid msgpack value) and is rejected with EINVAL.

KMES does not validate payloads from kernel emitters. For events emitted via the syscall interface, KMES MUST validate that the payload is well-formed msgpack before accepting the event. Validation is iterative with a bounded maximum nesting depth. Events with invalid payloads MUST be rejected and the syscall MUST return an error to the caller.

## Size limits

For events emitted via syscall, the maximum permitted event size is runtime-configurable via the registry (MaxEventSize). KMES uses an internal default until the registry is reachable. Events exceeding the limit MUST be rejected and the syscall MUST return an error. Kernel emitters are not subject to the configurable size limit -- they are subject only to the 50% ring buffer capacity structural limit defined in the Emission API section.
