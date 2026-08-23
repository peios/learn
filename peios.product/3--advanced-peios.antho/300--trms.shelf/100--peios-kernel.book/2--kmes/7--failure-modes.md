---
title: Failure Modes
description: Ring overrun, event drops, consumer crashes, buffer swap failure, LCS unavailability and clock discontinuity — what each does.
---

KMES has no external trust boundary on the write path: kernel emitters
are trusted, and userspace emitters are validated at the syscall
boundary (§2.4). Its failure semantics are correspondingly simpler
than a subsystem like LCS that spans the kernel-userspace boundary in
both directions.

## Ring overrun

When events are emitted faster than consumers drain them, the buffer
fills and KMES overwrites the oldest events. The write path is never
blocked and emission never fails from buffer pressure. Consumers see
the loss as gaps in the per-CPU sequence, and a consumer whose read
position has been overtaken re-anchors to the oldest surviving event.

Overrun is a normal operating condition under load, not an error: the
system degrades by keeping recent events, losing old ones, and telling
consumers that it did.

Two bulk-loss cases sit outside that model. The tail resynchronisation
guard (§2.5) can discard an entire surviving window at once when a
size field reads back implausibly, and a shrinking capacity swap drops
the oldest events that do not fit the new ring. Neither itemises the
discarded events in the drop counter, though both are traced.

## Event drop

An event is dropped without reaching the buffer when a structural
limit is exceeded — an event type length that cannot be encoded in the
header's `u16` field, or an event larger than half the ring capacity —
and, for syscall emitters only, when the event exceeds `MaxEventSize`
or the payload fails msgpack validation.

The two paths differ in what a consumer sees. For kernel emitters the
sequence number is consumed before the structural checks run, so the
drop appears as a sequence gap; the emitting subsystem is not
notified, since emission is fire-and-forget. For syscall emitters
validation completes before the write phase, so no sequence number is
consumed and no gap appears — the drop is visible only to the caller,
as the syscall's error return.

Events emitted before KMES initialisation completes are discarded with
no sequence consumed and no counter incremented, and are therefore
invisible to consumers in both ways.

The internal per-CPU dropped-event counter aggregates structural drops
and overwrite losses together. It is not exposed in the ring metadata
and is reachable only through the KUnit test interface.

## Consumer crash

A crashed consumer's mappings are cleaned up by the ordinary kernel
path when its file descriptors close on process exit, and the rings
themselves are reference-counted, so they survive until the last
reference goes. KMES is unaffected and keeps writing regardless of
whether any consumer is attached — a system with no consumers behaves
identically to one with consumers, events simply being stamped,
buffered, and eventually overwritten. A restarted consumer re-attaches
and sees every surviving event, with the outage visible as a sequence
gap.

## Buffer swap failure

If replacement rings cannot be allocated, the existing rings stay live
at their current size, the configuration change is not applied, no
generation changes, and consumers are unaffected. A
`KMES_BUFFER_SWAP_FAILED` event records the requested and retained
capacities (§2.6). KMES does not retry; the next configuration write
or a reboot triggers another attempt.

## LCS unavailable

If no source ever registers, KMES runs indefinitely on compiled-in
defaults with the boot-time rings live and the configuration watch
never armed. This is a valid operating mode, not a failure — the only
consequence is that the parameters cannot be tuned.

## Clock discontinuity

Timestamps come from `CLOCK_REALTIME`, so an NTP adjustment can move
them forward or backward and consumers sorting by timestamp will see
an apparent reordering. Sequence numbers are unaffected: they are
independent monotonic counters, never derived from the clock, and
remain the reliable ordering primitive within a CPU. KMES neither
detects nor compensates for discontinuities. Cross-CPU ordering near a
jump is best-effort — an inherent cost of wall-clock timestamps,
accepted for their readability and cross-boot comparability. Rate
limiting is immune, being driven by the monotonic clock.

System suspend and hibernate are special cases of the same thing. Ring
contents survive suspend to RAM, and are restored from the hibernate
image on resume; in both cases the clock jumps forward by the sleep
duration, so consumers see a wall-clock gap with no sequence gap.

## CPU topology

The set of rings is fixed at initialisation from the kernel's
possible-CPU set, and topology changes are not handled dynamically.

A CPU that was possible but offline at initialisation already has a
ring: if it comes online later, its events go to that ring, and
consumers can attach to it throughout. A CPU whose logical index was
outside the possible-CPU set has no ring, and `kmes_attach` rejects
that index; KMES neither creates rings for such CPUs nor publishes
topology-change notifications. A CPU taken offline through `cpu_online` keeps its ring,
and a consumer draining it simply sleeps indefinitely, unable to
distinguish a quiet CPU from a departed one. Hot-add is the realistic
case — hypervisors adding vCPUs to a running guest — while hot-remove
is rare outside mainframes.

Anything that fixes this is additive: a topology-change notification,
whether a generation bump meaning "re-enumerate", a dedicated
descriptor, or a status field in the metadata page, fits the existing
attach-per-CPU design without changing the ring format, the event
format, or the emission API.

One structural caveat applies to attach discovery. The index bound is
the count of rings successfully created, while rings are indexed by
logical CPU id. On a system whose possible-CPU mask has holes, the two
differ: the "attach with incrementing indexes until `EINVAL`" loop
stops early, and rings at high logical indexes are unreachable.

Each logical CPU — each hardware thread under SMT — gets its own ring,
so ring memory scales with threads rather than cores: at the 4 MB
default a 64-core, 128-thread machine holds 512 MB of ring buffers.
This follows from events being emitted per logical CPU and `cpu_id`
naming the logical CPU.

## Memory bounding

Ring memory in steady state is `num_cpus × BufferCapacity` for the
fixed CPU count fixed at initialisation, plus two metadata pages per CPU and one shmem page
per ring that has ever been attached. During a capacity swap old and
new rings coexist until every mapping of the old generation is
released.

Transient allocation during emission is bounded by the event size for
a single emit and freed as soon as the event is written. A batch is
different: every entry is staged in kernel memory simultaneously, so a
batch holds up to `count × MaxEventSize` — 256 entries at a 4 MB
maximum event size — until its write phase completes.

Each `kmes_attach` creates one file descriptor, bounded by
`RLIMIT_NOFILE` and by the SeSecurityPrivilege requirement. No
KMES-specific global memory cap exists; the capacity configuration and
standard Linux resource limits are the bounds.

## Allocation and timing choices

The data region is a plain `vzalloc` allocation of 4 KB pages, and the
mmap handler inserts pages one at a time, so hugepage backing is not
available to it. The difference is substantial for TLB coverage: a 4 MB
ring needs 1024 standard pages against 2 hugepages, and because the
double mapping doubles the virtual range, 2048 standard pages against
4 hugepages. Allocation is not NUMA-aware: pages come from the
general allocator with no attempt to place a ring on the node local to
its CPU, so writes on a CPU whose ring landed on a remote node cross
the interconnect — roughly 100-150 ns against about 70 ns for a local
node. Timestamps use the full `ktime_get_real_ns()` rather
than `ktime_get_real_fast_ns()`, which avoids the timekeeper seqlock
and costs roughly 15-25 ns less per event at the price of being up to
one tick stale when a timer interrupt is updating the timekeeper
concurrently. Headers are built field by field
on every event with no precomputed per-CPU template, msgpack
validation is scalar, and each staged syscall event takes its own
`kvmalloc` rather than drawing on a per-CPU staging buffer.

None of these choices affects the ring format, the event header, or
the consumer protocol.
