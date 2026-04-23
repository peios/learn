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
| `SeLoadDriverPrivilege` | Grants the ability to load and unload kernel modules. Extremely dangerous — a loaded module has full kernel access. | Disabled |
| `SeShutdownPrivilege` | Grants the ability to shut down or restart the machine. | Disabled |
| `SeSystemtimePrivilege` | Grants the ability to change the system clock. | Disabled |
| `SeTimeZonePrivilege` | Grants the ability to change the system time zone. | Enabled |
| `SeIncreaseBasePriorityPrivilege` | Grants the ability to raise process scheduling priority and set CPU affinity. | Disabled |
| `SeIncreaseQuotaPrivilege` | Grants the ability to override resource limits. | Disabled |
| `SeLockMemoryPrivilege` | Grants the ability to lock pages in physical memory (mlock). Used by databases and real-time applications. | Disabled |
| `SeProfileSingleProcessPrivilege` | Grants the ability to use performance monitoring tools (perf_event_open). | Disabled |
| `SeAuditPrivilege` | Grants the ability to write events to the audit log. | Disabled |
| `SeSystemEnvironmentPrivilege` | Grants the ability to modify firmware environment variables. | Disabled |
| `SeCreateJobPrivilege` | Grants the ability to submit jobs through the Job Forwarding Subsystem. | Disabled |
| `SeBindPrivilegedPortPrivilege` | Grants the ability to bind to ports below 1024. Custom Peios privilege — not present in Windows. | Disabled |

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
