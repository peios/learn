---
title: Huge Pages
type: concept
description: Huge-page support on Peios — transparent huge pages, hugetlbfs, page sizes, and the admin tunables that control them.
related:
  - peios/memory-management/memory-mapping
  - peios/memory-management/numa
  - peios/memory-management/shared-memory
---

The default page size on x86-64 is 4 KB. A process with a large working set ends up with a lot of pages, and the CPU's TLB (Translation Lookaside Buffer) caches a finite number of address translations — usually a few thousand entries. When the working set exceeds TLB capacity, every memory access risks an MMU page-table walk, which is slow.

**Huge pages** are larger page sizes — 2 MB and 1 GB on x86-64 — that map more memory per TLB entry. A 2 MB page covers what would otherwise need 512 standard pages. Workloads with large coherent working sets (databases, in-memory caches, scientific code) see double-digit performance improvements when their hot data is huge-page-backed.

There are two delivery mechanisms: **transparent huge pages** (THP), where the kernel opportunistically promotes regions, and **hugetlbfs**, where the application explicitly requests huge-page-backed memory. Both are present on Peios; the choice depends on whether you want kernel automation or application control.

## Why huge pages matter

A 4 KB-page system serving a 100 GB working set has 26 million pages. The CPU's TLB holds maybe 1500 entries. The TLB miss rate dominates performance.

The same workload with 2 MB pages has 51,200 pages. Every TLB entry covers 512× more memory. Workloads that previously spent 30% of cycles in TLB-related stalls now spend single digits.

The downside is **internal fragmentation**: if you only need 100 KB of data but allocated a 2 MB huge page for it, you've wasted 1.9 MB. For workloads dominated by many small allocations, regular pages are correct.

## Transparent huge pages

THP lets the kernel decide. Anonymous mappings are eligible for promotion to huge pages whenever the kernel finds a contiguous 2 MB region of physical memory and the mapping is suitably aligned.

Two events drive THP promotion:

1. **Faulting in.** When a process faults a page, the kernel may allocate a 2 MB huge page covering it instead of a 4 KB page, if the surrounding mapping is aligned and free.
2. **`khugepaged`.** A kernel thread scans existing mappings looking for opportunities to collapse 4 KB pages into huge pages. Runs continuously at low priority.

THP modes — settable per-image via the registry, applied at boot:

| Mode | Behaviour |
|---|---|
| `always` | Use THP for every eligible anonymous mapping. Maximum performance benefit; some memory waste from internal fragmentation. |
| `madvise` | Use THP only for regions explicitly marked `MADV_HUGEPAGE`. Conservative; opt-in per region. |
| `never` | Never use THP. Disables `khugepaged`. |

The default on Peios is `madvise`. Workloads that benefit from THP are a known set (PostgreSQL, JVM heaps, Redis, scientific simulations) and they all explicitly call `madvise(MADV_HUGEPAGE)` on their large allocations. Workloads that suffer from THP — anything with sparse access patterns or short-lived allocations — get the default behaviour without surprises.

A separate `defrag` setting controls how aggressively the kernel works to *find* huge pages when one is requested:

| Defrag mode | Behaviour |
|---|---|
| `always` | Block the faulting process while compacting memory to satisfy the request. |
| `defer` | Wake `khugepaged` and `kswapd`, return a normal page; the huge page may show up later. |
| `defer+madvise` | `defer` for non-`MADV_HUGEPAGE` regions, `always` for `MADV_HUGEPAGE` regions. |
| `madvise` | `always` for `MADV_HUGEPAGE` regions, do nothing otherwise. |
| `never` | Don't compact memory to satisfy huge-page requests. |

The default `defer+madvise` is the right balance: workloads that asked for huge pages get them eagerly, workloads that didn't ask are not made to wait.

## madvise hints for THP

A process can express preferences per-region:

| Advice | Effect |
|---|---|
| `MADV_HUGEPAGE` | Try to back this region with huge pages. |
| `MADV_NOHUGEPAGE` | Do not back this region with huge pages. |
| `MADV_COLLAPSE` | Synchronously collapse small pages in this region into huge pages, if possible. Blocks until done. |

The hints survive `fork` and `exec`. A process that has set `MADV_HUGEPAGE` on its main heap can be confident it'll persist into children and through `prctl(PR_SET_MEMORY_MERGE)`-style transitions.

## hugetlbfs — explicit hugepage memory

Some workloads need guarantees, not opportunistic promotion. **hugetlbfs** is a special filesystem that exists solely to back huge-page-mapped memory. Files in hugetlbfs are always hugepage-backed; mapping them gives the application explicit huge-page memory.

The pattern:

