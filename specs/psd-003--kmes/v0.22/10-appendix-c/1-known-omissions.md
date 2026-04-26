---
title: Known Omissions
---

This appendix lists capabilities that are intentionally omitted from v0.22 but are expected to be addressed in future versions. All items listed here are additive -- they can be implemented without restructuring the core ring buffer design, the syscall interface, or the event format.

## CPU topology changes

v0.22 fixes the set of per-CPU ring buffers at KMES initialisation time. The following topology changes are not handled:

**CPU hot-add.** A CPU brought online after KMES initialisation has no ring buffer. Events emitted on that CPU are dropped silently. The `kmes_attach(cpu_id)` API returns EINVAL for the new CPU.

**CPU offline.** A CPU taken offline via `cpu_online` still has a ring buffer. The drain thread for that CPU sleeps on `futex_wait` indefinitely since no new events are emitted. This is harmless (one sleeping thread) but not clean.

**CPU hot-remove.** A CPU that had a ring buffer is physically removed. The drain thread sleeps forever on a buffer that will never receive new events. Without a notification mechanism, the consumer cannot distinguish a quiet CPU from a removed one.

The fix for all three is a topology change notification mechanism. Options include a new generation bump that signals "re-enumerate CPUs", a dedicated topology-change file descriptor, or a field in the producer metadata page indicating CPU status. The `kmes_attach(cpu_id)` design accommodates all of these -- consumers discover new CPUs by extending their attach loop, and detect removed CPUs via a status field or error code. No changes to the ring buffer format, event format, or emission API are required.

CPU hot-add is the most likely real-world scenario (hypervisors adding vCPUs to a running guest). CPU hot-remove is rare outside mainframes.

## NUMA-aware buffer allocation

v0.22 does not specify which NUMA node ring buffer pages are allocated on. If a ring buffer's physical pages are allocated on a remote NUMA node, every event write on that CPU crosses the interconnect. At KMES throughput targets (millions of events per second), remote NUMA writes add measurable latency.

The fix is to allocate each per-CPU ring buffer's physical pages on the NUMA node local to that CPU. This is a kernel allocation policy change (`alloc_pages_node` or equivalent) with no consumer-visible effect. The ring buffer format, mapping layout, and syscall interface are unchanged.

## Suspend/resume

v0.22 does not explicitly address system suspend (S3 sleep) or hibernate (S4). Ring buffer contents survive S3 (memory is preserved). On resume, `CLOCK_REALTIME` jumps forward by the suspend duration. This is a special case of the clock discontinuity described in §7.1 -- consumers see a wall clock gap in timestamps but no sequence number gap.

S4 (hibernate) writes memory to disk. On resume, ring buffers are restored from the hibernate image. The same clock discontinuity applies. If the kernel re-initialises KMES on resume (implementation-dependent), the generation counter signals consumers to re-attach.

No architectural change is needed. A future version MAY add an explicit note to the clock discontinuity section covering suspend/resume.

## SMT capacity planning

Each logical CPU (hardware thread) receives its own ring buffer. On a system with simultaneous multithreading (e.g., 2 threads per core), the total ring buffer memory is doubled compared to a physical-core-only count. At the default 4 MB capacity on a 64-core / 128-thread system, total ring buffer memory is 512 MB.

This is by design -- events are emitted per logical CPU and the `cpu_id` in event headers reflects the logical CPU. The per-logical-CPU design is correct. A future version MAY add guidance on capacity tuning for SMT-heavy systems.
