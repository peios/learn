---
title: Ring Buffer
---

## Overview

The ring buffer is the sole delivery mechanism from KMES to userspace consumers. KMES maintains one ring buffer per CPU. Each per-CPU buffer is an independent shared memory region, independently mappable, with its own metadata, write position, and futex counter. There is no shared state between per-CPU buffers on the write path.

This per-CPU design eliminates all contention on the event emission path. Each CPU writes to its own buffer using its own counters. No atomic operations contend across CPUs. This is critical for workloads where KMES traces every syscall across many cores.

Consumers read from per-CPU buffers independently. Each buffer is a complete, self-contained ring buffer -- the same structure, the same read protocol, the same overwrite semantics. The per-CPU design does not change the ring buffer contract; it replicates it.

## Boot buffer

KMES begins buffering events the instant PKM loads, before the registry is available. During this early boot window, events are stored in internal kernel boot buffers (one per CPU). Boot buffers are not visible to consumers and cannot be mapped.

When LCS becomes available, KMES reads the configured ring buffer size from the registry, creates the consumer-facing per-CPU ring buffers at that size, and copies all surviving boot buffer events into them. The boot buffers are then discarded.

If LCS is not available (module loaded without registry), KMES creates the ring buffers at a compiled-in default size.

Boot buffers use the same circular overwrite semantics as ring buffers. If a boot buffer fills before the ring buffer is created, the oldest events are overwritten. The boot buffer size is a compiled-in constant.

## Capacity

All per-CPU ring buffers share the same capacity. The capacity MUST be a power of two. This allows the wrap-around offset calculation to use a bitwise AND (`position & (capacity - 1)`) instead of a modulo operation. Every event read and write hits this calculation.

The capacity is configurable via the registry. The compiled-in default is used when the registry is not yet available. The minimum and maximum permitted capacities are implementation-defined but MUST both be powers of two.

## Double virtual mapping

Each ring buffer's physical pages are mapped twice consecutively in virtual memory. If the ring buffer occupies N physical pages, the data region spans 2N pages of virtual address space, with the second N pages mapping the same physical memory as the first N.

```
Physical pages:  [0][1][2][3]
Virtual mapping: [0][1][2][3][0][1][2][3]
```

This eliminates all wrap-around handling. When KMES writes an event that crosses the end of the buffer, the write continues into virtual addresses that map back to the beginning of the physical buffer. No branch, no split write, no padding. A single contiguous `memcpy` handles every write regardless of position.

Consumers benefit identically -- an event that wraps around the physical boundary is read as a single contiguous byte sequence from the consumer's perspective.

## Mapped region layout

When a consumer calls `mmap()` on a per-CPU file descriptor returned by `kmes_attach`, the mapped region has the following layout:

| Region | Size | Description |
|---|---|---|
| Producer metadata page | 4096 bytes | KMES-written control fields. Mapped read-only to consumers. |
| Consumer metadata page | 4096 bytes | Consumer-written fields. Mapped read-write to consumers. |
| Data region | 2 × capacity | The double-mapped ring buffer containing events. Mapped read-only to consumers. |

The total mapping size is `8192 + (2 × capacity)` bytes. Every per-CPU buffer has the same layout and the same capacity.

The consumer maps the entire region with a single `mmap()` call on the per-CPU file descriptor: `mmap(NULL, 8192 + 2 * capacity, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0)`. The kernel's mmap handler enforces per-page permissions internally: the producer metadata page and data region pages are mapped read-only regardless of the requested PROT flags, the consumer metadata page is mapped read-write. The consumer does not need to issue separate mmap calls for each region. The consumer discovers `capacity` from the `kmes_attach` syscall (see the Syscall Interface section).

The mapping is split into read-only and read-write regions to enforce a trust boundary. KMES writes to the producer metadata page and the data region; consumers can only read these. Consumers write to the consumer metadata page; KMES reads from it but treats all values as advisory -- a corrupted consumer page cannot affect KMES correctness or the producer metadata.

