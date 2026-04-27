---
title: Memory Sealing
type: concept
description: The mseal syscall on Peios — preventing further changes to a memory region as a defence-in-depth primitive against bugs and exploits.
related:
  - peios/memory-management/memory-mapping
  - peios/memory-management/shared-memory
---

`mseal()` lets a process declare that a region of its address space will not change again. Once sealed, the kernel refuses operations that would unmap, remap, reprotect, or otherwise reshape the region — even if the calling process initiated the operation itself. The seal is irreversible for the lifetime of the mapping.

This is a **defence-in-depth** primitive. Its purpose is not to defend against the application's own intentional code; it's to defend against bugs and exploits that try to repurpose memory after the application has finished setting it up. A use-after-free in the application that attempts to `mprotect` a sealed region into something writable will fail; an exploit that tries to `munmap` a sealed code region to install replacement code will fail.

## The seal operation

`mseal(addr, length, flags)` seals the named range. Currently `flags` is reserved and must be `0`.

After sealing, the following operations on any page within the range fail with `EPERM`:

- `mprotect(...)` — protection cannot change.
- `pkey_mprotect(...)` — protection cannot change, including via pkeys.
- `munmap(...)` — the region cannot be unmapped.
- `mmap(MAP_FIXED, ...)` over the region — the region cannot be replaced.
- `mremap(...)` — the region cannot be moved or resized.
- `madvise(MADV_DONTNEED, ...)` — pages cannot be reclaimed (which would zero them on next access).
- `madvise(MADV_FREE, ...)` — same reason.

Operations that don't change the mapping continue to work: reads, writes (subject to the mapping's protection), `madvise(MADV_WILLNEED)`, etc. A sealed read-only region remains readable; a sealed read-write region remains writable.

## Why it's a kernel-side mechanism

A naive defence might be "the application checks before each operation whether the region should still be unchanged." This fails because exploits operate by *bypassing* application logic — the attacker's input causes a bug that calls a kernel function the application never intended to call. The application's checks aren't in the path.

The seal is enforced in the kernel. There is no path from userspace that can defeat it: the syscalls that would change the mapping all check the seal flag and refuse. An exploit targeting the application has no way to "talk past" the kernel's check.

The seal cannot be removed. Once `mseal()` succeeds, the kernel records the seal in the VMA structure permanently. Even calls from the same process cannot unseal — there is no `munseal` syscall. The only way to "remove" the seal is to terminate the process; the seal state is per-VMA and dies with the process.

## What sealing does not protect

Sealing protects the mapping's structure and protection bits. It does not protect the **contents** of the mapped pages. A sealed read-write region can still have its contents modified by writes — the seal doesn't make the mapping read-only. Code that wants the mapping to be both immutable and read-only seals it after `mprotect`-ing it to read-only.

Sealing also does not protect against:

- Other processes with cross-process write access (`process_vm_writev`, `/proc/<pid>/mem`) — those operations target memory contents, not VMA structure, and pass through the standard process SD gate.
- Kernel bugs that bypass VMA checks. A kernel exploit that achieves arbitrary write to the kernel's data structures can clear the seal flag. mseal is a defence in depth, not against kernel-level attackers.

## The MAP_SEALABLE flag

`mmap` accepts a `MAP_SEALABLE` flag indicating that the resulting mapping is eligible for `mseal()`. Mappings created without this flag cannot be sealed; the `mseal()` call returns `EINVAL`.

The intent of the flag is forward-compatibility: future kernel revisions may add additional seal types or impose stricter requirements on sealable mappings. The flag lets applications opt into "I want this mapping to participate in the sealing model" without requiring the kernel to enforce sealability invariants on every mapping.

In practice, applications that use `mseal()` always pass `MAP_SEALABLE` at mmap time. Allocators that wrap `mmap()` typically pass it for any allocation that might later be sealed.

## Use cases

**Sealing the program text.** The dynamic linker maps the executable's `.text` segment read-only-and-executable. Sealing it prevents any subsequent attempt to mark it writable, install a JIT'd replacement, or unmap it — defeating exploit chains that aim to overwrite trusted code.

**Sealing trusted constants.** A process loads a configuration file, parses it into a structure, marks the structure read-only, and seals it. The configuration cannot now be tampered with from any path within the process; even a use-after-free that tried to `mprotect` the structure to write new contents would fail.

**Sealing crypto keys.** A process derives a key, places it in a region, marks the region read-only, and seals. The key contents are then both read-only (mapping protection) and structurally permanent (no remap, no unmap). Combined with `mlock` (no swap-out) and possibly `memfd_secret` (no kernel-direct-map exposure), this is a strong containment posture for long-lived secrets.

**Sealing the stack.** Some hardened runtimes seal the stack mapping itself (not its contents — the stack is necessarily writable) to prevent stack-pivoting exploits that try to `mprotect` the stack to executable.

## Compatibility

`mseal()` is a kernel 6.10+ feature on Linux. Older kernels return `ENOSYS`; applications that want to be portable check the syscall return and fall back to leaving the region un-sealed. This is acceptable defence-in-depth — sealing is additive; nothing breaks if it's not present.

Peios builds with `mseal` available. Application code that depends on sealing should still degrade gracefully when running on older kernels (e.g. a Linux VM exporting an older kernel ABI), since seal-or-no-seal both produce a working application; only the defence-in-depth is reduced.

## See also

- [Memory mapping](memory-mapping) — the operations that sealing forbids.
- [Shared memory](shared-memory) — file sealing (`F_SEAL_*`), the related but distinct mechanism for sealing memfd contents.
- [Memory locking](memory-locking) — `mlock` as the complementary "keep this in RAM" primitive for sealed secrets.
