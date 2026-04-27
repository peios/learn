---
title: Understanding the Address Space
type: concept
description: Per-process virtual memory on Peios — what each process sees, how the kernel partitions it, and how introspection through /proc is gated.
related:
  - peios/memory-management/memory-mapping
  - peios/process-management/understanding-process-creation
  - peios/process-security/process-security-descriptors
---

Every process on Peios runs in its own private virtual address space. Pointers from one process are not meaningful in another. The kernel maintains a per-process page table that maps virtual addresses to physical ones, and CPU-level memory protection enforces the boundary on every load and store. This is foundational; everything else in memory management — mappings, protection, sharing, swapping — is layered on top.

This page covers the layout you can rely on, how the kernel populates it, and which `/proc` interfaces let you inspect another process's address space (and what gates them).

## Layout on x86-64

A process's virtual address space is 64-bit, but only a portion of it is canonical. On standard x86-64 (4-level paging), 48 bits are usable, giving 256 TB total — split half-and-half between userspace and kernel:

| Range | Use |
|---|---|
| `0x0000000000000000` – `0x00007FFFFFFFFFFF` | Userspace (128 TB) |
| `0xFFFF800000000000` – `0xFFFFFFFFFFFFFFFF` | Kernel (128 TB) |

The hole between userspace top and kernel bottom is **non-canonical** — addresses in that range are illegal at the CPU level and faulting them produces a general protection fault, not a page fault. This is what makes user/kernel separation cheap to enforce.

On CPUs with **5-level paging** (LA57, available on Ice Lake and later), the usable range expands to 57 bits, giving 128 PB total. The kernel uses this opportunistically for very large processes; userspace defaults to 47-bit layouts unless it explicitly maps above the 56-bit boundary, to avoid breaking software that stuffs metadata into pointer high bits.

A typical userspace layout, low addresses to high:

```
0x0000000000000000  null page (mmap_min_addr forbids mapping here)
0x0000000000400000  program text (.text, read+exec)
                    program data (.data, .bss, read+write)
                    heap (grows up via brk)
                    ...
0x00007F0000000000  mmap region (libraries, anonymous mappings)
                    vDSO and vvar pages
                    stack (grows down)
0x00007FFFFFFFFFFF  userspace top
```

