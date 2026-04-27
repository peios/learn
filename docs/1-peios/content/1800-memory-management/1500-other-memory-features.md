---
title: Other Memory Features
type: reference
description: Smaller memory-management features on Peios — process_mrelease, DAMON, mmap_min_addr, max_map_count, MAP_32BIT, stack clash protection, MAP_UNINITIALIZED.
related:
  - peios/memory-management/memory-mapping
  - peios/memory-management/overcommit-and-oom
  - peios/process-management/process-lifecycle
---

A handful of memory-management features don't fit cleanly into the larger topic pages. They're collected here for reference.

## process_mrelease — expedite memory release

When a process is killed (`SIGKILL`, OOM, etc.), its memory is released asynchronously by the OOM reaper or the normal exit path. For most workloads this is fast enough; for a system under acute memory pressure waiting on a specific dying process to release its pages, the asynchronous release may not be fast enough.

`process_mrelease(pidfd, flags)` lets the caller force-release a dying process's memory **synchronously**. The call returns once the named process's pages are released. The target must already be in the dying state (post-`SIGKILL`) — `process_mrelease` does not kill anything itself.

| Use case | Why |
|---|---|
| User-space OOM-killer daemons | After issuing the kill, force-release immediately so the freed pages are available before the kernel's reaper gets to them. |
| Container supervisors during pod eviction | Speed up the eviction-to-resources-available transition. |
| Memory pressure resolvers | Same idea — once the target is being killed, get its pages back as fast as possible. |

The call is gated on the target's process SD. The caller needs `PROCESS_SET_QUOTA` (or equivalent) plus PIP dominance — the same sort of gate that applies to other "influence the target's resource state" operations. Self-targeting (`pidfd` referring to the calling process) is rejected; the caller must already be dying.

## DAMON — data access monitor

**DAMON** (Data Access MONitor) is a kernel facility that monitors memory access patterns of running processes and exposes them through a kernel API. It works by sampling: a small number of pages are watched, their access patterns recorded, and conclusions extrapolated to the rest of the address space. The CPU overhead is bounded (configurable, typically below 1%) and the granularity is coarse, but the result is a reasonable picture of a process's hot and cold regions.

DAMON has two relevant interfaces:

| Interface | Purpose |
|---|---|
| Read-only access pattern reporting | Tells you which regions of which processes are hot/warm/cold. |
| DAMON-based reclaim and proactive LRU management | Drives reclaim decisions based on the DAMON-observed patterns rather than the kernel's standard LRU heuristics. |

The reporting side is observability: a diagnostic tool reads access pattern data via the DAMON API or sysfs interface. Reading another process's DAMON data is gated by the same access masks as `/proc/<pid>/smaps` — `PROCESS_QUERY_INFORMATION` on the target's process SD.

The control side is administrative: a TCB-tier daemon configures DAMON to drive the kernel's reclaim policy. Configuration uses the registry surface (registry-driven via ksyncd), gated on the relevant key SDs.

DAMON is opt-in per workload — by default, the kernel does not run DAMON monitoring. Enabling it for a specific workload or system-wide is a deliberate admin choice.

## mmap_min_addr

`/proc/sys/vm/mmap_min_addr` sets the lowest virtual address at which a process can `mmap`. The default is page-size-aligned and small (typically 65536 bytes on x86-64). Mappings below this address fail with `EPERM`.

The point is to defeat **null-pointer-dereference** kernel exploits. Many kernel bugs follow the pattern: kernel function dereferences a pointer that was supposed to point at user-supplied data, but due to a bug the pointer is `NULL` (or near-`NULL`). On a system where userspace has mapped page 0, the dereference reads attacker-controlled data instead of crashing, and the bug becomes a controlled-write primitive. On a system with `mmap_min_addr` enforced, page 0 cannot be mapped by unprivileged userspace, so the dereference faults instead.

