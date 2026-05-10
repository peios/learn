---
title: Privilege Reference
type: how-to
description: Complete catalog of Peios privileges, covering AccessCheck overrides, operation gates, and domain/delegation rights.
---

A complete catalog of privileges on Peios. Each privilege is a system-wide right carried on a token. Privileges are assigned by policy at token creation time.

## Privileges that influence AccessCheck

These privileges can grant access rights that the DACL does not.

| Privilege | What it does | Default state |
|---|---|---|
| `SeBackupPrivilege` | Grants read access to any object regardless of the DACL, when backup intent is declared. Intent-gated — only active during backup operations. | Disabled |
| `SeRestorePrivilege` | Grants write access (plus WRITE_DAC, WRITE_OWNER, and DELETE) to any object regardless of the DACL, when restore intent is declared. Intent-gated. | Disabled |
| `SeTakeOwnershipPrivilege` | Grants WRITE_OWNER on any object — the right to claim ownership. Does not grant read or write access to the object's contents. | Disabled |
| `SeSecurityPrivilege` | Grants ACCESS_SYSTEM_SECURITY — the right to read and modify SACLs (audit rules, integrity labels, trust labels). | Disabled |
| `SeRelabelPrivilege` | Grants the ability to set or change mandatory integrity labels on objects. | Disabled |

## Privileges that gate operations

These privileges control access to system-wide operations that are not tied to a specific object's security descriptor.

| Privilege | What it does | Default state |
|---|---|---|
| `SeTcbPrivilege` | Identifies the process as part of the Trusted Computing Base. Gates a wide range of system operations (mount, namespaces, raw I/O, and others). TCB-only for v1. | Disabled |
| `SeCreateTokenPrivilege` | Grants the ability to create new tokens from scratch. Extremely restricted — typically only the kernel and the authentication service. | Disabled |
| `SeAssignPrimaryTokenPrivilege` | Grants the ability to install a primary token on a process. Typically held by init and the authentication service. | Disabled |
| `SeImpersonatePrivilege` | Grants the ability to impersonate a client's token. Required for services that act on behalf of users. | Disabled |
| `SeDebugPrivilege` | Grants the ability to debug any process regardless of its security descriptor. Still subject to PIP — cannot debug a PIP-protected process without dominance. | Disabled |
| `SeLoadDriverPrivilege` | Grants the ability to load kernel-resident code: kernel modules, kprobes, kretprobes, uprobes, uretprobes, and BPF programs on tracing/LSM/networking attach points. **The most powerful privilege in the system.** Code installed under this privilege runs *as* the kernel, below the access-check layer, and therefore bypasses PIP — no other privilege can do this. Trust accordingly. | Disabled |
| `SeShutdownPrivilege` | Grants the ability to shut down or restart the machine. | Disabled |
| `SeSystemtimePrivilege` | Grants the ability to change the system clock. | Disabled |
| `SeTimeZonePrivilege` | Grants the ability to change the system time zone. | Enabled |
| `SeIncreaseBasePriorityPrivilege` | Grants the ability to raise process scheduling priority and set CPU affinity. | Disabled |
| `SeIncreaseQuotaPrivilege` | Grants the ability to override resource limits. | Disabled |
| `SeLockMemoryPrivilege` | Grants the ability to lock pages in physical memory (mlock). Used by databases and real-time applications. | Disabled |
| `SeProfileSingleProcessPrivilege` | Grants the ability to attach `perf_event_open()` to a *specific other process* (cross-task profiling). PIP-respecting — cannot profile a PIP-protected target without dominance. Own-task profiling does not require this privilege. | Disabled |
| `SeSystemProfilePrivilege` | Grants the ability to use system-wide performance profiling: per-CPU events, all-task sampling, kernel-mode events, and the cross-paranoid-level capabilities of `perf_event_open()`. Does not respect PIP at the per-sample level — system-wide samples include PIP-protected tasks. Operator-class privilege, granted to monitoring services rather than interactive users. | Disabled |
| `SeAuditPrivilege` | Grants the ability to write events to the audit log. | Disabled |
| `SeSystemEnvironmentPrivilege` | Grants the ability to modify firmware environment variables. | Disabled |
| `SeCreateJobPrivilege` | Grants the ability to submit jobs through the Job Forwarding Subsystem. | Disabled |
| `SeBindPrivilegedPortPrivilege` | Grants the ability to bind to ports below 1024. Custom Peios privilege — not present in Windows. | Disabled |
| `SeLoadSchedulerPrivilege` | Grants the ability to load and attach `sched_ext` BPF scheduler programs. Replacing the CPU scheduler is qualitatively different from loading a driver — bugs can deadlock the system. Custom Peios privilege. | Disabled |
| `SeFilterFileSystemPrivilege` | Grants the ability to register fanotify permission events, system-wide fanotify marks (`FAN_MARK_MOUNT` / `FAN_MARK_FILESYSTEM`), `FS_PRE_ACCESS` listeners, and the `FAN_UNLIMITED_*` flags. Fills the niche Windows handles via filesystem filter drivers. Custom Peios privilege. | Disabled |
| `SeManageFileLeasePrivilege` | Grants the ability to acquire file leases (`F_SETLEASE`) on files where the calling principal is not the SD owner. Self-owned leases work without this privilege. Held by the Samba service principal. Custom Peios privilege. | Disabled |

## Privileges typically enabled by default

| Privilege | What it does |
|---|---|
| `SeChangeNotifyPrivilege` | Grants the right to traverse directories without individual traverse access checks. Nearly every operation requires directory traversal, so this privilege is enabled by default on all tokens. |
| `SeTimeZonePrivilege` | Changing the time zone is a low-risk operation, so this is typically enabled by default. |

## Domain and delegation privileges

| Privilege | What it does | Default state |
|---|---|---|
| `SeEnableDelegationPrivilege` | Grants the ability to mark an account as trusted for delegation. Domain administration. | Disabled |
| `SeMachineAccountPrivilege` | Grants the ability to add machines to the domain. | Disabled |
| `SeSyncAgentPrivilege` | Grants the ability to synchronize directory data. | Disabled |
| `SeTrustedCredManAccessPrivilege` | Grants trusted access to the credential manager. | Disabled |
| `SeCreateGlobalPrivilege` | Grants the ability to create global objects. | Disabled |
| `SeCreatePermanentPrivilege` | Grants the ability to create permanent kernel objects. | Disabled |
| `SeUndockPrivilege` | Grants the ability to undock a machine. | Disabled |