The exact addresses are randomised — see [ASLR](#aslr) below.

## Page tables and demand paging

The kernel maintains a per-process **page table** — a hierarchical structure mapping virtual page numbers to physical page frame numbers (PFNs) plus protection bits (read, write, execute, user/supervisor, etc.). On x86-64 the table has 4 levels (5 with LA57). The CPU's MMU walks the table on every memory access; the TLB caches recent translations.

When the kernel creates a mapping (via `mmap()`, `brk()`, or any other primitive), it doesn't immediately allocate physical pages. The mapping is recorded in the process's VMA (virtual memory area) list, but no PTEs are populated. Only when the process **first touches** a page does the kernel allocate a physical page, copy any required content (zero-fill for anonymous, file content for file-backed), and install the PTE. This is **demand paging**.

The benefit is that allocating a 1 GB region only costs the bookkeeping for the VMA — the actual physical memory is consumed lazily as the program reads or writes pages. This is the basis of Linux's overcommit model (see [Overcommit and OOM](overcommit-and-oom)).

## ASLR

**Address Space Layout Randomization** randomises the base addresses of mapped regions to prevent attackers from hard-coding addresses in exploits. Without ASLR, an attacker who finds a buffer overflow can rely on the stack always being at a known address; with ASLR, the address changes every execution and the attacker must first leak a pointer.

Peios randomises:

- **Stack base** — varies by 8 MB (default).
- **mmap region base** — where dynamically-loaded libraries land, varies by 1 GB.
- **Heap base** — where `brk` starts, varies.
- **vDSO and vvar pages** — varies.
- **Program base** (for PIE binaries — Position-Independent Executables) — randomised on each exec.

Non-PIE binaries have a fixed program base baked in at link time, so they cannot be re-randomised across executions. PIE is the default on Peios; non-PIE binaries are honoured but cannot benefit from program-base ASLR.

The level of randomisation is controlled by a registry-driven sysctl analogue, with three modes mirroring Linux's `/proc/sys/kernel/randomize_va_space`:

| Value | Behaviour |
|---|---|
| `0` | Off — every region at a fixed address |
| `1` | Partial — stack and mmap randomised, heap and program base not |
| `2` | Full — stack, mmap, heap, vDSO, and program base all randomised (default) |

The setting is image-policy: you want full ASLR on production deployments. Lowering it is a debugging convenience, not a security choice — diagnostic images may set it to `0` to make crash dump addresses comparable across runs.

## Stack and the guard gap

The stack grows **downward** — pushing a stack frame decrements the stack pointer, popping it increments. This means stack overflow runs into lower addresses. To detect overflow before it corrupts adjacent mappings, the kernel reserves a **guard gap** below the stack: a region of unmapped pages that triggers a fault if the stack grows into them.

The guard gap default is 256 pages (1 MB on x86-64, configurable via the `stack_guard_gap` boot parameter). This protects against the **stack clash** family of attacks, where carefully-sized stack growth is used to leap over the natural guard region into adjacent heap or mmap mappings.

Stack growth itself is automatic: the kernel maps additional stack pages on demand when the stack pointer references unmapped memory immediately above the current stack base. The growth is bounded by `RLIMIT_STACK`. The `RLIMIT_*` model on Peios is documented in the Resource Control category.

## vDSO

The **vDSO** (virtual Dynamic Shared Object) is a small ELF library mapped into every process by the kernel, containing fast-path implementations of a few syscalls — most notably `gettimeofday()`, `clock_gettime()`, `getcpu()`, and `time()`. Calling into the vDSO does not transition to kernel mode; it executes a few instructions in userspace and returns. The vDSO reads kernel-maintained state from the **vvar** page (also mapped read-only into every process).

The vDSO exists because these syscalls are called millions of times per second by typical workloads (anything that reads a clock) and the cost of a real syscall — entering kernel mode, validating arguments, walking back out — dominates the actual work. The vDSO trades a small kernel-write/userspace-read coherence cost for syscall-free execution.

The legacy **vsyscall** page (a fixed-address region for the same purpose) is supported in emulation mode for compatibility with statically linked binaries from older systems but is not used for new code. It will be removed in a future kernel revision.

## brk and the heap

Process heap growth is controlled by the **program break** — a single pointer marking the high end of the data segment. `brk(addr)` sets it; `sbrk(delta)` adjusts it relative to the current value. Increasing the break extends the heap; decreasing it returns memory to the kernel.

Modern allocators (glibc's ptmalloc, jemalloc, mimalloc, tcmalloc) use `brk` only for small allocations and switch to `mmap()` for larger ones. The historical conflation of "heap" with "brk region" no longer holds; most allocator state lives in mmap regions.

`brk()` failing means the heap can't grow further — usually because of `RLIMIT_DATA`, `RLIMIT_AS`, or because the next address would collide with an existing mapping. Allocators handle this transparently by switching to mmap.

## Address space limits

Each process has soft and hard limits on its total virtual address space, set by `RLIMIT_AS`. Exceeding the limit causes `mmap()` and `brk()` to fail with `ENOMEM` even if physical memory is available.

The `RLIMIT_*` mechanism in general — its inheritance, who can raise it, how cgroup-based limits interact — is covered in the Resource Control category. From this page's perspective, `RLIMIT_AS` is one of several knobs that bound a process's address space.

## /proc memory introspection

The `/proc/<pid>/` directory exposes several interfaces for inspecting another process's memory. Each is gated; this section enumerates them and the gates.

| Path | Content | Access mask required |
|---|---|---|
| `/proc/<pid>/maps` | List of VMAs (start–end, protection, backing file) | `PROCESS_QUERY_LIMITED_INFORMATION` on the target's process SD |
| `/proc/<pid>/smaps`, `smaps_rollup` | Detailed per-VMA statistics (RSS, PSS, swap) | `PROCESS_QUERY_INFORMATION` on the target's process SD |
| `/proc/<pid>/pagemap` | Per-page PFN, swap location, soft-dirty | `PROCESS_QUERY_INFORMATION`; PFN bits zeroed unless caller holds `SeTcbPrivilege` |
| `/proc/<pid>/mem` (read) | Direct memory contents | `PROCESS_VM_READ` |
| `/proc/<pid>/mem` (write) | Direct memory write | `PROCESS_VM_WRITE` |

PIP dominance applies to all of these — a low-PIP caller cannot read or write a higher-PIP target regardless of DACL.

The PFN-zeroing rule on `pagemap` exists to mitigate **Rowhammer**: knowing the physical page frame number lets an attacker target physically-adjacent DRAM rows for bit-flipping. Production processes have no legitimate need for raw PFNs; diagnostic tooling running with `SeTcbPrivilege` does. Substrate-as-is from the Linux model.

For the mechanics of the process SD and its access masks, see [Process Security Descriptors](../process-security/process-security-descriptors). For PIP dominance, see [Process Integrity Protection](../pip/understanding-pip).

## Self-introspection

A process inspecting its own memory through `/proc/self/...` follows the same access-control path as inspecting any other process — the AccessCheck succeeds because the caller's effective token is the process's own primary token, which (by default DACL) has full self-access. There is no special "self" bypass; the model is uniform.

This matters because it means impersonation works correctly: a thread impersonating a less-privileged client and reading `/proc/self/mem` reads the **process's** memory but is gated by what the **client's** token can do, not the process's. If the client's token couldn't read the process's memory directly, it can't read it via `/proc/self/mem` either.

## See also

- [Memory mapping](memory-mapping) — `mmap`, `mprotect`, and the protection model.
- [Overcommit and OOM](overcommit-and-oom) — how demand paging interacts with the OOM killer.
- [Understanding Process Creation](../process-management/understanding-process-creation) — how a fresh address space is built at clone/exec.
- [Process Security Descriptors](../process-security/process-security-descriptors) — the access masks that gate `/proc/<pid>/*`.