`mmap_min_addr` is registry-driven via ksyncd. The default value is conservative; lowering it requires admin authority on the registry key and is rarely a good idea outside specialised debugging.

A privileged caller can `mmap` below the limit if it holds `SeTcbPrivilege` (the inheritor of `CAP_SYS_RAWIO` for this purpose) — diagnostic tools occasionally need to map at low addresses to inspect specific kernel constructs.

## max_map_count

`/proc/sys/vm/max_map_count` caps the number of distinct VMAs a process can have. Default is 65530.

Each `mmap` (and each fragmentation event from `mprotect`-ing a sub-range) creates or splits a VMA. A process that does enough independent small mappings can hit the limit and have subsequent `mmap` calls fail with `ENOMEM`.

The cap exists because the kernel's per-process VMA list is walked linearly for some operations; uncapped, a malicious process could create millions of VMAs and consume kernel memory or slow operations.

For most workloads the default is generous. The limit is occasionally raised for memory-mapped database engines, scientific software with many small datasets, and certain garbage collectors that map many small spans. It's an admin sysctl, registry-driven via ksyncd; raising it is harmless if the workload genuinely needs more VMAs.

## MAP_32BIT

`mmap` with `MAP_32BIT` requests an address in the lowest 2 GB of the address space. Used by some 32-bit-clean code generators and by software that stuffs metadata into the high bits of pointers and needs the low bits to be unique.

The flag is x86-64-specific. On other architectures it may be ignored or rejected. On Peios it works as expected on x86-64 and is inert elsewhere. There are no security implications — the request is a placement hint, not a privilege.

## Stack clash protection

A **stack clash** is a class of attack where carefully-sized stack growth is used to leap over the natural guard region (between the stack and adjacent mappings) and land in another mapping, where the attacker can read or write data they shouldn't. The classic example: a function with a large local array forces stack growth past the guard pages into a heap region holding sensitive data.

The kernel mitigates this by making the guard gap large (`stack_guard_gap` boot parameter, default 256 pages) and by enforcing it with hard bounds. Compilers contribute by emitting **stack probes** — small writes to each page of a large stack frame as it's allocated, ensuring that the kernel sees the access pattern and refuses to let the stack grow into another mapping.

The Peios userspace toolchain enables stack probes by default (`-fstack-clash-protection` on GCC/clang). The kernel's stack-guard-gap enforcement is unconditionally on. Both contribute to the broader hardening picture; neither is user-controllable.

## MAP_UNINITIALIZED

`MAP_UNINITIALIZED` is a request to skip zero-filling the pages backing a new mapping. Faster than the default zeroed mapping, at the cost of the application potentially seeing whatever data was previously in the physical page — typically belonging to some other process that recently freed it.

This flag is a privacy disaster on any general-purpose system. It is **rejected** on the default Peios kernel; passing it returns `EINVAL`. It is supported only on kernels built explicitly for embedded use cases where the entire system runs trusted code with no privacy boundaries.

The flag exists because zero-fill costs measurable cycles on memory allocators that are very hot (game engines, signal-processing pipelines) and embedded systems sometimes run hardware where the zero-fill latency matters more than the privacy implication. Substrate-as-is on the Linux model: present in the ABI for compatibility, refused on hardened images.

## remap_file_pages

`remap_file_pages(...)` is a historical syscall for creating non-linear file mappings — different parts of a single mapping pointing at different file offsets. It was deprecated in 2014; the kernel emulates it by issuing equivalent `mmap` calls under the hood.

Modern code should use multiple `mmap` calls instead. `remap_file_pages` remains in the ABI for compatibility with very old software but produces no benefit over the equivalent `mmap` sequence and may eventually be removed entirely.

## See also

- [Memory mapping](memory-mapping) — the primary mapping syscalls these features supplement.
- [Overcommit and OOM](overcommit-and-oom) — the OOM model that `process_mrelease` accelerates.
- [Process lifecycle](../process-management/process-lifecycle) — process death and resource release.
