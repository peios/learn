---
title: Memory Mapping
type: concept
description: How processes shape their address space — mmap, mprotect, madvise, and the protection model. The bread-and-butter calls of Peios memory management.
related:
  - peios/memory-management/understanding-the-address-space
  - peios/memory-management/shared-memory
  - peios/memory-management/memory-protection-keys
  - peios/process-security/process-security-descriptors
---

The kernel doesn't decide where a process's memory comes from. The process does, by issuing **memory-mapping** calls that establish, modify, and tear down regions of its own address space. `mmap()` is the central primitive; almost everything else in this chapter — anonymous allocations, file-backed regions, shared memory, huge pages — is `mmap()` with different flags.

This page covers the mapping syscall family, the protection model, the advice flags that influence the kernel's reclaim and prefetch decisions, and how the cross-process variants are gated.

## The mapping primitives

| Syscall | Purpose |
|---|---|
| `mmap(addr, length, prot, flags, fd, offset)` | Create a new mapping. |
| `munmap(addr, length)` | Remove a mapping. Pages are unmapped immediately; physical pages return to the system. |
| `mremap(old, oldlen, newlen, flags)` | Resize a mapping in place, or move it to a new address. |
| `mprotect(addr, length, prot)` | Change the protection bits on an existing mapping. |
| `pkey_mprotect(addr, length, prot, pkey)` | Like `mprotect`, but also assigns a memory protection key. See [Memory Protection Keys](memory-protection-keys). |
| `remap_file_pages(...)` | Historical primitive for non-linear file mappings. Deprecated; emulated for compatibility but not recommended. |

A process can call any of these on its own memory at will — there is no privilege gate on shaping your own address space, only on what you can put into it (e.g. mapping a file requires read access to that file).

## Protection bits

`prot` is a bitwise OR of:

| Flag | Effect |
|---|---|
| `PROT_READ` | Pages may be read. |
| `PROT_WRITE` | Pages may be written. |
| `PROT_EXEC` | Pages may be executed (instructions fetched). |
| `PROT_NONE` | No access. Useful for guard pages and reservations. |

Removing a protection (e.g. `mprotect(PROT_READ)` on a previously writable region) is always permitted. **Adding `PROT_EXEC`** is the operation worth understanding, because it interacts with the W^X integrity-protection mitigation.

