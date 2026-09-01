---
title: Syscall Interface
description: The three KMES syscalls — emit, batch emit and attach — with their privilege gate, rate limiting, validation and preemption behaviour.
---

KMES exposes three syscalls in the PKM syscall range (1090–1099):
`kmes_emit` (1090) emits a single event from userspace, `kmes_attach`
(1091) attaches the caller as a consumer of one per-CPU ring buffer,
and `kmes_emit_batch` (1092) emits multiple events in one operation.
All three follow the standard Linux convention — they return −1 and
set errno on failure — and their numbers, entry struct layout, error
tables, and privilege masks are collected in §2.A.

Before KMES initialisation completes, all three syscalls fail with
`ENOMEM`. Before KACS initialisation, the emit syscalls fail closed
with `EPERM`, since privilege checks cannot be performed. [*syscalls.pre-init-fail-closed]

## kmes_emit

Emits one event. The origin class is set to 0 (userspace)
unconditionally — the caller cannot choose it — and the event is
written to the ring buffer of the CPU the calling thread is executing
on at write time. [*emit.origin-forced-zero]

### Privilege gate [*emit.privilege-gate]

The caller's effective token has to hold SeAuditPrivilege, enabled;
otherwise the syscall fails with `EPERM`. A successful gate records
SeAuditPrivilege as used on the token, as a KACS standalone privilege
gate; a failed gate records nothing. If recording the used state
itself fails, the syscall also fails with `EPERM`.

### Rate limiting [*emit.rate-limit]

Callers without enabled SeTcbPrivilege are rate limited per process by
a token bucket: the refill rate and the burst capacity both equal the
configured `MaxEmitRatePerProcess` (§2.6). The bucket is allocated
together with the process's KACS security state at fork, initialised
to full capacity, and freed when the process's security state is
released at exit. [*emit.rate.bucket-per-process-lifecycle] Refill is computed against the monotonic clock, so
wall-clock jumps do not affect it. [*emit.rate.monotonic-refill] When `MaxEmitRatePerProcess`
changes at runtime, the new rate and capacity take effect immediately
— rates are read live on every operation — and each bucket's current
token count is clamped down to the new capacity. [*emit.rate.reconfigure-applies-immediately]

A token is reserved up front and refunded if the syscall subsequently
fails, so validation failures cost nothing; the refund is clamped to
capacity, which means a refund landing just after a rate decrease can
forfeit the token. [*emit.rate.reserve-then-refund] An empty bucket fails the reserve with `EAGAIN`,
consuming nothing. [*emit.rate.empty-eagain] Callers holding enabled SeTcbPrivilege bypass the
bucket entirely, and the exemption records SeTcbPrivilege as used. [*emit.rate.tcb-bypass]

Rate state is per-process rather than per-SID: per-SID limiting would
penalise unrelated services sharing a SID (LocalService, for
instance). A process that forks to reset its limit is bounded by
`RLIMIT_NPROC`. [*emit.rate.per-process-not-per-sid]

### Validation [*emit.validation-order]

Validation runs in order and stops at the first failure; the errno
reflects the first failing check.

1. The privilege gate and rate reservation, above.
2. `event_type_len` is nonzero — `EINVAL` otherwise. [*emit.empty-type-einval]
3. The declared total event size (`77 + type_len + payload_len`) is
   computed from the length fields alone, without dereferencing either
   userspace pointer, with overflow-checked arithmetic — overflow is
   `EINVAL`. [*emit.size-computed-without-deref]
4. The declared size is within `MaxEventSize` — `ENOSPC` otherwise. [*emit.max-event-size-enospc]
5. The declared size is within 50% of the ring capacity — `ENOSPC`
   otherwise. At this stage the check runs against the first live
   ring's capacity; it is repeated against the actual target CPU's
   ring inside the write phase, so a capacity swap racing the syscall
   can surface `ENOSPC` after all other validation has passed. [*emit.half-capacity-enospc]
6. The event type and payload are copied into a kernel staging buffer
   (`EFAULT` if a pointer is inaccessible, `ENOMEM` if allocation
   fails). Everything after this point — validation and the ring
   write — operates on the kernel copy, closing the TOCTOU window in
   which userspace could rewrite the payload after validation. [*emit.staged-copy-closes-toctou]
7. The event type is validated as UTF-8 — `EINVAL` otherwise. [*emit.type-utf8-einval]
8. The payload is validated as msgpack within `MaxNestingDepth`
   (§2.2) — `EINVAL` otherwise. [*emit.payload-msgpack-einval]

### Preemption

Validation runs with preemption enabled — the userspace copies can
fault, and msgpack validation of a large payload takes microseconds.
Preemption is disabled only around the ring buffer write: determining
the CPU, stamping, writing, publishing `write_pos`, and checking
`need_wake`. The `cpu_id` and identity GUIDs therefore reflect the
thread's state at write time, not at syscall entry. [*emit.stamps-at-write-time] On success the
syscall returns 0 and the event is immediately visible to consumers. [*emit.success-immediately-visible]

## kmes_emit_batch

Emits up to 256 events in one call, sharing the privilege check, the
timestamp, the identity capture, and the single `write_pos`
publication across the batch. The 256-entry cap bounds the
preemption-disabled write window to roughly 50–100 microseconds for
typical event sizes.

