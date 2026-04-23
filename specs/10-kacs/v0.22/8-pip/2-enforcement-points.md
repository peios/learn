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

`/proc/pid/` exposes process metadata: command line, memory maps, open file descriptors, environment, status, symlinks to the executable and working directory, namespace handles, and more. New kernel versions regularly add entries.

PIP enforcement on `/proc/pid/` uses a **default-deny** model. If the caller does not dominate the target and the target is PIP-protected, access to ALL files and symlinks under `/proc/pid/` MUST be denied. This includes both ptrace-gated entries (mem, maps, fd, environ) and non-ptrace-gated entries (cmdline, status, stat, io, cgroup, exe, cwd, root, ns/*, wchan, stack, syscall, smaps, oom_score, and any others).

Default-deny avoids a blacklist that becomes stale as the kernel adds new `/proc` entries. The only exception is the directory entry itself — the PID remains visible in `/proc` directory listings (`getdents`). The process is visible-but-inaccessible.

> [!INFORMATIVE]
> Full PID invisibility would require filtering `getdents` on `/proc`, which is additional hook coverage beyond the per-file access denial. For v0.22, visible-but-inaccessible is acceptable.

> [!INFORMATIVE]
> `/proc` is not FACS-managed — it is a virtual filesystem with no backing store and no xattrs. PIP enforcement on `/proc` is a direct kernel check, not an AccessCheck evaluation. This is the only place in KACS where access control is enforced without an SD.

## Resource limits (prlimit)

Changing a process's resource limits (`prlimit`) requires PROCESS_SET_INFORMATION on the target's process SD, plus PIP dominance. SeDebugPrivilege bypasses the SD check but not PIP.

## Token open operations

Opening another process's primary token (`kacs_open_process_token`) or a thread's token (`kacs_open_thread_token`) requires PROCESS_QUERY_INFORMATION on the target's process SD, plus PIP dominance. These are process-boundary-crossing operations — reading a process's security identity is as sensitive as reading its memory.

## Performance monitoring (perf_event_open)

`perf_event_open()` targeting a specific process can leak execution timing, branch prediction behavior, cache access patterns, and instruction traces — side-channel information that can reveal cryptographic keys and other secrets. If the caller does not dominate the target and the target is PIP-protected, `perf_event_open()` MUST be denied. This is enforced via the `security_perf_event_open` LSM hook.

## /dev/mem and /dev/kmem

`/dev/mem` provides raw access to physical memory. A process with access to `/dev/mem` could read any process's memory by mapping its physical pages, bypassing all virtual memory protections including PIP.

The primary defense is `CONFIG_STRICT_DEVMEM=y`, which restricts `/dev/mem` to I/O regions only (no RAM access). This is a kernel build configuration requirement. As a secondary defense, FACS SHOULD place a restrictive SD on `/dev/mem` and `/dev/kmem`.
