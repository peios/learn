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
| 27 | 16 | `effective_token_guid` | GUID of the effective token for the emitting thread. Microsoft GUID binary format. Null GUID if not available. |
| 43 | 16 | `true_token_guid` | GUID of the process's primary token. Microsoft GUID binary format. Null GUID if not available. |
| 59 | 16 | `process_guid` | GUID of the emitting process. Microsoft GUID binary format. Null GUID if not available. |
| 75 | 2 | `type_len` | Length of the event type string in bytes. `u16`, little-endian. |
| 77 | `type_len` | `type` | Event type string. UTF-8 encoded. Not null-terminated. |

The payload begins at offset `header_size` from the start of the event. The next event in the ring buffer begins at offset `event_size` from the start of the current event.

`header_size` is exactly `77 + type_len`. Consumers MUST use `header_size` to locate the payload.

There is no separate limit on event type string length. The event type length is constrained only by the total event size limits (MaxEventSize for syscall emitters, 50% of ring buffer capacity for all emitters).

## Stamp fields

KMES populates the following header fields at emission time. The emitter does not provide these -- they are set by KMES unconditionally.

### KMES-intrinsic stamps

- `timestamp` -- captured from the wall clock (`CLOCK_REALTIME`) at the moment KMES accepts the event.
- `sequence` -- assigned by incrementing the emitting CPU's per-boot monotonic counter (initialized to zero) and taking the new value. The first event on each CPU receives sequence number 1; sequence 0 is never assigned.
- `cpu_id` -- the CPU on which the event was emitted.
- `origin_class` -- for syscall emission, set unconditionally to 0 (userspace) by KMES. For kernel emission, set to the value provided by the calling subsystem.

### Identity stamps

- `effective_token_guid` -- the GUID of the token governing the current thread's effective access rights. If the thread is impersonating, this is the impersonation token's GUID. If the thread is not impersonating, this equals `true_token_guid`. Captured by calling `kacs_effective_token_guid()`.
- `true_token_guid` -- the GUID of the process's primary token. Always the process token regardless of impersonation state. Captured by calling `kacs_primary_token_guid()`.
- `process_guid` -- the GUID of the emitting process, assigned at fork and immutable across exec. Captured by calling `kacs_process_guid()`.

All three identity stamp accessors return the null GUID (16 zero bytes) when KACS is not initialised or when the current execution context has no associated process (kernel worker threads, interrupt-deferred work). KMES does not distinguish between these cases -- a null GUID means "identity not available."

### Structural fields

`event_size`, `header_size`, and `type_len` are structural fields set by KMES during event construction.

The emitter provides the event type string and the msgpack payload. KMES does not modify either.

## Ordering

For cross-CPU ordering, events are ordered by `timestamp` (wall clock). Events with identical timestamps from different CPUs were genuinely concurrent and have no defined relative order. Within a single CPU, the `sequence` number provides reliable monotonic ordering even across clock discontinuities. Events with identical timestamps from the same CPU are ordered by `sequence`.

There is no global sequence number. Each CPU maintains its own independent sequence counter. The pair (`cpu_id`, `sequence`) uniquely identifies an event within a single boot.

### Identity stamp timing

Identity stamps are captured during the preemption-disabled ring buffer write phase, alongside the KMES-intrinsic stamps. The three KACS accessor calls are guaranteed to be safe with preemption disabled (no sleeping, no allocation). The identity stamps reflect the thread's identity at the moment of the ring buffer write, not at syscall entry time.

For batch emission, identity stamps are captured once and shared across all events in the batch, since the batch executes with preemption disabled on a single CPU and the emitting thread's identity cannot change mid-batch.

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

For events emitted via syscall, the maximum permitted event size is runtime-configurable via the registry (MaxEventSize). KMES uses an internal default until the registry is reachable. Events exceeding the limit MUST be rejected and the syscall MUST return an error. Kernel emitters are not subject to the configurable size limit -- they are subject only to the 50% ring buffer capacity structural limit defined in §3.1.6.
