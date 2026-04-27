---
title: Memory Protection Keys
type: concept
description: Memory protection keys on Peios — per-thread, hardware-enforced access control over memory regions, configurable from userspace without syscalls.
related:
  - peios/memory-management/memory-mapping
  - peios/memory-management/memory-sealing
---

**Memory protection keys** (pkeys) are a hardware mechanism that lets a process apply additional access-control bits to memory regions, then change those bits from userspace without a syscall. This is a CPU feature exposed through a small syscall family for setup; once configured, the actual access checks are performed by the CPU on every load and store, and the per-key state lives in a userspace-writable register.

Pkeys are useful when a process wants finer-grained or more frequently-toggled protection than `mprotect` can provide. Toggling a region between read-only and read-write via `mprotect` requires a syscall, a TLB flush, and microsecond-class latency. Toggling via pkeys requires a single instruction — the cost is a few CPU cycles.

## The mechanism

Each memory page can be tagged with a **protection key**, a small integer (4 bits on x86-64, allowing 16 keys numbered 0–15). The key is stored in unused bits of the page table entry.

Each thread has a **PKRU register** (Protection Key Rights for Userspace), 32 bits wide. The PKRU encodes per-key access bits: for each of the 16 keys, two bits indicate "access disabled" and "write disabled" for that key. When the CPU performs a memory access, it consults the page's protection key, looks up the corresponding bits in PKRU, and enforces them in addition to the standard read/write/execute permissions of the page.

The PKRU register is **per-thread** and **userspace-writable**. The `WRPKRU` instruction updates it in a few cycles; no syscall is needed. This is the fast-toggle path that makes pkeys useful — a thread can switch between "key 1 inaccessible" and "key 1 fully accessible" between two memory accesses.

## The syscalls

| Syscall | Purpose |
|---|---|
| `pkey_alloc(flags, access_rights)` | Allocate a key. Returns a key ID (1–15; key 0 is reserved). |
| `pkey_free(pkey)` | Release a key, freeing it for future allocation. |
| `pkey_mprotect(addr, len, prot, pkey)` | Like `mprotect`, but also assigns a protection key to the region. |

The flow:

1. `pkey_alloc(0, 0)` returns a fresh key, e.g. `1`.
2. `pkey_mprotect(addr, size, PROT_READ|PROT_WRITE, 1)` tags the region with key 1 and grants read+write at the mapping level.
3. The thread sets PKRU so that key 1's bits indicate "access disabled" — the region is now inaccessible from this thread, even though the mapping is read-write.
4. To access the region, the thread executes `WRPKRU` to clear key 1's disable bits, performs the access, then `WRPKRU` again to re-disable.

The kernel does not participate in steps 3 and 4. The pkey mechanism is fully under the thread's control once the mapping has been tagged.

## Default access bits at allocation

`pkey_alloc(flags, access_rights)` lets the caller set the **initial** access state for the new key:

| `access_rights` value | Meaning |
|---|---|
| `0` | Full access (no restrictions). |
| `PKEY_DISABLE_ACCESS` | All access disabled (PKRU bits set so reads and writes both fail). |
| `PKEY_DISABLE_WRITE` | Writes disabled, reads allowed. |

The caller-thread's PKRU is updated to reflect the requested initial state. Other threads are unaffected — their PKRU values are independent. A thread that was created before the `pkey_alloc` does not have any state for the new key until it explicitly sets one.

## Per-thread independence

Because PKRU is per-thread, each thread can have a different view of the same memory. Thread A can have key 1 disabled while Thread B has key 1 fully accessible — both threads share the same address space, but key 1 regions appear inaccessible to A and accessible to B at the same instant.

This is a powerful primitive for in-process compartmentalisation. A web browser can place security-sensitive memory (passwords, session tokens) under a key that is normally disabled in worker threads, only re-enabling it briefly in trusted threads that need access. Worker threads compromised by a JavaScript engine bug cannot then read the sensitive memory because their PKRU disables it — even though the memory is in the same address space.

The `WRPKRU` instruction itself is uninterceptable. There is no kernel mediation; the thread cannot be paused or inspected during the toggle. This is the property that makes pkeys faster than `mprotect`, and also the property that makes them inappropriate as a security boundary against threads in the same process — any thread can `WRPKRU` to whatever value it wants. Pkeys are useful for *defending against bugs* (a corrupted thread accidentally accessing the wrong region triggers a fault), not for *defending against deliberate adversaries* sharing the address space.

## Faults and signal delivery

When a thread accesses a region in violation of its PKRU, the CPU raises a fault. The kernel translates this into a `SIGSEGV` with `si_code = SEGV_PKUERR`. The signal handler can inspect `si_addr` (the address that faulted) and `si_pkey` (the protection key associated with the region) to diagnose the violation.

Most software treats a pkey fault the same as any other SEGV: log and crash. Pkey-aware software can recover by adjusting PKRU and retrying — this is the basis of "lazy" protection schemes where access is denied by default and granted on demand within a small critical section.

## The 15-key limit

x86-64 reserves 4 bits in the PTE for the protection key, giving 16 values total. Key 0 is the **default key** — every page that hasn't been tagged with a pkey has key 0, and key 0's PKRU bits are always full-access (the default state for unrelated software). This leaves 15 user-allocatable keys.

Fifteen is enough for most reasonable use cases. A typical compartmentalised application uses one or two keys (one for sensitive data, perhaps one for code-only regions). Software that needs more compartments than fit in pkeys must either use multiple processes (and rely on process-level isolation) or invent a software-managed pseudo-key system on top of pkeys.

## Pkeys and mseal

Pkeys and `mseal` solve different problems. `mseal` prevents the **structural** changes to a mapping (no remap, no munmap, no mprotect change). Pkeys provide a **dynamic** access overlay that the thread can toggle. They compose: a sealed read-write region tagged with pkey 1 is structurally permanent (mseal-protected) and dynamically gated (pkey-PKRU-controlled). The two mechanisms target different attack surfaces and complement each other.

`pkey_mprotect` on a sealed region fails — changing the pkey assignment requires modifying the VMA, which sealing forbids. Tag with the desired pkey before sealing if both mechanisms are wanted.

## Cross-process inheritance

Pkey assignments on a memory region are properties of the **mapping**, so they survive `fork` and are inherited by the child. The child's PKRU is initialised to a copy of the parent's at fork time.

Pkey allocations themselves are per-process — `pkey_alloc` results in a key valid only within the calling process. After `fork`, both parent and child see the same set of allocated keys, but a `pkey_free` in one does not affect the other.

`exec` clears all pkey assignments (the mappings are torn down) and resets PKRU to the default.

## Pkeys are unprivileged

There is no privilege gate on `pkey_alloc`, `pkey_free`, or `pkey_mprotect`. A process is free to compartmentalise its own memory however it wants. Pkeys are a **defensive primitive** for the calling process; using them does not affect the system or other processes, so there is nothing to gate.

## Hardware availability

Pkeys are available on Intel CPUs starting with Skylake (consumer) / Skylake-X (server) and on AMD CPUs starting with Zen 3. The kernel detects support at boot and exposes the syscalls only on systems where the hardware is present. On systems without pkey hardware, the syscalls return `ENOSYS`.

ARM64 has its own equivalent (Memory Tagging Extension and Memory Domain Access Control), with different semantics and a different ABI. Pkey-using code on Peios is x86-64-specific by design.

## See also

- [Memory mapping](memory-mapping) — `pkey_mprotect` as a variant of `mprotect`.
- [Memory sealing](memory-sealing) — combining pkey access control with structural permanence.