The consumer metadata page is shared between all consumers attached to the same per-CPU buffer. A malicious consumer with SeSecurityPrivilege could overwrite `need_wake` to suppress notification to other consumers on the same buffer. This is accepted because SeSecurityPrivilege is a very high-trust privilege -- normal event consumers use eventd (which enforces per-event SD-based access control), not direct ring buffer access.

## Producer metadata page (offset 0, read-only)

The producer metadata page is laid out to prevent false sharing. Fields that are updated at different frequencies are placed on separate 64-byte cache lines.

False sharing occurs when two independent fields share a cache line. Updating one field invalidates the cache line in every CPU core, forcing all cores to re-fetch the line even for the unchanged field. In the per-CPU design, false sharing between CPUs is eliminated by using separate buffers. Cache line separation within a buffer prevents false sharing between the producing CPU and consuming threads.

### Cache line 0 -- static fields (bytes 0--63)

Written once when the ring buffer is created. Never modified after initialisation. Consumers MAY cache these values for the lifetime of the mapping.

| Offset | Size | Type | Field | Description |
|---|---|---|---|---|
| 0 | 8 | `[u8; 8]` | `magic` | Magic byte sequence identifying this as a KMES ring buffer. Value: `4B 4D 45 53 52 49 4E 47` (`KMESRING` in ASCII). Compared byte-by-byte, not as an integer. |
| 8 | 4 | `u32` | `version` | Ring buffer format version. v0.20 uses version 1. |
| 12 | 2 | `u16` | `cpu_id` | The CPU this buffer belongs to. |
| 14 | 2 | `u16` | `reserved0` | Reserved. Must be zero. |
| 16 | 8 | `u64` | `capacity` | Data region capacity in bytes. Power of two. |
| 24 | 8 | `u64` | `data_offset` | Byte offset from the start of the mapping to the data region. Equal to the combined metadata size (8192). |
| 32 | 8 | `u64` | `generation` | Buffer generation counter. Starts at 1 for the first ring buffer created on each CPU. Monotonically increasing across buffer swaps -- the new buffer's generation is the old buffer's incremented value. |
| 40 | 24 | -- | `reserved1` | Reserved. Must be zero. Pads to cache line boundary. |

### Cache line 1 -- producer fields (bytes 64--127)

Written by KMES on every event write to this CPU's buffer. This is the hottest cache line in the ring buffer. In the per-CPU design, only one CPU ever writes to this cache line, eliminating cross-core invalidation.

| Offset | Size | Type | Field | Description |
|---|---|---|---|---|
| 64 | 8 | `u64` | `write_pos` | Monotonically increasing byte offset of the next write position. Never wraps -- at 1 GB/s sustained throughput, a `u64` byte offset would take over 500 years to overflow. The actual data region offset is `write_pos & (capacity - 1)`. Initialized to 0 on a fresh buffer (advanced after boot buffer events are copied). |
| 72 | 8 | `u64` | `tail_pos` | Byte offset of the oldest surviving event. Advanced by KMES when events are overwritten. Consumers whose read position is behind `tail_pos` have been lapped. Initialized to 0 on a fresh buffer. |
| 80 | 48 | -- | `reserved2` | Reserved. Must be zero. Pads to cache line boundary. |

### Cache line 2 -- notification fields (bytes 128--191)

Written by KMES when waking consumers. Read by consumers for futex-based sleep.

| Offset | Size | Type | Field | Description |
|---|---|---|---|---|
| 128 | 4 | `u32` | `futex_counter` | Counter incremented by KMES when waking sleeping consumers. Consumers use `futex_wait` on this address. `u32` because Linux `futex(2)` operates on 32-bit integers. Only incremented when `need_wake` is set. |
| 132 | 60 | -- | `reserved3` | Reserved. Must be zero. Pads to cache line boundary. |

## Consumer metadata page (offset 4096, read-write)

The consumer metadata page is mapped read-write to consumers. KMES reads from this page but treats all values as advisory. A malicious or buggy consumer that corrupts this page can only affect its own notification behavior -- it cannot affect KMES correctness, the producer metadata, the data region, or other consumers' view of producer metadata.

