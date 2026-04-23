---
title: Enforcement Points
---

PIP process isolation is enforced at kernel hook sites. Each hook reads `pip_type` and `pip_trust` from the caller's PSB and the target's PSB, performs the dominance check, and denies the operation if the caller does not dominate.

## SeDebugPrivilege and process SD interaction

All process-to-process operations perform two checks: (1) an AccessCheck against the target's process SD, and (2) a PIP dominance check. SeDebugPrivilege bypasses only the process SD check — it MUST NOT bypass PIP dominance. This applies uniformly to all enforcement points: ptrace, signal delivery, prlimit, process information query/set, and token open operations.

## ptrace

ptrace grants full control over the target: read/write memory, read/write registers, single-step execution, inject signals, modify execution flow. A single successful ptrace attach is equivalent to full compromise of the target process.

If the caller does not dominate the target, the operation MUST be denied regardless of ptrace mode. SeDebugPrivilege bypasses the process SD check but MUST NOT bypass PIP dominance.

## Process memory access

Direct memory access (`/proc/pid/mem`, `process_vm_readv`, `process_vm_writev`) goes through the same ptrace access check in the kernel. The PIP check in the ptrace hook covers all memory access vectors.

> [!INFORMATIVE]
> This is critical for secret-keeping processes. An HSM daemon's in-memory key material is protected by the kernel refusing to let any non-dominant process read its address space. The secret genuinely cannot leak to a compromised administrator.

## Signal delivery

Signals can disrupt, terminate, or debug a process. If the caller does not dominate the target, signal delivery MUST be denied. PIP dominance is checked uniformly regardless of signal type.

The process SD provides per-signal granularity via three access rights: PROCESS_TERMINATE (lethal signals), PROCESS_SUSPEND_RESUME (stop/continue signals), and PROCESS_SIGNAL (informational signals). See the signal classification table in the process SD specification for the full mapping.

This means lifecycle management of PIP-protected processes (shutdown, restart) MUST go through a process that dominates them — in practice, peinit, which runs at the highest trust level.

## /proc metadata

`/proc/pid/` exposes process metadata: command line, memory maps, open file descriptors, environment, status. Some entries are ptrace-gated (mem, maps, fd, environ) — the PIP ptrace hook covers these automatically.

Several entries are NOT ptrace-gated: `cmdline`, `status`, `stat`, `io`, `cgroup`. For PIP-protected processes, these leak information. PIP MUST enforce visibility on these entries: if the caller does not dominate the target and the target is PIP-protected, access MUST be denied.

> [!INFORMATIVE]
> Denying access prevents reading files within `/proc/pid/` but does not hide the PID from directory listings. The PID and directory name remain visible via `getdents`. Full invisibility would require additional hook coverage. For v0.20, visible-but-inaccessible is acceptable.

> [!INFORMATIVE]
> `/proc` is not FACS-managed — it is a virtual filesystem with no backing store and no xattrs. PIP enforcement on `/proc` is a direct kernel check, not an AccessCheck evaluation. This is the only place in KACS where access control is enforced without an SD.

## Resource limits (prlimit)

Changing a process's resource limits (`prlimit`) requires PROCESS_SET_INFORMATION on the target's process SD, plus PIP dominance. SeDebugPrivilege bypasses the SD check but not PIP.

## Token open operations

Opening another process's primary token (`kacs_open_process_token`) or a thread's token (`kacs_open_thread_token`) requires PROCESS_QUERY_INFORMATION on the target's process SD, plus PIP dominance. These are process-boundary-crossing operations — reading a process's security identity is as sensitive as reading its memory.

## /dev/mem and /dev/kmem

`/dev/mem` provides raw access to physical memory. A process with access to `/dev/mem` could read any process's memory by mapping its physical pages, bypassing all virtual memory protections including PIP.

The primary defense is `CONFIG_STRICT_DEVMEM=y`, which restricts `/dev/mem` to I/O regions only (no RAM access). This is a kernel build configuration requirement. As a secondary defense, FACS SHOULD place a restrictive SD on `/dev/mem` and `/dev/kmem`.
