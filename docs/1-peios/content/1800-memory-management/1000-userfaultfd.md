---
title: userfaultfd
type: concept
description: userfaultfd on Peios — what it does, why it became a kernel-exploit primitive, and the three-value policy knob that gates its dangerous mode.
related:
  - peios/memory-management/memory-mapping
  - peios/memory-management/kernel-hardening
  - peios/process-security/process-security-descriptors
  - peios/privileges/se-tcb-privilege
---

`userfaultfd()` lets a process register **userspace handlers for page faults**. Instead of the kernel resolving a page fault by looking at backing store, the kernel sends an event to a userspace handler and waits for the handler to provide the page contents. Once the handler responds, the kernel resumes the faulting thread.

This is a **userspace pager**. It enables several legitimate use cases — post-copy live migration, snapshotting, garbage collector compaction — and it created several years of kernel exploits because the wait window can be used to widen race conditions in unrelated kernel code paths.

This page explains the mechanism, the attack pattern, and the Peios policy knob that gates the dangerous mode while preserving the legitimate uses.

## How uffd works

A process sets up uffd as follows:

1. Call `userfaultfd(flags)` to obtain a file descriptor.
2. Call `ioctl(fd, UFFDIO_REGISTER, range)` to associate the fd with an address range. From this point, page faults in that range produce events on the fd instead of being resolved by the kernel.
3. A handler thread reads events from the fd. Each event identifies the faulting address, the faulting thread, and the type of fault (read, write, or write-protect).
4. The handler resolves the fault by issuing one of:
   - `UFFDIO_COPY` — write supplied bytes into the page, then resume the faulting thread.
   - `UFFDIO_ZEROPAGE` — install a zero-filled page, then resume.
   - `UFFDIO_CONTINUE` — for shared mappings, install the existing backing.
   - `UFFDIO_WRITEPROTECT` — flip the write-protect state for write-fault tracking.

Until the handler responds, the faulting thread is blocked. The wait can be arbitrarily long; the kernel imposes no timeout.

The same fd can also receive events for other lifecycle changes — `UFFD_EVENT_FORK`, `UFFD_EVENT_REMAP`, `UFFD_EVENT_REMOVE`, `UFFD_EVENT_UNMAP` — letting the handler track the registered range across address-space modifications. These events are advisory and don't block the kernel.

## Legitimate uses

**Post-copy live migration.** A VM or container is migrated to a new host. Instead of transferring all of its memory before resuming, the destination host resumes the workload immediately, then pulls pages from the source on demand whenever the workload touches an unmapped page. uffd is the mechanism: the destination registers the workload's address space with uffd; faults trigger network requests to the source; arrived pages are installed via `UFFDIO_COPY`.