| Offset | Size | Type | Field | Description |
|---|---|---|---|---|
| 4096 | 1 | `u8` | `need_wake` | Consumer-managed flag. Set to 1 by the consumer before sleeping. Read by KMES after writing an event -- KMES treats any nonzero value as 1. If 0, KMES skips the futex_counter increment and futex_wake entirely. Cleared by the consumer after waking. |
| 4097 | 4095 | -- | `reserved4` | Reserved. Must be zero. Pads to page boundary. |

Under sustained load, the consumer is always draining and `need_wake` remains 0. KMES reads `need_wake`, sees 0, and skips all notification overhead -- no futex_counter increment, no futex_wake syscall. The entire notification path costs a single memory read per event (~1ns). Under low load, the consumer sets `need_wake` before sleeping, and KMES performs the full wake sequence when the next event arrives.

## Write protocol

Each per-CPU buffer has exactly one writer: the CPU it belongs to. There is no cross-CPU contention on any write operation. The write protocol uses no locks and no cross-CPU atomic operations.

For each event on a given CPU:

1. Capture the wall clock timestamp (`CLOCK_REALTIME`).
2. Increment the CPU's per-boot sequence counter and take the new value. This is a CPU-local operation with no contention.
3. Build the packed event header (timestamp, sequence number, cpu_id, origin class, event type).
4. Compute the total event size (header + payload).
5. If the total event size exceeds 50% of the ring buffer capacity, drop the event. The sequence number is consumed, creating a visible gap. Increment the internal dropped-event counter. Stop.
6. If `write_pos + event_size - tail_pos > capacity`, the write would overwrite surviving events. Advance `tail_pos` past overwritten events by reading each overwritten event's `event_size` field and adding it to `tail_pos` until sufficient space is available. Store `tail_pos` with a release memory barrier.
7. Write the event (header + payload) into the data region at offset `write_pos & (capacity - 1)`. The double virtual mapping ensures this is a single contiguous write even if it crosses the physical buffer boundary.
8. Store the new `write_pos` (old value + event size) with a release memory barrier. This barrier ensures the event data is fully visible to consumers before `write_pos` advances.
9. Read `need_wake`. If `need_wake` is 0, stop -- no consumer is sleeping. If `need_wake` is 1, increment `futex_counter` with a release store and issue `futex_wake` to wake all waiting consumer threads.

During batch writes, steps 8--9 are deferred until all events in the batch have been written. A single release store of `write_pos` and a single `need_wake` check cover the entire batch. The overwrite check (step 6) uses an internal running write offset that tracks the current write frontier within the batch, not the consumer-visible `write_pos`.

The release barriers in steps 6 and 8 establish the ordering guarantee: a consumer that observes the new `write_pos` is guaranteed to observe the fully written event data and the correct `tail_pos`.

## Read protocol

Consumers read events directly from the mapped data region. The read protocol uses no locks and no syscalls during the event drain loop.

Each consumer maintains its own read position per buffer in process-local memory. KMES does not track consumer read positions and is not aware of how many consumers exist or how far behind they are. A consumer SHOULD initialize its `read_pos` to `tail_pos` on first attachment, starting from the oldest surviving event.

Events are packed contiguously in the data region with no alignment padding between them. `event_size` is the exact byte count of the event (header + payload) with no trailing padding. The next event begins immediately at the byte following the previous event.

A consumer typically dedicates one thread per CPU buffer. Each thread independently drains its buffer using the following protocol.

### Drain loop

