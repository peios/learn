---
title: Failure Modes
---

KMES is a kernel subsystem with no external trust boundary on the write path. Kernel emitters are trusted; userspace emitters are validated at the syscall boundary. Failure semantics are simpler than subsystems like LCS that span kernel-userspace trust boundaries, but MUST still be explicit.

## Ring buffer overrun

When events are emitted faster than consumers drain them, the ring buffer fills and KMES overwrites the oldest events to make space.

- The write path is never blocked. Emission never fails due to buffer pressure -- buffer-full conditions are handled by overwriting, not blocking.
- Consumers detect lost events as gaps in the per-CPU sequence number.
- Consumers whose read position has been overwritten are advanced to `tail_pos` (the oldest surviving event).
- KMES maintains an internal per-CPU dropped-event counter. This counter is not exposed in the ring buffer metadata in v0.22 but MAY be exposed in a future version.

Overrun is a normal operating condition under heavy load, not an error. The system degrades gracefully: recent events are preserved, old events are lost, consumers are aware of the loss.

## Event drop

An event is dropped without being written to the ring buffer when:

- **Structural limit exceeded.** The event exceeds 50% of the per-CPU ring buffer capacity. Applies to both kernel and syscall emitters.
- **Policy limit exceeded** (syscall only). The event exceeds MaxEventSize.
- **Validation failure** (syscall only). The payload is not valid msgpack or exceeds MaxNestingDepth.

For kernel emitters, the per-CPU sequence number advances even when an event is dropped, making the drop visible to consumers as a gap in the sequence. The emitting subsystem is not notified, as the emission API is fire-and-forget.

For syscall emitters, validation failures occur before the ring buffer write phase, so no sequence number is consumed and no gap is visible to consumers. The drop is visible only to the caller via the syscall error return.

## Consumer crash

If a consumer process (e.g., eventd) crashes:

- The consumer's mmap'd ring buffer regions remain valid in kernel memory. The kernel cleans up the mappings when the process's file descriptors are closed (normal kernel fd cleanup on process exit).
- KMES is unaffected. It continues writing events to the per-CPU ring buffers regardless of whether any consumers are attached.
- Events emitted while no consumer is attached accumulate in the ring buffers. If the buffers fill, oldest events are overwritten.
- When a consumer restarts and re-attaches (calls `kmes_attach` for each CPU and mmaps the buffers), it sees all surviving events. Events overwritten during the outage are visible as a sequence gap starting from whatever sequence number the consumer last processed.

KMES has no dependency on consumers. A system with no consumers attached operates identically to a system with consumers -- events are emitted, stamped, buffered, and eventually overwritten.

## Buffer swap failure

When KMES attempts to create new ring buffers (due to a BufferCapacity configuration change or the boot-to-registry transition), memory allocation may fail.

- If allocation fails, KMES retains the existing ring buffers at their current size. The configuration change is not applied.
- An event is emitted via KMES itself recording the allocation failure and the retained buffer size.
- The generation counter is not incremented. Consumers are unaffected.
- KMES does not retry automatically. A subsequent configuration write (or system reboot) triggers another attempt.

## LCS unavailable

If LCS never becomes available (no source registers), KMES operates indefinitely with compiled-in defaults. The ring buffers are created at the default BufferCapacity. The self-configuration watch is never armed because there is no registry to watch.

This is not a failure -- it is a valid operating mode. KMES has no hard dependency on LCS. The only consequence is that operational parameters cannot be tuned.

## Clock discontinuity

KMES timestamps use `CLOCK_REALTIME` (wall clock). NTP adjustments can cause the clock to jump forward or backward. When this occurs:

- Events emitted after a backward jump have timestamps earlier than events emitted before the jump. Consumers that sort by timestamp will see an apparent reordering.
- Per-CPU sequence numbers are unaffected (they are monotonic counters, not derived from the clock). Sequence numbers remain the reliable ordering primitive within a single CPU.
- KMES does not detect or compensate for clock discontinuities. Consumers that require monotonic ordering within a CPU SHOULD use the sequence number, not the timestamp.

Cross-CPU ordering during a clock discontinuity is best-effort. Events from different CPUs near a clock jump may have misleading relative timestamps. This is an inherent limitation of wall clock timestamps and is accepted as a trade-off for human-readable, cross-boot-comparable timestamps.

## CPU hotplug

CPU hotplug (adding or removing CPUs at runtime) is not supported in v0.22. The number of per-CPU ring buffers is fixed at KMES initialisation time based on the number of online CPUs when PKM loads. If a CPU is brought online after KMES initialisation, events emitted on that CPU are dropped.

A future version MAY support dynamic per-CPU buffer creation for hotplugged CPUs.

## Memory bounding

KMES kernel memory usage is bounded by:

- **Per-CPU ring buffers:** `num_cpus × BufferCapacity`. At defaults (4 CPUs × 4 MB), 16 MB. Ceiling is `num_cpus × 256 MB`, configurable only by administrators.
- **Per-CPU boot buffers:** `num_cpus × boot_buffer_size`. Compiled-in constant. Freed after ring buffers are created.
- **Event construction:** Temporary allocations during event construction are bounded by the maximum event size and freed immediately after the event is written to the ring buffer.
- **Consumer file descriptors:** Each `kmes_attach` call creates one file descriptor. A consumer attaching to all CPUs creates `num_cpus` file descriptors. Bounded by RLIMIT_NOFILE and the SeSecurityPrivilege requirement.

No KMES-specific global memory cap is required. The BufferCapacity configuration and standard Linux resource limits provide sufficient protection.
