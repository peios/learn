---
title: Emission API
description: The in-kernel emission interface — single and batch emission, the structural checks that drop an event, and what happens when a ring is full.
---

The emission API is the internal kernel interface through which PKM
subsystems emit events — an ordinary function call inside the module,
not a syscall. Userspace emission goes through the syscall interface
(§2.4). There are two entry points: single emission
(`pkm_kmes_emit_kernel`) and batch emission
(`pkm_kmes_emit_kernel_batch`). Both return nothing: kernel emission
is fire-and-forget, and the emitting subsystem is never notified of a
drop.

## Single emission

A kernel emitter passes an origin class, an event type (pointer and
length), and a payload (pointer and length). It does not choose a CPU
or buffer: KMES writes the event to the ring buffer of the CPU the
calling code is executing on.

The entire emission path runs with preemption disabled — from before
the current CPU is determined until after the ring buffer write —
which guarantees the emitting thread cannot migrate mid-write and
preserves the single-writer-per-buffer invariant. For kernel emitters
this covers the full path, timestamp capture through ring write; the
payloads are small and trusted, and the non-preemptible window is a
few hundred nanoseconds.

Construction proceeds in order: capture the wall clock timestamp;
increment the CPU's sequence counter and take the new value; capture
the three identity GUIDs from KACS; build the packed header; write
header and payload contiguously into the ring. The ordering
consequences of these steps are described in §2.2.

KMES trusts kernel emitters. It does not validate the origin class,
the type string's encoding, or the payload — only the structural
checks below run. A null event-type pointer is not checked on the
single-emission path; passing one faults.

## Structural checks and drops

Every kernel emission is checked for: nonzero event type length; type
length within `u16`; total event size within `u32` (overflow-checked);
and total event size within 50% of the per-CPU ring capacity.

A failing event is not written — but its sequence number has already
been consumed, so the drop is visible to consumers as a gap in that
CPU's sequence, and an internal per-CPU dropped-event counter is
incremented. That counter also aggregates events discarded by
overwrite when the buffer wraps; it is not exposed in the ring buffer
metadata and is readable only by the KUnit test harness.

Two further situations discard kernel events entirely outside this
accounting:

- Before KMES initialisation completes, emission is a silent no-op: no
  sequence number is consumed, no counter is incremented, and no gap
  is visible. Events emitted in this window are simply gone.
- If the ring's recorded CPU identity does not match the executing
  CPU, single emission treats it as a structural drop (sequence
  consumed, counter incremented), while both batch paths return early
  without consuming anything.

## Ring buffer full

Each per-CPU buffer is circular. When it is full, KMES overwrites the
oldest events to make room; the write position advances
unconditionally, and emission never blocks and never fails from buffer
pressure. Consumers detect the overwritten events as sequence gaps,
and a consumer whose read position has been overtaken re-anchors to
the oldest surviving event, as specified in the PSPK event stream
chapter. The overwrite mechanics are described with the write protocol
in §2.5.

## Batch emission

The batch API emits multiple events in one operation: an origin class
applied to the whole batch, an array of event descriptors (type
pointer and length, payload pointer and length each), and a count.
There is no upper bound on the kernel batch count — unlike the syscall
batch, which caps at 256 entries — so the non-preemptible window is
bounded only by the caller's restraint.

The batch executes as one preemption-disabled section:

1. One wall clock timestamp is captured; every event in the batch
   shares it.
2. The three identity GUIDs are captured once and shared.
3. Each event, in order: structural checks, sequence assignment,
   header build, ring write. The batch structural check is slightly
   stronger than the single-emission one — it also rejects a null
   type pointer, a null payload pointer with a nonzero length, and a
   header size beyond `u32`. A failing event is dropped exactly as in
   single emission (sequence consumed, gap visible, counter
   incremented) and the batch continues with the next event — kernel
   emitters are trusted, and an individual structural failure
   indicates a kernel bug rather than hostile input. This differs
   deliberately from the syscall batch, which stops at the first
   failure so the untrusted caller learns which entry was bad.
4. After the loop, provided at least one event was actually written,
   the new tail position and then the new write position are published
   with release stores — one publication for the whole batch — and
   the consumer wake flag is checked once, incrementing the futex
   counter if a consumer is asleep. A batch in which every event
   failed publishes nothing and performs no wake check.
5. Preemption is re-enabled, and only then is the futex wake syscall
   work performed, outside the non-preemptible window.

Deferring publication gives batch atomicity: consumers observe either
none of the batch or all of it, since the data is fully written before
the single `write_pos` release store. During the batch, the overwrite
check runs against an internal running write offset — the consumer-
visible `write_pos` stays untouched until the end. The tail position
is likewise kept local and published only at the end.

## Write atomicity

Individual event writes are atomic from the consumer's perspective: an
event's bytes are fully written into the data region before the
`write_pos` release store makes them reachable, so a consumer bounded
by `write_pos` can never observe a partially written event. The
memory-ordering contract this rests on is part of the PSPK event
stream specification; the kernel-side implementation of the write
protocol is described in §2.5.
