---
title: Recommended Implementation Optimisations
---

The following optimisations are not normative. They do not affect the ring buffer format, the event header layout, or the consumer protocol. An implementation that omits all of them is fully conformant. However, each one provides measurable throughput or latency improvement with no behavioural trade-offs, and implementers are encouraged to adopt them.

## Timestamp capture

Timestamp capture (`CLOCK_REALTIME`) is the single most expensive per-event operation on the write path, at approximately 15--25 ns per call. Implementations SHOULD use `ktime_get_real_fast_ns()` -- the kernel-internal fast path that avoids the full timekeeper seqlock dance. On architectures with an invariant TSC (Time Stamp Counter), this reduces to an `rdtsc` instruction plus a multiply and add. The trade-off is that in the rare case where a timer interrupt is updating the timekeeper concurrently, the timestamp may be off by one tick. For nanosecond-precision event timestamps, this is acceptable.

## Hugepages

The ring buffer data region benefits from 2 MB hugepages rather than 4 KB standard pages. A 4 MB ring buffer requires 1024 standard pages but only 2 hugepages. Fewer pages means fewer TLB (Translation Lookaside Buffer -- the CPU's cache of virtual-to-physical address mappings) entries are needed to cover the buffer. TLB misses during event reads and writes add ~10-30 ns each, and a large buffer with standard pages can cause frequent misses during sequential traversal.

The double virtual mapping doubles the virtual address range, so the TLB benefit of hugepages is even more pronounced: 4 MB of physical memory mapped as 8 MB of virtual space requires 4 hugepages vs 2048 standard pages.

Hugepages are transparent to consumers -- the mmap'd region behaves identically regardless of the underlying page size.

## NUMA-local allocation

On NUMA (Non-Uniform Memory Access) systems, physical memory is divided into nodes. Each CPU has a local node with fast access (~70 ns) and remote nodes with slower access (~100-150 ns). Ring buffer pages SHOULD be allocated on the same NUMA node as the CPU that writes to them.

Since each ring buffer is written by exactly one CPU, NUMA-local allocation ensures all producer writes are fast. Consumer reads may cross NUMA boundaries (the consumer thread may run on a different node), but under the per-CPU design, the consumer thread can be affinity-bound to the same node as a secondary optimisation.

## Precomputed header templates

Several event header fields are constant for a given CPU: `cpu_id` and the header structure bytes (`header_size`, field offsets). A per-CPU header template can be precomputed at initialisation time. At emit time, KMES copies the template and fills in only the variable fields (`event_size`, `timestamp`, `sequence`, `origin_class`, `type_len`, `type`, and the three identity GUIDs). This reduces per-event header construction to a small memcpy plus a few stores.

For kernel emitters with a fixed origin class, the template can include the origin class as well, reducing the per-event work further. The identity GUIDs are per-thread and must be captured at emit time -- they cannot be templated.

## Software prefetch

After reading an event's `event_size` field, the consumer knows where the next event starts. Issuing a software prefetch instruction for the next event's header address (e.g., `__builtin_prefetch` in C, `prefetch` intrinsic in Rust) allows the CPU to begin fetching the next event's cache lines while the current event is being processed. This hides memory latency during sequential buffer traversal.

This is most effective when event processing involves non-trivial work (msgpack decoding, SQLite insertion) that gives the prefetch time to complete.

## Msgpack validation with SIMD

For the `kmes_emit` syscall path, msgpack payload validation can be accelerated using SIMD (Single Instruction, Multiple Data) instructions. The initial type-byte scan -- determining whether each byte is a fixint, a container header, or a data byte -- is amenable to vectorised classification using SSE4.2 or AVX2 byte-shuffle instructions. This reduces validation overhead for large payloads.

This optimisation is only relevant to the syscall path. Kernel emitters bypass payload validation entirely.

## Per-CPU staging buffer

The `kmes_emit` and `kmes_emit_batch` syscalls copy event data from userspace into a kernel buffer before validation and ring buffer write. A per-CPU pre-allocated staging buffer (e.g., one page / 4 KB) eliminates dynamic allocation from the common-case syscall path. Events exceeding the pre-allocated size fall back to `kmalloc`.

For batch emission, the staging buffer can be reused sequentially: copy entry 0, validate, hold the kernel copy; copy entry 1 into the same staging buffer if entry 0 has already been written to the ring buffer, or allocate a second buffer if entries must be held simultaneously. The goal is to avoid 256 separate `kmalloc` calls for a full batch.

## Consumer thread affinity

Consumer threads that drain per-CPU ring buffers benefit from being pinned to CPUs on the same NUMA node as the buffer they read. While not strictly necessary (the per-CPU design eliminates write contention regardless of consumer placement), NUMA-local reads avoid cross-node memory traffic during the drain loop.

For eventd specifically, pinning each drain goroutine's underlying OS thread to the same NUMA node as its buffer is a simple configuration that reduces read latency.