**Concurrent garbage collection.** Modern GCs (Java's ZGC and Shenandoah, Go's runtime, .NET's coreclr) need to track which pages have been moved during compaction. `UFFDIO_WRITEPROTECT` makes a region write-protected; writes trigger uffd events that the GC handles. This is more efficient than `mprotect`-based tracking because uffd's events deliver per-page granularity with low overhead.

**Snapshotting and time-travel debugging.** Tools like CRIU snapshot a process by registering its address space with uffd, write-protecting everything, and saving the dirty pages on each fault. Replay tools like rr work similarly.

**JIT compilers** that need to fill in code pages on demand sometimes use uffd to lazily compile and install code on first execution.

These are all real, valuable workloads, and most of them only need uffd to handle **userspace** faults — faults that occur because user code touched user memory. Kernel-mode handling, where a kernel function (`copy_from_user`, etc.) hits an unmapped page in a uffd-registered range, is needed only by post-copy migration and similar deep tooling.

## Why uffd is dangerous

The wait window during a kernel-mode fault is the problem.

When a process calls a syscall that touches user memory — `read`, `write`, `recvmsg`, anything with a userspace buffer — the kernel function uses helpers like `copy_from_user` and `copy_to_user` to move data. If the user buffer is in a uffd-registered range, the helper triggers a uffd event and **the kernel function blocks** waiting for the handler to respond. The kernel is now suspended mid-syscall, holding whatever locks and state the function had at that point.

This wait can be made arbitrarily long. The userspace handler can sit on the event indefinitely. While the kernel is suspended, **other threads can execute** — including threads that target the suspended kernel function with carefully-timed operations.

The exploit pattern:

1. Find a kernel bug where there's a race between two operations on user memory: typically a TOCTOU (time-of-check time-of-use) where the kernel reads a value, validates it, and reads it again — and an attacker who modifies the value between the two reads can bypass the check.
2. The native race window is microseconds — a few hundred CPU cycles between check and use. Exploiting it requires winning a race billions of times.
3. Place the user memory in question inside a uffd-registered range.
4. Trigger the syscall. The kernel hits the first read, faults, blocks on the uffd handler. The race window is now "as long as I want" instead of microseconds.
5. While the kernel is blocked, modify other state (or have another thread modify state) that affects the kernel's second read.
6. Signal the uffd handler to resolve. The kernel resumes, performs the second operation under the modified conditions, and the bug is exploited reliably.

This pattern was used in dozens of kernel exploit chains from 2015 to 2020. CVE-2016-3672 (`setuid` race), CVE-2017-1000405 (Dirty COW variant), CVE-2022-0185 (filesystem-context use-after-free), and many others. uffd became the standard "race-window-extender" primitive in public exploit toolkits.

## How Linux responded

Linux hardened uffd in stages.

**Stage 1: privilege gate on the syscall.** A sysctl `vm.unprivileged_userfaultfd` was introduced to require privilege for `userfaultfd()`. Mode `0` requires the privilege; mode `1` allows unprivileged.

**Stage 2: `UFFD_USER_MODE_ONLY` flag.** A new flag for the `userfaultfd()` syscall restricts the resulting fd to handling **userspace-mode** page faults only. Kernel-mode faults bypass uffd entirely and fall through to the normal kernel fault path. With this flag set, the race-widening primitive is closed: kernel functions don't block on uffd, only userspace code does.

**Stage 3: third sysctl mode.** `vm.unprivileged_userfaultfd = 2` allows unprivileged callers, but only if they pass `UFFD_USER_MODE_ONLY`. This recognises that most legitimate uses (GC compaction, snapshotting, JITs) only need userspace-mode handling and can run safely without privilege; only post-copy migration and similar deep tooling need kernel-mode handling, and those run in TCB.

The clever observation: the dangerous mode and the most-common-legitimate-use are different. Separating them is sufficient — you don't need to ban uffd, just restrict the dangerous half.

## The Peios policy

Peios provides a single registry-driven knob with three values, applied via ksyncd:

| Value | Behaviour |
|---|---|
| `disabled` | `userfaultfd()` always fails with `ENOSYS`. uffd is effectively absent from the system. |
| `privileged-only` | `userfaultfd()` requires `SeTcbPrivilege` regardless of flags. |
| `user-mode-only` | `userfaultfd()` succeeds without privilege if and only if `UFFD_USER_MODE_ONLY` is set. Without the flag, the call requires `SeTcbPrivilege`. |

The default is `user-mode-only`. This matches Linux's modern posture: GCs and JITs that pass the flag work transparently; CRIU and post-copy-migration tooling pick up the privilege; the kernel-race-widening primitive is unavailable to unprivileged callers.

There is **no** `unrestricted` value. The policy knob can only tighten — moving from `user-mode-only` to `privileged-only` to `disabled` strictly removes capability. This is intentional: there is no deployment scenario where re-opening the kernel-race-widening primitive is the right answer, and providing a knob to do it would invite misconfiguration.

## Setting the policy

The knob lives in the registry. Writing it requires the appropriate registry-key SD permission, which by default is granted to TCB-tier identities. Changes are applied at next boot, or immediately via ksyncd if the running kernel supports it.

A fortress-mode image may set the policy to `privileged-only` or `disabled` to reduce attack surface further. A development image stays at `user-mode-only` for maximum compatibility with GC- and snapshot-using software.

## Cross-process registration

`UFFDIO_REGISTER` requires the registering process to have authority over the address range. Registering against another process's memory — uncommon but possible via `UFFDIO_API` extensions on a passed fd — requires `PROCESS_VM_WRITE` on the target's process SD plus PIP dominance. Same gate as any other "modify another process's memory state" operation.

Self-registration is unrestricted, subject to the syscall-level gate above.

## Audit signal

When `userfaultfd()` is called **without** `UFFD_USER_MODE_ONLY`, the audit subsystem records the event including the calling process, the privilege held, and the syscall flags. This produces an audit trail of every TCB-tier uffd registration — the high-risk operations are visible and rare enough to monitor; the high-frequency userspace-only operations are not audited individually (they would flood the audit log without security benefit).

## Performance and migration considerations

Userspace-only uffd registration has very small per-fault overhead — a few microseconds per fault for the round-trip to the handler thread. This is acceptable for GC compaction (faults are rare relative to memory accesses) but unacceptable for hot paths.

Kernel-mode uffd handling is significantly more expensive when faults occur because the kernel must serialise on the uffd fd. Post-copy migration tooling typically uses kernel-mode handling for the brief migration window, then unregisters once memory has fully transferred.

## See also

- [Memory mapping](memory-mapping) — the regions uffd registers against.
- [Kernel hardening](kernel-hardening) — the broader picture of kernel-side defence.
- [Process Security Descriptors](../process-security/process-security-descriptors) — the access masks for cross-process registration.
