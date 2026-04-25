---
title: Privilege Catalog
---

This is the complete set of Peios privileges. Each privilege is listed with a description and its enforcement category:

- **Kernel standalone** — enforced at a specific operation boundary, independent of AccessCheck.
- **AccessCheck** — evaluated inside the AccessCheck pipeline.
- **AccessCheck + kernel standalone** — evaluated inside AccessCheck AND used as a standalone gate for capability mappings or other kernel checks.
- **Application-level** — checked by a userspace service, not by the kernel.
- **Reserved** — allocated for format compatibility but not enforced in v0.20.
- **Kernel standalone (future)** — defined for ABI stability but not enforced in v0.20. Will become kernel standalone when the gated subsystem is implemented.

## Identity and token management

| Privilege | Description | Enforcement |
|---|---|---|
| SeCreateTokenPrivilege | Create tokens from scratch. Only TCB components (authd, peinit). | Kernel standalone |
| SeAssignPrimaryTokenPrivilege | Install a token as another process's primary identity. | Kernel standalone |
| SeImpersonatePrivilege | Impersonate another principal's identity on the current thread. Required by every service that handles requests on behalf of users. | Kernel standalone |

## Access control

| Privilege | Description | Enforcement |
|---|---|---|
| SeSecurityPrivilege | Read and write an object's SACL. Also gates CAP_AUDIT_CONTROL, CAP_MAC_ADMIN, and CAP_AUDIT_READ via capability mapping. | AccessCheck + kernel standalone |
| SeTakeOwnershipPrivilege | Take ownership of any object regardless of current permissions. | AccessCheck |
| SeBackupPrivilege | Read any object regardless of DACL, for backup. Intent-gated: only evaluated when the caller passes BACKUP_INTENT. | AccessCheck |
| SeRestorePrivilege | Write any object, modify permissions, change ownership, access SACL -- everything needed to restore an object. Intent-gated: only evaluated when the caller passes RESTORE_INTENT. | AccessCheck |
| SeRelabelPrivilege | Change an object's integrity label. Punches WRITE_OWNER through MIC for non-dominant callers. Removes the "only at or below own level" restriction at label-write time in kacs_set_sd. | AccessCheck + kernel standalone |
| SeChangeNotifyPrivilege | Bypass traverse checking. Without this privilege, accessing a file requires FILE_TRAVERSE on every intermediate directory. Granted to all principals by default. Implementations SHOULD cache the privilege status as a boolean flag on the token (e.g., `has_traverse_privilege`) and check the flag in the `security_inode_permission` hot path rather than scanning the privilege array on every intermediate directory. This privilege is checked O(depth) times per path resolution. | Kernel standalone |
| SeCreateSymbolicLinkPrivilege | Create symbolic links. Required in addition to FILE_ADD_FILE on the parent directory. Granted to all principals by default. | Kernel standalone |

## System operations

| Privilege | Description | Enforcement |
|---|---|---|
| SeTcbPrivilege | Act as part of the trusted computing base. Catch-all for system operations that do not map to a more specific privilege. Only TCB services need this. | Kernel standalone |
| SeShutdownPrivilege | Shut down or reboot the local system. | Kernel standalone |
| SeRemoteShutdownPrivilege | Shut down the system from a remote connection. When a shutdown request comes from a remote logon type, both SeShutdownPrivilege and SeRemoteShutdownPrivilege are required. | Kernel standalone |
| SeLoadDriverPrivilege | Load or unload kernel modules. MUST be stripped from all non-peinit tokens via FilterToken. | Kernel standalone |
| SeDebugPrivilege | Attach to and inspect any process regardless of its SD. Does not bypass PIP. | Kernel standalone |
| SeSystemtimePrivilege | Change the system clock. | Kernel standalone |
| SeIncreaseBasePriorityPrivilege | Raise process scheduling priority and set CPU affinity for other processes. | Kernel standalone |
| SeIncreaseQuotaPrivilege | Override resource limits (ulimits) for a process. | Kernel standalone |
| SeLockMemoryPrivilege | Lock pages in physical memory (mlock/mlockall). | Kernel standalone |
| SeAuditPrivilege | Write events to the audit log. | Kernel standalone |
| SeProfileSingleProcessPrivilege | Use performance monitoring tools (perf_event_open). | Kernel standalone |
| SeCreateJobPrivilege | Submit supervised jobs via JFS. Custom Peios privilege. Not enforced in v0.20 (JFS is out of scope). Defined for ABI stability. | Kernel standalone (future) |

## Network

| Privilege | Description | Enforcement |
|---|---|---|
| SeBindPrivilegedPortPrivilege | Bind to TCP/UDP ports below 1024. Custom Peios privilege -- retains the Linux convention as defense-in-depth. | Kernel standalone |

## Directory and domain operations

| Privilege | Description | Enforcement |
|---|---|---|
| SeSyncAgentPrivilege | Read all objects in the directory regardless of per-object permissions. For AD replication agents. | Application-level |
| SeEnableDelegationPrivilege | Mark a principal account as trusted for delegation in the directory. | Application-level |
| SeMachineAccountPrivilege | Add computer accounts to the domain. | Application-level |

## Reserved

The following privileges are allocated for format compatibility. The positions exist so that tokens from Active Directory environments can carry these privileges without information loss. They have no enforcement point in v0.20.

| Privilege | Reservation rationale |
|---|---|
| SeCreateGlobalPrivilege | Peios has no per-LogonSession object namespaces. |
| SeCreatePagefilePrivilege | Absorbed in SeTcbPrivilege. |
| SeCreatePermanentPrivilege | No Linux equivalent. |
| SeIncreaseWorkingSetPrivilege | Linux does not gate memory residency hints. |
| SeManageVolumePrivilege | Absorbed in SeTcbPrivilege. |
| SeTrustedCredManAccessPrivilege | Reserved for future secrets infrastructure. |
| SeSystemEnvironmentPrivilege | Gated by SDs on efivar files under FACS. |
| SeSystemProfilePrivilege | Absorbed in SeProfileSingleProcessPrivilege. |
| SeTimeZonePrivilege | Linux does not gate timezone changes. |
| SeUndockPrivilege | Server operating system. |

## Custom privilege allocation

Custom Peios privileges are allocated from the high end of the 64-bit privilege space, while format-compatible privileges occupy their standard Windows LUID positions (bits 2-35). Custom privileges grow downward from bit 63:

| Privilege | Bit position |
|-----------|-------------|
| SeBindPrivilegedPortPrivilege | 63 |
| SeCreateJobPrivilege | 62 |

This avoids collision if new privileges are defined in future AD releases.

## Default-grant privileges

SeChangeNotifyPrivilege and SeCreateSymbolicLinkPrivilege are granted to all principals by default. This is an authd policy decision — authd includes these privileges in every token it creates. They MAY be removed from specific tokens via FilterToken if needed.
