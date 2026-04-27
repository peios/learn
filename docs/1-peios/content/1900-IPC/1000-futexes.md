---
title: Futexes
type: concept
description: Futexes on Peios — the userspace-fast-path kernel-fallback synchronisation primitive used by every modern threading library.
related:
  - peios/IPC/event-fds
  - peios/process-management/understanding-the-thread-model
  - peios/memory-management/shared-memory
---

A **futex** ("fast userspace mutex") is a synchronisation primitive that lives in userspace memory but can ask the kernel to block waiters when contention occurs. The uncontended fast path is purely userspace — atomic operations on a shared word, no syscalls. Only when contention forces a thread to wait does the kernel get involved.

This design is what makes modern user-space threading libraries work. Every pthread mutex, every Java `synchronized` block, every Go channel-on-mutex, every C++ `std::mutex` ultimately lowers to a futex on Linux. The performance is "free" when uncontended (a few atomic instructions) and degrades gracefully under contention.

Futexes on Peios are substrate-as-is from Linux. The mechanism is identical, the access semantics match, and there is no Peios-specific design here beyond what the substrate provides. This page documents the surface for completeness.

## The basic operations

The `futex` syscall takes a futex word (a 32-bit aligned integer in shared memory) and an operation. The two foundational ops:

| Op | Effect |
|---|---|
| `FUTEX_WAIT` | If the futex word equals the expected value, sleep until woken. Otherwise return `EAGAIN`. |
| `FUTEX_WAKE` | Wake up to N waiters on this futex. |

The atomicity of `FUTEX_WAIT`'s "compare value and sleep" is what makes the protocol race-free. A typical mutex lock:

1. Atomically try to flip the futex word from 0 (unlocked) to 1 (locked-uncontended) in userspace. If successful, lock acquired with no syscall.
2. If contended (already 1), atomically flip to 2 (locked-with-waiters).
3. Issue `FUTEX_WAIT(futex, 2)` — if the value is still 2, sleep; otherwise (lock was just released) return immediately and retry.

Unlock:

1. Atomically flip the futex from 1 → 0 (or 2 → 0 if there were waiters).
2. If there were waiters, issue `FUTEX_WAKE(futex, 1)` to wake one.

The fast path (no contention) is two atomic instructions and zero syscalls. Under contention, one syscall per blocked waiter to sleep and one syscall per wake to revive. This is the lower bound for any synchronisation primitive that can block.

## Extended operations

Beyond `FUTEX_WAIT` and `FUTEX_WAKE`, several variants serve more elaborate patterns:

| Op | Effect |
|---|---|
| `FUTEX_REQUEUE` | Wake N waiters and move M others to a different futex. Used for condition-variable signal-while-holding-mutex patterns. |
| `FUTEX_CMP_REQUEUE` | Conditional requeue — if the value matches expectation, perform the requeue. Race-free version. |
| `FUTEX_WAKE_OP` | Wake N waiters, perform an atomic operation on a second futex, optionally wake M waiters there. Used for paired-condition signalling. |
| `FUTEX_WAIT_BITSET` / `FUTEX_WAKE_BITSET` | Per-waiter bitmask filter. A wake with bitmask `B` only wakes waiters whose bitmask intersects `B`. Used for selective wakeup of waiters on the same address. |

These are infrastructure for higher-level primitives (condition variables, read/write locks, semaphores). Most application code never uses them directly; they're implementation details of pthreads and similar libraries.

## Priority-inheritance futexes

`FUTEX_LOCK_PI`, `FUTEX_UNLOCK_PI`, `FUTEX_TRYLOCK_PI`, `FUTEX_WAIT_REQUEUE_PI`, `FUTEX_CMP_REQUEUE_PI` implement **priority-inheritance** mutexes. The priority-inversion problem: a low-priority thread holds a mutex, a high-priority thread blocks on it, a medium-priority thread runs and prevents the low-priority one from releasing. The high-priority thread is effectively blocked by the medium-priority one — priority inversion.

PI mutexes solve this by temporarily boosting the holding thread's priority to that of the highest-priority waiter, ensuring the holder can run and release the lock. Used by real-time code and by some kernel sync primitives that must guarantee bounded wait times.

PI futexes have stricter requirements than regular futexes — the futex word format is more constrained, and only one waiter may be tracked at a time. The complexity is worth it for real-time correctness; for ordinary applications, regular futexes are simpler and faster.

## Process-private vs shared

`FUTEX_PRIVATE_FLAG` (ORed into the operation) tells the kernel that the futex is used only within a single process. The kernel can then avoid the work of looking up the underlying physical page (since the virtual address is sufficient identifier within one process), saving a few hundred cycles per operation.

Process-shared futexes (no `FUTEX_PRIVATE_FLAG`) live in memory shared between processes — typically `mmap(MAP_SHARED)` regions or System V SHM segments. They work identically, just slightly slower.

Threading libraries default to private futexes for intra-process synchronisation. Cross-process synchronisation primitives (POSIX shared semaphores in shared memory, custom protocols using shared memory) use shared futexes.

## futex_waitv — multi-futex wait

`futex_waitv(waiters[], nr, ...)` (kernel 5.16+) lets a thread wait on multiple futexes simultaneously, returning when any of them is signalled. This is the equivalent of `select`/`poll` but for futexes — a single syscall waits on a batch.

Used by event-loop code that wants to mix futex synchronisation with other condition variables, by transactional memory libraries, and by some recent runtime systems for languages with async/await semantics. Substrate-as-is on Peios.

## Robust futex lists

A robust futex is one that survives the holder's death gracefully. If a thread dies while holding a futex (a normal mutex lock), other waiters are stuck forever — there's no one to release the lock. Robust futexes solve this by registering, with the kernel, a per-thread list of currently-held futexes; when the thread exits, the kernel automatically wakes waiters and marks the futex with a bit indicating "the holder died."

The mechanism:

| Call | Purpose |
|---|---|
| `set_robust_list(head, len)` | Register the calling thread's robust-futex list. |
| `get_robust_list(...)` | Retrieve the list (rarely used). |

`set_robust_list` is unprivileged — it's a per-thread registration with no cross-process effects.

The `CLONE_CHILD_CLEARTID` flag at clone time pairs with this: it lets a thread's exit zero out a memory location and wake futex-waiters on it, providing the "thread has fully exited" notification mechanism that pthread_join uses.

## Access semantics

Futex operations require **read** access to the futex word's memory location for `WAIT` (since the kernel reads the value to compare) and **write** access for the operations that update the value (`WAKE_OP`, `REQUEUE` writes, etc.).

When the futex is in process-private memory, the calling thread is the only one with access — there's no cross-process question. When the futex is in shared memory, access is governed by the SD on the underlying SHM region (POSIX shm, System V SHM, or memfd). A process that can't `mmap` the SHM segment can't operate on a futex inside it; that's the access boundary.

Futexes themselves don't add an additional access-control layer. The mechanism is the SHM SD plus the standard memory-mapping access semantics.

## See also

- [Understanding the thread model](../process-management/understanding-the-thread-model) — threads as the consumers of futex synchronisation.
- [Shared memory](../memory-management/shared-memory) — where shared futexes live.
- [Event-bearing file descriptors](event-fds) — the alternative event-delivery mechanism for fd-based event waits.