`PROT_EXEC` cannot be added to a mapping that is currently writable, and `PROT_WRITE` cannot be added to a mapping that is currently executable, when the process has W^X active (the default for processes without `PROCESS_MITIGATION_DYNAMIC_CODE_POLICY` allowing it). The intent is to forbid the JIT-style "write code, then execute it" pattern that exploit chains rely on, while permitting the legitimate "load code from a file" pattern (where the file's pages were never writable to the process). Processes that genuinely need to JIT — V8, the JVM, .NET — opt in via the appropriate `prctl` and accept the relaxation.

The full mitigation surface is documented in the Process Security category.

## Mapping flags

`flags` selects between the major mapping kinds. The most common combinations:

| Flag combination | Effect |
|---|---|
| `MAP_PRIVATE` + file fd | Copy-on-write file mapping. Reads see file contents; writes go to a private copy not visible elsewhere. |
| `MAP_SHARED` + file fd | Shared file mapping. Writes are visible to other mappers and eventually written back to the file. |
| `MAP_ANONYMOUS \| MAP_PRIVATE` | Anonymous private mapping. Zero-filled. The default for `malloc` large allocations. |
| `MAP_ANONYMOUS \| MAP_SHARED` | Anonymous shared mapping. Visible across `fork` (parent and child see the same pages). Useful for in-process worker pools. |

Modifier flags adjust placement, allocation policy, and special behaviour:

| Flag | Effect |
|---|---|
| `MAP_FIXED` | Place the mapping at the given address, replacing anything there. Caller is responsible for ensuring it doesn't clobber something important. |
| `MAP_FIXED_NOREPLACE` | Like `MAP_FIXED`, but fail with `EEXIST` if the address is occupied. The safe variant. |
| `MAP_POPULATE` | Pre-fault all pages immediately, defeating demand paging for this mapping. Useful when you know you'll touch every page. |
| `MAP_LOCKED` | Lock the mapping in physical RAM, like `mlock()`. Subject to `SeLockMemoryPrivilege` and quota rules — see [Memory Locking](memory-locking). |
| `MAP_NORESERVE` | Don't reserve swap/commit charge for the mapping. The mapping will fault later if the system can't back it. |
| `MAP_GROWSDOWN` | Stack-style mapping that automatically grows downward. Used internally by the kernel for the main stack; rarely useful in userspace. |
| `MAP_HUGETLB`, `MAP_HUGE_2MB`, `MAP_HUGE_1GB` | Use hugepage-sized pages. See [Huge Pages](huge-pages). |
| `MAP_STACK` | Hint that this mapping will be used as a stack. Currently advisory. |
| `MAP_SYNC` | For DAX persistent-memory mappings, guarantees writes go to persistent storage. |
| `MAP_UNINITIALIZED` | Don't zero pages before returning them. Available only on kernels built for embedded use; rejected on standard images. |
| `MAP_32BIT` | Map in the first 2 GB of address space. Used by some 32-bit-clean code generators. |

The combinations matter. `MAP_ANONYMOUS \| MAP_SHARED` followed by `fork()` is how processes set up shared scratch space without going through `shmget` or filesystem-backed shm. `MAP_PRIVATE` on a file is what dynamic linkers use to load executables. `MAP_FIXED_NOREPLACE` is what allocators use when they want a specific address but won't tolerate clobbering.

## madvise — telling the kernel about access patterns

`madvise(addr, length, advice)` is the process telling the kernel "here's how I plan to use this region; reclaim, prefetch, and merge accordingly." It's a hint, not a command — the kernel may ignore it — but on hot paths the hints make a measurable difference.

The advice values fall into a few groups:

**Reclaim hints** — what to do under memory pressure:

| Advice | Meaning |
|---|---|
| `MADV_DONTNEED` | These pages are dispensable; reclaim them now. The next access faults and zero-fills (anonymous) or refetches (file). |
| `MADV_FREE` | Lazy `MADV_DONTNEED`; the kernel may reclaim under pressure but doesn't have to. The process gets a no-op if memory is plentiful. Cheaper than `MADV_DONTNEED`. |
| `MADV_COLD` | Move pages to the inactive LRU list. Reclaim sooner, but don't force-evict. |
| `MADV_PAGEOUT` | Reclaim or page-out immediately. Heavy hammer for explicit eviction. |

**Prefetch hints** — pull pages in sooner:

| Advice | Meaning |
|---|---|
| `MADV_WILLNEED` | I'll access these pages soon; start populating. Does not block. |
| `MADV_POPULATE_READ` | Synchronously fault all pages for reading. Blocks until done. |
| `MADV_POPULATE_WRITE` | Synchronously fault all pages for writing. Useful for warming up anonymous regions before a hot loop. |

**Pattern hints** — affects readahead behaviour:

| Advice | Meaning |
|---|---|
| `MADV_SEQUENTIAL` | I'll read this region front-to-back. Aggressive readahead. |
| `MADV_RANDOM` | I'll read this region in unpredictable order. Disable readahead. |

**Inheritance hints** — affects fork behaviour:

| Advice | Meaning |
|---|---|
| `MADV_DONTFORK` | Don't include this mapping in children created by `fork()`. |
| `MADV_DOFORK` | Default — children inherit. |

**Core dump hints** — affects what's captured in a crash dump:

| Advice | Meaning |
|---|---|
| `MADV_DONTDUMP` | Exclude this region from core dumps. Used for large caches whose contents would bloat the dump without aiding diagnosis. |
| `MADV_DODUMP` | Default — include in core dumps. |

**Page-merging hints** — see [KSM](ksm) for the full story:

| Advice | Meaning |
|---|---|
| `MADV_MERGEABLE` | Mark this region as eligible for KSM page deduplication. Opt-in to a known cross-process side channel. |
| `MADV_UNMERGEABLE` | Reverse the opt-in; unmerge currently-merged pages. |

**Huge page hints** — see [Huge Pages](huge-pages):

| Advice | Meaning |
|---|---|
| `MADV_HUGEPAGE` | Try to use transparent huge pages for this region. |
| `MADV_NOHUGEPAGE` | Don't use THP here. |
| `MADV_COLLAPSE` | Force-collapse this region into a huge page synchronously. |

The kernel is free to disregard any of these. Reclaim hints in particular are advisory; the kernel may keep pages resident if there's no pressure, or evict pages without being asked when there is.

## Cross-process operations

Three primitives operate on another process's memory:

| Syscall | Effect | Gate |
|---|---|---|
| `process_madvise(pidfd, iov, ...)` | Apply `madvise` advice to another process's memory regions. | `PROCESS_VM_WRITE` on the target's process SD plus PIP dominance. |
| `process_vm_readv(...)` | Read another process's memory into local buffers. | `PROCESS_VM_READ` on the target's process SD plus PIP dominance. |
| `process_vm_writev(...)` | Write to another process's memory from local buffers. | `PROCESS_VM_WRITE` on the target's process SD plus PIP dominance. |

The same gates apply whether the target is a child, a sibling, or an unrelated process. There is no parent-child fast path; the SD governs uniformly.

`process_madvise` is mostly used by container runtimes and supervisors that want to proactively reclaim memory from idle worker processes (`MADV_COLD` / `MADV_PAGEOUT` on another process). The privilege requirement matches the operation's blast radius — influencing another process's memory is non-trivial.

## Reservations and the commit accounting

`mmap()` can succeed without reserving any physical memory: anonymous mappings populate lazily. Whether the **commit charge** (kernel's accounting of total promised memory) is incremented at mmap time depends on the overcommit policy and the `MAP_NORESERVE` flag.

Under default Linux-style overcommit (the Peios default), commit charge is updated only when a page is actually touched. Under strict commit accounting (an image-policy option for high-availability deployments), commit charge is reserved at mmap time and the call fails up front if the system can't promise that memory. See [Overcommit and OOM](overcommit-and-oom) for the full discussion.

`MAP_NORESERVE` opts a specific mapping out of commit accounting regardless of policy — useful for sparse mappings that will only ever touch a small fraction of their range, but with the caveat that touching a page may fault later if the system can't back it.

## Sealing — `mseal`

A process can mark regions as **sealed**, preventing further mapping changes against them. Sealed regions cannot be unmapped, remapped, reprotected, or touched by `madvise(MADV_DONTNEED)`. This is a defensive primitive against bugs and exploits that try to repurpose memory after the application has finished setting it up. See [Memory Sealing](memory-sealing) for the full mechanism.

## See also

- [Understanding the Address Space](understanding-the-address-space) — the layout these calls operate within.
- [Shared Memory](shared-memory) — `MAP_SHARED` patterns and the SHM primitives.
- [Memory Locking](memory-locking) — `MAP_LOCKED` and the privilege model around pinning memory.
- [Huge Pages](huge-pages) — the `MAP_HUGETLB` family.
- [Memory Protection Keys](memory-protection-keys) — `pkey_mprotect`.
- [Memory Sealing](memory-sealing) — `mseal` and the `MAP_SEALABLE` flag.
- [KSM](ksm) — the cross-process deduplication side channel that `MADV_MERGEABLE` opts into.