1. Mount hugetlbfs (typically at `/dev/hugepages`, with size and pagesize options).
2. Open a file in it: `open("/dev/hugepages/myregion", O_RDWR | O_CREAT)`.
3. Truncate to size: `ftruncate(fd, size)`.
4. Map: `mmap(MAP_SHARED, ..., fd, 0)`.

Or, more commonly, use `MAP_HUGETLB` directly with `mmap`:

```c
mmap(NULL, size, PROT_READ | PROT_WRITE,
     MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB | MAP_HUGE_2MB,
     -1, 0);
```

The `MAP_HUGE_2MB` and `MAP_HUGE_1GB` flags select the hugepage size; without them, the default hugepage size is used.

`memfd_create` also accepts `MFD_HUGETLB` for hugepage-backed shared memory:

```c
int fd = memfd_create("hp", MFD_HUGETLB | MFD_HUGE_2MB);
```

This combines memfd's fd-bearer-authority sharing model with explicit huge-page backing.

## Page sizes on x86-64

x86-64 supports two huge-page sizes natively:

| Size | Use |
|---|---|
| 2 MB | The common case. Most THP and hugetlbfs use 2 MB. |
| 1 GB | "Gigabyte pages" — used by virtual machine hosts for guest memory, by very-large-memory-footprint applications. Allocation must be done at boot time on most systems. |

Mixing sizes within a single mapping is not supported; a mapping is either 4 KB pages, 2 MB pages, or 1 GB pages. THP only uses 2 MB; hugetlbfs can use either.

## The hugepage pool

Unlike THP (which uses pages from the general allocator), hugetlbfs pages come from a dedicated **pool** reserved at boot or after boot. The pool exists because allocating 1 GB of physically-contiguous memory at runtime is hard once the system has been running and memory has fragmented. Reserving early avoids the problem.

Pool size is registry-driven, applied at boot via ksyncd:

| Tunable | Effect |
|---|---|
| `nr_hugepages` | Number of standard-size huge pages to reserve. |
| `nr_hugepages_<size>` | Number of huge pages of a specific size (e.g. `nr_hugepages_1048576kB` for 1 GB pages). |
| `nr_overcommit_hugepages` | Soft cap allowing additional huge pages to be allocated dynamically beyond the reserved pool. Best-effort. |

NUMA-aware allocation: each NUMA node can have its own pool, controlled per-node via `/sys/devices/system/node/node<N>/hugepages/`. Workloads with strong NUMA affinity (databases pinned to a single socket) want their pool sized per-node accordingly.

The pool can be resized at runtime. Shrinking is best-effort — if all pages are in use, the kernel cannot free them and the resize stalls until pages are freed.

## Reservations

When a process maps `MAP_HUGETLB` memory, the kernel reserves the corresponding pages from the pool **at mmap time**, not at first-touch. This is a difference from anonymous mappings: with hugetlb, an mmap of 100 GB succeeds only if the pool currently has 100 GB worth of huge pages available. Demand-paging still applies in the sense that the pages aren't physically zeroed and installed in the page table until first touch, but the pool accounting is reserved at mmap.

This means a workload using hugetlb cannot accidentally over-promise huge pages to itself — `mmap` fails with `ENOMEM` if the reservation can't be made.

## Cgroup integration

The `hugetlb` cgroup controller bounds how much hugetlb memory a cgroup may reserve, per page size. This is part of the cgroup memory model and is documented fully in the **Resource Control** category alongside the rest of cgroup management. From this page's perspective, the cgroup limit is one of several things that can cause an `mmap(MAP_HUGETLB)` to fail.

THP is *not* gated by cgroup hugetlb limits — THP draws from the general allocator and is bounded by overall memory limits, not the hugetlb pool.

## Choosing between THP and hugetlbfs

Use **THP** when:

- The workload benefits from huge pages opportunistically.
- The application doesn't want to manage the hugepage pool.
- The hugepage allocation can fail back to normal pages without breaking correctness.

Use **hugetlbfs** (`MAP_HUGETLB`) when:

- The application needs *guaranteed* huge-page backing for performance correctness.
- 1 GB pages are needed (THP only does 2 MB).
- The workload pins memory and wants reservation accounting up front.
- The workload is a VM host providing huge pages to guests.

In practice: most application code runs with THP and never thinks about it; database storage engines and VM hypervisors use hugetlbfs explicitly.

## See also

- [Memory mapping](memory-mapping) — `MAP_HUGETLB` and the `MAP_HUGE_*` flags.
- [Shared memory](shared-memory) — `MFD_HUGETLB` for hugepage-backed memfds.
- [NUMA support](numa) — per-node hugepage pools.