The caller passes an array of 32-byte entry descriptors (layout in
§2.A; the descriptor padding bytes are documented as
reserved-must-be-zero in the ABI header but are not validated), a
`count`, and an `emitted_out` pointer. [*batch.padding-not-validated]

Processing order:

1. The SeAuditPrivilege gate, as for `kmes_emit`.
2. `count` is within 1–256 — `EINVAL` otherwise. [*batch.count-range-einval]
3. `count` tokens are reserved from the rate bucket in one critical
   section, so concurrent threads cannot both pass the check —
   `EAGAIN` if unavailable, and nothing is emitted. [*batch.tokens-reserved-atomically] SeTcbPrivilege
   exempts as before.
4. Zero is stored to `*emitted_out` before any per-entry work —
   `EFAULT` if unwritable, with nothing emitted. [*batch.emitted-out-zeroed-first]
5. The descriptor array is copied from userspace (`EFAULT`/`ENOMEM`).
6. Each entry, in order, goes through the same staging pipeline as
   `kmes_emit` — declared-size arithmetic, `MaxEventSize`, 50%
   capacity, userspace copy, UTF-8, msgpack. Staging stops at the
   first failing entry. [*batch.staging-stops-at-first-failure]
7. The validated prefix is emitted in one preemption-disabled write
   phase: one timestamp, one identity capture, a sequence number per
   event, origin class 0 throughout, and a single deferred
   publication that makes the whole prefix visible atomically. [*batch.prefix-visible-atomically]
8. Unused tokens (`count` minus events emitted) are refunded — only
   events actually emitted are charged. [*batch.unused-tokens-refunded]

On full success the syscall returns 0 and writes `count` to
`*emitted_out`. If entry N fails, entries 0 through N−1 are emitted,
N is written to `*emitted_out`, and the syscall returns −1 with the
errno of the failing entry. [*batch.partial-failure-reporting] Failed entries never consume sequence
numbers, so batch validation failures leave no consumer-visible gap. [*batch.no-gap-on-failure]
The final `emitted_out` store is a second write to userspace; if it
faults, the syscall reports `EFAULT` even though the prefix was
already emitted. [*batch.emitted-out-fault-after-emit]

Every staged entry is held in kernel memory simultaneously until the
write phase completes, so a batch's transient allocation is bounded by
`count × MaxEventSize` — up to 1 GB at the maximum settings — rather
than by a single event. [*batch.staging-held-simultaneously]

## kmes_attach

Attaches the caller as a consumer of one per-CPU ring buffer,
returning a file descriptor. The consumer contract built on this fd —
the mapped region layout, the drain and notification protocols, and
the re-attach protocol across buffer swaps — is specified in the PSPK
event stream chapter; the TRM side of the mechanics is §2.5.

The caller's effective token has to hold SeSecurityPrivilege, enabled
— `EPERM` otherwise — and a successful gate records SeSecurityPrivilege
as used. [*attach.privilege-gate] `cpu_id` is a logical CPU index using the same numbering as
the ring metadata and event headers.

The slot array is allocated at KMES initialisation and sized by
`nr_cpu_ids`, then filled by walking `for_each_possible_cpu`. Those two
quantities are not the same thing: the array size bounds a valid
`cpu_id`, while the ring count is however many of those slots got a
ring. They agree only when the possible-CPU mask is dense. An index at
or beyond the array size fails with `EINVAL`; so does an index inside
it whose slot holds no live ring. [*attach.slots-sized-by-nr-cpu-ids]

A consumer learns the array size by calling `kmes_attach` with
`cpu_id` set to `KMES_ATTACH_QUERY_SLOTS` (`0xFFFFFFFF`). The call
takes the same privilege gate, writes the slot count through
`capacity`, returns 0, and opens no descriptor. Enumeration then walks
0 to slots-1 and skips the indexes that answer `EINVAL`. [*attach.query-slots]

Counting up until the first `EINVAL` — which is what this interface
used to ask for — is wrong on a sparse mask: it stops at the first
hole, and every ring above it becomes permanently unreachable, filling
and overwriting with no consumer able to attach. [*attach.enumeration-skips-holes]

CPUs that were possible but offline at initialisation have rings and
are attachable; hotplug beyond the initial set is not handled (§2.7). [*attach.offline-possible-cpus-attachable]

On success the current ring capacity is written to `*capacity` — the
consumer computes its mmap size as `8192 + 2 × capacity` — and the fd
is returned. The fd is opened `O_RDWR | O_CLOEXEC` and supports
exactly two operations: `mmap()` and `close()`. [*attach.capacity-and-fd-contract] The fd is installed
before the capacity write-back; if that write faults, the fd is closed
again and the syscall returns `EFAULT`, but another thread of the
process can have observed the fd in the interim. [*attach.writeback-fault-closes-fd]

Repeated attaches to the same CPU are permitted and return a new fd
each time; all fds for one CPU share the same ring — producer
metadata, consumer metadata, and data region — so multiple direct
consumers can drain one buffer concurrently, each keeping its own
read position in its own memory. KMES stores no per-consumer state:
the fd's private data is a reference to the ring, nothing more. When
events arrive and `need_wake` is set, KMES increments that buffer's
futex counter and wakes all waiting threads. [*attach.shared-ring-many-fds]
