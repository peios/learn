---
title: Event Model
description: What an event is on the wire — the packed header, the stamps the kernel applies, ordering, the msgpack payload and the size limits.
---

## Structure [*event.wire-structure]

An event is a packed binary header followed immediately by its msgpack
payload, written and delivered as a single contiguous byte sequence
with no padding or alignment gaps anywhere. The header is never
represented as a C struct in the kernel; it is serialised field by
field, in order, directly into the ring buffer. The field-by-field
layout — offsets, sizes, and endianness — is part of the consumer
contract and is defined in the PSPK event stream specification. In
summary: all fields before the event type string sit at fixed offsets,
the event type string begins at offset 77 with its `u16` length at
offset 75, the header is exactly `77 + type_len` bytes, the payload
occupies the bytes from `header_size` to `event_size`, and the next
event begins at offset `event_size` from the start of the current one.
All multi-byte header integers are little-endian; the identity GUIDs
are copied as opaque 16-byte values.

`event_size`, `header_size`, and `type_len` are structural fields
computed by KMES during construction. The emitter supplies only the
event type string and the payload, and KMES copies both verbatim. [*event.emitter-bytes-verbatim]

## Intrinsic stamps [*event.stamps-unconditional]

KMES populates four intrinsic stamp fields at emission time,
unconditionally; the emitter cannot supply them.

- **`timestamp`** — wall clock time (`CLOCK_REALTIME`, via
  `ktime_get_real_ns()`) at the moment KMES accepts the event, in
  nanoseconds since the Unix epoch. [*event.stamp.timestamp-realtime]
- **`sequence`** — the emitting CPU's per-boot counter, incremented
  and then read, so the first event on each CPU gets 1. [*event.stamp.sequence-increment-then-read]
- **`cpu_id`** — the CPU on which the ring buffer write occurs, which
  identifies the per-CPU buffer holding the event. [*event.stamp.cpu-id-of-write]
- **`origin_class`** — for syscall emission, set unconditionally to 0
  (userspace); the caller cannot influence it. For kernel emission,
  the value the calling subsystem passed, written to the header
  without validation — kernel emitters are trusted to pass an
  assigned value. [*event.stamp.origin-class-trust]

The timestamp is captured before the sequence number is assigned, so
two events with the same timestamp on the same CPU are ordered by
sequence. [*event.stamp.timestamp-before-sequence]

## Identity stamps [*event.identity-at-write-time]

The three identity GUIDs are captured by calling KACS accessors during
the preemption-disabled ring buffer write phase, after the sequence
number is taken and before the header is built. All three accessors
are safe with preemption disabled — each is a handful of pointer
dereferences and a 16-byte copy, with no allocation and no sleeping.
The stamps therefore reflect the thread's identity at the moment of
the ring buffer write, not at syscall entry.

- `kacs_effective_token_guid()` reads the thread's *subjective*
  credentials (`current_cred()`), so during impersonation — which
  installs the impersonation token via `override_creds()` — it yields
  the impersonation token's GUID. Otherwise it equals the true token
  GUID. [*event.identity.effective-follows-impersonation]
- `kacs_primary_token_guid()` reads the *real* credentials
  (`current_real_cred()`), which impersonation leaves untouched, so it
  always yields the process's primary token GUID. [*event.identity.true-ignores-impersonation]
- `kacs_process_guid()` reads the process GUID KACS assigned when the
  process's security state was created at fork. Threads created with
  `CLONE_THREAD` share the process state, and no exec path writes the
  field, so the GUID is stable for the process's lifetime. [*event.identity.process-guid-stable]

All three accessors return the null GUID when there is no task context
(`!current` or not `in_task()`), and the token accessors also return it
when the token cannot be resolved. A fully null identity triple
therefore indicates emission before KACS initialisation, from a kernel
thread, or from interrupt or softirq context. No event is ever stamped
with the identity of a task that merely happened to be interrupted. [*event.identity.null-without-task-context]

For batch emission, the timestamp and the three identity GUIDs are
captured once, before the per-event loop, and shared by every event in
the batch: the batch executes with preemption disabled on one CPU, so
the emitting thread's identity cannot change mid-batch. Each event
still receives its own sequence number. [*event.identity.batch-captured-once]

## Ordering [*event.ordering-contract]

Cross-CPU ordering is by `timestamp`. Events with identical timestamps
from different CPUs were genuinely concurrent and have no defined
relative order. Within one CPU, `sequence` is the reliable ordering
primitive, monotonic even across wall-clock discontinuities; events
with identical timestamps on the same CPU are ordered by sequence.

## Payload

The payload is a single msgpack value. KMES neither interprets nor
modifies it — buffering and delivery are content-blind — and it
performs no payload validation at all for kernel emitters, which are
trusted callers inside PKM. [*event.payload.kernel-not-validated]

Payloads arriving through the syscall interface are validated before
acceptance by an iterative (non-recursive) msgpack walker implemented
in Rust, operating on the kernel's staged copy of the payload:

- The payload is exactly one well-formed top-level msgpack value.
  Trailing bytes after it are rejected, as is the never-used `0xc1`
  type byte. [*event.payload.exactly-one-value] A zero-length payload is rejected — an empty byte
  sequence is not a msgpack value — so syscall events always carry a
  payload. [*event.payload.empty-rejected] (Kernel emitters can emit header-only events with
  `event_size == header_size`.)
- Nesting depth is bounded by the configured `MaxNestingDepth`
  (§2.6). Depth counts from 1 at the top-level value; each child of an
  array or map sits one deeper than its container. A non-empty
  container at the maximum depth is invalid, because its children
  would exceed the limit; an empty array or map at the maximum depth
  is valid, consuming no depth. Map keys and values each occupy a
  child slot, so a map contributes twice its entry count of children. [*event.payload.depth-model]
- The walker's own stack is 256 frames, matching the upper bound of
  the `MaxNestingDepth` range; a configured depth outside 1–256 causes
  every payload to be rejected rather than any to be waved through. [*event.payload.bad-depth-config-rejects-all]
- Length prefixes inside msgpack are big-endian, per the MessagePack
  specification — the one big-endian ingredient in an otherwise
  little-endian event.

A rejected payload fails the syscall with `EINVAL` and nothing is
written to the ring buffer. [*event.payload.reject-writes-nothing]

The event type string is validated as UTF-8 on the syscall path by the
same staged-copy pass; kernel emitters' type strings are trusted and
copied as given. Types are compared by consumers as raw bytes — no
case folding or normalisation is applied anywhere. [*event.type-utf8-on-syscall-path]

## Size limits [*event.size-limits]

Three structural bounds apply to every event, and one configurable
policy bound applies to syscall emitters only:

- The event type length fits the header's `u16` `type_len` field and
  is nonzero. Syscall emitters cannot express an overlong type — the
  ABI length field is already `u16` — but the kernel emission API
  takes a `size_t` and enforces the bound itself. [*event.limits.type-len-u16-nonzero]
- The total event size (header + payload) fits a `u32`, checked with
  overflow-safe arithmetic on the declared lengths. [*event.limits.total-fits-u32]
- The total event size does not exceed 50% of the per-CPU ring buffer
  capacity — a fixed ratio, not configurable, protecting a CPU's
  event history from a single giant event. An event of exactly half
  the capacity is accepted. Capacity is always a power of two, so the
  halving is exact. [*event.limits.half-capacity]
- Syscall events are additionally bounded by the registry-configurable
  `MaxEventSize` (§2.6), rejected with `ENOSPC` when exceeded. Kernel
  emitters are exempt from this policy limit. [*event.limits.max-event-size-syscall-only]