1. Load `write_pos` with an acquire memory barrier. If `write_pos == read_pos`, no new events are available. Proceed to notification wait.
2. Load `tail_pos` with an acquire memory barrier. If `read_pos < tail_pos`, the consumer has been lapped -- events at `read_pos` have been overwritten. Set `read_pos = tail_pos`. The gap between the old `read_pos` and `tail_pos` represents lost events, detectable as a sequence number gap.
3. Save the current `tail_pos` as `saved_tail`.
4. Read the event at data region offset `read_pos & (capacity - 1)`. The double virtual mapping ensures this is a contiguous read.
5. Re-read `tail_pos`. If `tail_pos > saved_tail` AND `read_pos < tail_pos`, the event was overwritten during the read (torn read). Discard the event and go to step 2.
6. Validate `event_size > 0` and `event_size >= header_size`. If either check fails, the event data is corrupt -- the consumer SHOULD advance to `tail_pos` and continue from step 2. An `event_size` of 0 would cause an infinite loop; an `event_size` smaller than `header_size` indicates a malformed header.
7. The event is valid. Process it. Advance `read_pos` by the event's `event_size`. Consumers MUST NOT read beyond the event's `event_size` boundary -- stale data from previously overwritten events may be present in the data region. Go to step 1.

### Notification wait

When no events are available on a given buffer:

