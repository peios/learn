---
title: Memory Locking
type: concept
description: Pinning memory in physical RAM on Peios — the mlock family, SeLockMemoryPrivilege, and the relationship with secret protection.
related:
  - peios/memory-management/swap
  - peios/memory-management/shared-memory
  - peios/privileges/se-lock-memory-privilege
---

A process can ask the kernel to **lock** specific pages in physical RAM. Locked pages are exempt from the kernel's normal reclaim and swap mechanisms — they will not be swapped out, will not be evicted from the working set, and will not be reclaimed under memory pressure. They stay in physical memory until the process exits or explicitly unlocks them.

This is useful for two distinct reasons. First, **secrets** — cryptographic keys, authentication tokens, decrypted content — should not be written to swap, where they would persist on disk after the process dies. Second, **latency-sensitive code** — real-time threads, low-latency network servers, audio processing — cannot tolerate the unbounded latency of a page fault, so the working set is locked to eliminate swap-induced stalls.

Pinning memory has a cost. Locked pages cannot be reclaimed by the kernel, so a process that locks too much can starve the rest of the system. Peios bounds this with a privilege gate.

## The locking syscalls

| Syscall | Effect |
|---|---|
| `mlock(addr, len)` | Lock the pages overlapping the range. Returns success only after all pages are present in RAM. |
| `mlock2(addr, len, flags)` | Like `mlock`, with flag bits. |
| `munlock(addr, len)` | Unlock pages. They become eligible for reclaim/swap again. |
| `mlockall(flags)` | Lock all currently mapped pages (`MCL_CURRENT`), or all future pages (`MCL_FUTURE`), or both. |
| `munlockall()` | Unlock everything currently locked by the calling process. |

`mlock` and `mlock2` produce the same observable effect for a given range. The flag bits on `mlock2`:

| Flag | Effect |
|---|---|
| `MLOCK_ONFAULT` | Lock pages only on first access (fault), rather than synchronously paging them in. Useful for sparse mappings where you don't want to pay for un-accessed pages. |

`mlockall` flags:

| Flag | Effect |
|---|---|
| `MCL_CURRENT` | Lock all currently mapped pages. |
| `MCL_FUTURE` | Lock pages mapped in the future (any subsequent `mmap` is implicitly `MAP_LOCKED`). |
| `MCL_ONFAULT` | Lock pages on fault rather than synchronously. |

`MAP_LOCKED` on `mmap()` is a third path: the mapping is locked at creation time without a separate `mlock` call.

## SeLockMemoryPrivilege and the quota

Locking memory above a certain threshold requires **`SeLockMemoryPrivilege`**. Below the threshold, locking is unprivileged — any process can pin a small amount of memory for legitimate secret-protection without needing privilege.

The threshold is a **quota**, not a hard cap. The full quota model — how the limit is set, whether it's per-process or per-cgroup or both, how it interacts with cgroup memory limits, how administrators raise or lower it — is documented in the **Resource Control** category. From this page's perspective, the relevant facts are:

- A small default quota exists (sufficient for typical secret-pinning — a few keys, a few hundred kilobytes worth) and applies to every process by default.
- Without `SeLockMemoryPrivilege`, the calling process is bounded by the quota; `mlock` calls that would exceed it fail with `EAGAIN`.
- With `SeLockMemoryPrivilege`, the quota does not apply; the only bound is total system memory.

The privilege gate exists because unbounded memory locking is a denial-of-service vector. A misbehaving or compromised process that locks all available RAM can starve the kernel itself, causing system-wide thrashing or hard hangs.

## Why crypto libraries don't need the privilege

The default quota is sized to accommodate the legitimate use case of pinning small secrets — TLS session keys, password hashes, authentication tokens, decrypted credential material. These are kilobytes per process at most. Crypto libraries (libsodium, OpenSSL's secure-heap, GPG's `mlock`-backed allocators) call `mlock` on key buffers as a matter of course; they all fit within the default quota and require no privilege.

A workload that needs to lock megabytes — a real-time processing pipeline, a database holding pinned indexes, a low-latency network server with a large connection table — does require the privilege. These are operationally distinct from "I just want to keep my keys out of swap" and the privilege requirement matches the operational scope.

## Lifetime and inheritance

Locks are properties of the **virtual mapping**, not the underlying file or the calling process per se. A locked anonymous mapping unlocks automatically when the mapping is unmapped (via `munmap`, by `exec()`, or by process exit). A locked file mapping unlocks similarly.

`fork()` produces a child whose mappings inherit the lock state — locked regions in the parent are locked in the child too, and counted against the child's quota. `exec()` clears all locks (the mappings themselves are torn down), so a freshly-exec'd process starts with no locked memory.

`MCL_FUTURE` is a per-process attribute, not a per-mapping one; it persists across `mmap` calls until cleared via `munlockall`. It does not survive `exec`.

## Locks and shared mappings

A shared mapping (`MAP_SHARED`) locked by one process is locked **for that process's view**. Other processes mapping the same underlying file each have their own lock state. A page is physically locked in RAM as long as any process has the page locked — the kernel reference-counts. When the last process unlocks (or unmaps), the page becomes reclaimable again.

This means two processes mapping the same file can have different lock states, both of which count against their respective quotas. Locking a shared mapping does not "lock for everyone."

## Relationship with secrets

Memory locking is one piece of a larger pattern for handling secrets:

| Concern | Mechanism |
|---|---|
| Secret should not be written to swap | `mlock` or `MAP_LOCKED` |
| Secret should not be visible via kernel direct map | `memfd_secret` |
| Secret should not be visible to other processes' `process_vm_readv` | Process SD (default DACL denies cross-process read) |
| Secret should be unmappable/unprotected after setup | `mseal` |
| Secret should not appear in core dumps | `madvise(MADV_DONTDUMP)` |

A fully hardened secret region uses several of these in combination: a `memfd_secret` mapping, locked via `MAP_LOCKED`, written once, sealed via `mseal`, marked `MADV_DONTDUMP`. Each defence is independent of the others; together they reduce exposure across multiple categories of bug.

## RLIMIT_MEMLOCK compatibility

Linux exposes a per-process `RLIMIT_MEMLOCK` rlimit that bounds locked memory; on Linux without `CAP_IPC_LOCK`, this rlimit applies, and with `CAP_IPC_LOCK` it is bypassed. Peios honours the `RLIMIT_MEMLOCK` ABI for compatibility — software that calls `setrlimit(RLIMIT_MEMLOCK, ...)` and expects the kernel to enforce it gets the expected behaviour. The Peios quota model is documented separately in the Resource Control category and may not be a single per-process rlimit; the Linux ABI is exposed as a compatibility surface that maps onto whatever the underlying quota mechanism is.

## See also

- [Swap](swap) — what locked memory is exempt from.
- [Shared memory](shared-memory) — `memfd_secret` and the larger secret-handling pattern.
- [Memory sealing](memory-sealing) — `mseal` for structural immutability of locked secrets.
