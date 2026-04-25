---
title: Emission API
---

## Purpose

The emission API is the internal kernel interface through which PKM subsystems emit events into KMES. It is not a syscall -- it is a function call within the kernel module. Userspace event emission is handled by the syscall interface defined in §4.

## Interface

A kernel emitter calls KMES with the following parameters:

- `origin_class` (`u8`) -- the origin class value identifying the emitting subsystem.
- `event_type` (byte pointer + length) -- the event type string. UTF-8 encoded.
- `payload` (byte pointer + length) -- the msgpack-encoded payload.

The emitter does not specify a CPU or buffer. KMES writes the event to the ring buffer of the CPU on which the calling code is currently executing.

## Preemption

The entire emission path MUST execute with preemption disabled. Preemption is disabled before determining the current CPU and re-enabled after the ring buffer write is complete. This guarantees that the emitting thread cannot be migrated to a different CPU mid-write, which would violate the single-writer-per-buffer invariant.

For kernel emitters, preemption is disabled for the full emission path (timestamp capture through ring buffer write). This is acceptable because kernel emitters produce small, trusted payloads and the total non-preemptible window is a few hundred nanoseconds.

## Event construction

KMES constructs the event by:

1. Capturing the wall clock timestamp.
2. Incrementing the current CPU's per-boot sequence counter and taking the new value. The counter starts at 0; the first event on each CPU receives sequence number 1. Sequence 0 is never assigned to an event. This is a CPU-local operation with no cross-CPU contention.
3. Building the packed header from the stamp fields, cpu_id, origin class, and event type.
4. Writing the header and payload contiguously into the current CPU's ring buffer.

The timestamp is captured before the sequence number is assigned. Two events with the same timestamp on the same CPU are ordered by sequence number.

## Caller contract

The emitter MUST provide a valid origin class value as defined in §2.1.5. The emitter MUST provide a valid UTF-8 event type string. The emitter MUST provide the payload as a contiguous byte buffer.

KMES does not validate the origin class, event type encoding, or payload contents from kernel emitters. These are trusted callers within PKM.

## Structural checks

The emission API performs the following structural checks on every call:

- The event type string MUST have nonzero length.
- The total event size (header + payload) MUST fit in a `u32`.
- The total event size MUST NOT exceed 50% of the per-CPU ring buffer capacity.

The ring buffer capacity check protects against kernel bugs that would emit an event large enough to overwrite most of a CPU's event history. This threshold is a fixed ratio, not a configurable parameter.

If a structural check fails, the event is not written to the ring buffer. The sequence number still advances, making the drop visible as a gap in the sequence. KMES increments an internal dropped-event counter.

## Ring buffer full

Each per-CPU ring buffer is circular. When a buffer is full, KMES overwrites the oldest events in that buffer to make space for the new event. The write pointer advances unconditionally -- emission never blocks and never fails due to buffer pressure.

Consumers detect overwritten events as gaps in the sequence number. If a consumer's read position has been overwritten, the consumer is advanced to the oldest surviving event.

## Batch emission

The batch emission API allows a kernel emitter to emit multiple events as a single operation, reducing per-event overhead.

### Interface

A kernel emitter calls the batch API with the following parameters:

- `origin_class` (`u8`) -- the origin class value identifying the emitting subsystem. Applied to all events in the batch.
- `events` (array of event descriptors) -- each descriptor contains an event type (byte pointer + length) and a payload (byte pointer + length).
- `count` (`u32`) -- the number of events in the array.

### Behavior

KMES processes the batch as follows:

1. Disable preemption.
2. Capture a single wall clock timestamp. All events in the batch share this timestamp.
3. For each event in order: perform structural checks, assign a sequence number, build the header, and write the event to the ring buffer. If a structural check fails on any event, the failing event is dropped (sequence number consumed, gap visible) but subsequent events in the batch continue to be processed.
4. Store `write_pos` with a single release barrier after all events are written.
5. Check `need_wake` once. If `need_wake` is 1, increment `futex_counter` with a release store and issue `futex_wake` to wake all waiting consumer threads.
6. Re-enable preemption.

The shared timestamp reflects the logical instant of the batch. Events within a batch are ordered by their sequence numbers. The single `write_pos` update and single `need_wake` check are the primary performance benefits over individual emission.

### Failure semantics

The kernel batch API continues processing after a single event failure. If a structural check fails on event N, event N is dropped but events N+1 through the end of the batch are still processed. This is deliberately different from the syscall batch API (`kmes_emit_batch`), which stops processing at the first failure. Kernel emitters are trusted and individual structural failures are expected to be rare (indicating a kernel bug). Syscall emitters are untrusted and receive an error indicating which entry failed so the caller can diagnose and fix the issue.

### Caller contract

The same caller contract as single emission applies to each event in the batch. KMES does not validate payload contents from kernel emitters.

## Atomicity

Individual event writes to the ring buffer MUST be atomic from the consumer's perspective. A consumer MUST NOT observe a partially written event. For batch emission, `write_pos` is deferred until all events are written, so consumers observe the entire batch atomically -- no events from the batch are visible until all have been written. The consumer processes individual events within the batch, each of which is independently valid. The mechanism used to guarantee write atomicity is defined in §5.1.8.