1. Store 1 to `need_wake` with a release memory barrier. This signals KMES that the consumer is about to sleep.
2. Re-read `write_pos` with an acquire barrier. If new events have arrived since the drain loop exited (KMES wrote between the drain loop's check and the `need_wake` store), clear `need_wake` to 0 and return to the drain loop.
3. Read the current `futex_counter` value.
4. Optionally spin briefly, re-checking `write_pos` for new events. If events arrive during the spin window, clear `need_wake` to 0 and return to the drain loop. The spin duration is a consumer implementation choice.
5. Call `futex_wait(futex_counter_address, last_seen_value)`. The kernel puts the thread to sleep if `futex_counter` has not changed since it was read. This is a genuine kernel sleep -- the thread is descheduled and consumes no CPU.
6. On wake (KMES incremented `futex_counter` and called `futex_wake`), clear `need_wake` to 0 and return to the drain loop.

Clearing `need_wake` to 0 (steps 2, 4, and 6) is a plain (relaxed) store -- no memory barrier is required. If KMES observes a stale `need_wake` of 1 after the consumer has already cleared it, KMES performs a spurious `futex_wake` on a thread that is already awake. This is harmless -- `futex_wake` on a non-sleeping thread is a no-op.

The re-check at step 2 closes the race window between the drain loop finding no events and the `need_wake` store. If KMES writes an event and reads `need_wake` as 0 (because the consumer hasn't stored it yet), the consumer will see the new `write_pos` at step 2 and never enter `futex_wait`.

The adaptive spin in step 4 is optional. Without it, the consumer sleeps immediately when the buffer is empty and is woken by KMES. With it, the consumer catches closely-spaced events without a kernel round-trip. Under sustained load, the consumer never reaches the notification wait -- it stays in the drain loop and `need_wake` remains 0.

### Generation check

After completing a drain cycle (buffer fully drained or batch limit reached), the consumer SHOULD check the `generation` field in the metadata page.

If `generation` has changed since the consumer last checked:

1. Record the sequence number of the last successfully processed event from this buffer.
2. Call `kmes_attach` to obtain new file descriptors for the resized ring buffers.
3. `mmap` the new file descriptor for this CPU.
4. Read the new buffer's metadata (`capacity`, `write_pos`, `tail_pos`).
5. Scan events in the new buffer to find the first event with a sequence number greater than the recorded sequence number. Set `read_pos` to that event's position.
6. Close the old file descriptor and unmap the old buffer.
7. Continue draining from the new buffer.

Events MUST NOT be lost during a generation change. KMES copies surviving events from the old buffer into the new buffer before incrementing `generation`, and sequence numbers are continuous across the swap. Events are re-compacted during the copy -- they are written contiguously starting from position 0 in the new buffer. The consumer's old `read_pos` is not valid in the new buffer; it MUST scan by sequence number to find its position.

The consumer MUST finish draining the old buffer up to its frozen `write_pos` before switching to the new buffer. After the swap, KMES stops writing to the old buffer; its `write_pos` is frozen.

The old buffer's physical pages remain valid for as long as any consumer has them mapped. KMES's internal release of the old buffer does not affect existing consumer mappings -- standard kernel mmap reference counting ensures the pages persist until all consumers have unmapped them.

### Buffer swap serialization

The buffer swap MUST be atomic per CPU: no events may be lost or duplicated during the transition from the old buffer to the new buffer on a given CPU.

An implementation MAY achieve this with the following per-CPU algorithm:

1. Disable preemption on the target CPU.
2. Copy surviving events from this CPU's old buffer to the new buffer, re-compacted contiguously starting from position 0. Events are copied in sequence order. Set the new buffer's `tail_pos = 0` and `write_pos` to the total byte size of the copied events.
3. Set the new buffer's `generation` to the old buffer's `generation + 1`. The new buffer MUST be fully initialized before consumers can see it.
4. Switch the per-CPU buffer pointer from the old buffer to the new buffer. New events are now written to the new buffer.
5. Increment `generation` in the old buffer's metadata. This signals consumers still reading the old buffer that a swap has occurred and they should re-attach.
6. Re-enable preemption.

The new buffer's `generation` is set before it becomes visible (step 3 before step 4). The old buffer's `generation` is incremented after the switch (step 5 after step 4). This ensures consumers see a consistent generation value regardless of whether they read from the old or new buffer.

With preemption disabled, no events can be emitted on this CPU between the copy and the switchover. Events emitted on other CPUs are unaffected -- each CPU's swap is independent.

The generation check adds one `u64` read per drain cycle. This cost is negligible relative to the event processing work.

## Overwrite semantics

Each per-CPU ring buffer is circular. When a buffer is full, KMES overwrites the oldest events in that buffer to make space for new events. The write pointer advances unconditionally -- emission never blocks.

Consumers detect overwritten events in two ways:

- **Lapping detection.** If `read_pos < tail_pos`, events at the consumer's read position have been overwritten. The consumer advances to `tail_pos`.
- **Sequence gaps.** The consumer tracks the last sequence number it processed from each CPU. A gap in the sequence for a given CPU indicates events were lost -- either overwritten in the ring buffer or dropped due to size limits.

KMES maintains `tail_pos` per buffer to enable lapping detection. When KMES overwrites events, it advances `tail_pos` past the overwritten events by reading each event's `event_size` field. This allows consumers to jump directly to the oldest valid event without scanning.

Advancing `tail_pos` requires walking overwritten events sequentially, reading each event's `event_size` to determine the next event boundary. This has variable latency proportional to the number of overwritten events and may involve cache-cold reads (the tail region may be megabytes away from the current write position). This cost is accepted as a tradeoff -- the alternative (maintaining a secondary index of event offsets) would add per-event overhead on the write path to optimize the uncommon case where the write pointer overtakes surviving events.

## Memory ordering summary

| Operation | Barrier | Purpose |
|---|---|---|
| KMES stores `tail_pos` | release | Consumers see the advanced tail before they see new data at old positions. |
| KMES stores `write_pos` | release | Consumers see complete event data before they see the advanced write position. |
| KMES stores `futex_counter` | release | Consumers waking from futex see all prior writes. |
| Consumer stores `need_wake = 1` | release | KMES sees the flag before the consumer enters futex_wait. |
| Consumer stores `need_wake = 0` | relaxed | Spurious futex_wake from stale read is harmless. |
| Consumer loads `write_pos` (after setting `need_wake`) | acquire | Closes the race window: if KMES wrote before seeing `need_wake`, the consumer sees the write. |
| Consumer loads `write_pos` (drain loop) | acquire | Pairs with KMES release on `write_pos`. |
| Consumer loads `tail_pos` | acquire | Pairs with KMES release on `tail_pos`. |

In the per-CPU design, the producer (KMES on CPU N) and the consumer (a userspace thread, potentially on a different CPU) are the only two parties accessing a given buffer's metadata. There is no multi-producer contention. The memory barriers ensure correct visibility between the single producer and its consumers.

On x86-64, stores are not reordered with other stores, so the release barriers on the producer side are no-ops in practice. The specification mandates them for architectural correctness on all platforms.
