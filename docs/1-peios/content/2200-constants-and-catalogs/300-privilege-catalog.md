---
title: Privilege catalog
type: reference
description: Every privilege defined in v0.20, with its LUID bit position, category, and one-line effect. Privileges occupy a 64-bit bitmask on each token; this catalog is the bit-by-bit reference.
related:
  - peios/constants-and-catalogs/overview
  - peios/privileges/overview
  - peios/privileges/categories
---

Every privilege has a name and a bit position in the token's 64-bit privilege bitmask. The bit position is the privilege's **LUID**. This page is the catalog — name, LUID bit, category, one-line effect — for every privilege defined in v0.20.

The conceptual model is in [Privileges](~peios/privileges/overview); the categories are in [Privilege categories](~peios/privileges/categories). Use this page for "what's the bit for `SeBackupPrivilege`?" lookups.

## Naming convention

Every privilege name starts with `Se` and ends with `Privilege`. The middle part is descriptive (`SeBackupPrivilege`, `SeChangeNotifyPrivilege`, `SeDebugPrivilege`).

## Category column

Each privilege is one of:

- **AccessCheck** — Modifies access decisions during AccessCheck. May be intent-gated.
- **Kernel standalone** — Gates a specific kernel operation; consulted at the operation's entry point.
- **Application** — Defined for authd/directory consumption; the kernel does not enforce.
- **Reserved** — Defined in the catalog but no v0.20 effect.

Some privileges fall in multiple categories (gate both an AccessCheck path and a kernel-standalone path); marked as both.

## The catalog

Sorted by LUID bit position.

| Bit | Name | Category | Effect |
|---|---|---|---|
| 2 | `SeCreateTokenPrivilege` | Kernel standalone | Allows `kacs_create_token`. Required to mint new tokens. |
| 3 | `SeAssignPrimaryTokenPrivilege` | Kernel standalone | Allows installing a token as another process's primary token via `KACS_IOC_INSTALL`. |
| 4 | `SeLockMemoryPrivilege` | Kernel standalone | Lock pages in physical memory (`mlock`, `mlockall`). |
| 5 | `SeIncreaseQuotaPrivilege` | Kernel standalone | Override resource limits (`setrlimit` increases beyond hard limit). |
| 6 | `SeMachineAccountPrivilege` | Application | Add computer accounts to the domain. authd-interpreted. |
| 7 | `SeTcbPrivilege` | Kernel standalone | Act as part of the TCB. Required for `kacs_create_session`, `kacs_set_caap`, `kacs_set_mount_policy`, and other TCB-only operations. |
| 8 | `SeSecurityPrivilege` | AccessCheck + Kernel | Grants `ACCESS_SYSTEM_SECURITY` (SACL access). Also gates CAP_AUDIT_CONTROL, CAP_AUDIT_READ, CAP_MAC_ADMIN. |
| 9 | `SeTakeOwnershipPrivilege` | AccessCheck | Grants `WRITE_OWNER` on any object regardless of DACL. Subject to MIC and PIP. |
| 10 | `SeLoadDriverPrivilege` | Kernel standalone | Load and unload kernel modules. MUST be stripped from non-peinit tokens via FilterToken. |
| 11 | `SeSystemProfilePrivilege` | Reserved | Folded into `SeProfileSingleProcessPrivilege`. |
| 12 | `SeSystemtimePrivilege` | Kernel standalone | Set the system clock. |
| 13 | `SeProfileSingleProcessPrivilege` | Kernel standalone | Use performance monitoring (`perf_event_open`). |
| 14 | `SeIncreaseBasePriorityPrivilege` | Kernel standalone | Raise scheduling priority; set CPU affinity for other processes. |
| 15 | `SeCreatePagefilePrivilege` | Reserved | Folded into `SeTcbPrivilege`. |
| 16 | `SeCreatePermanentPrivilege` | Reserved | No Linux equivalent. |
| 17 | `SeBackupPrivilege` | AccessCheck (intent-gated) | Grants read-category rights on any object when `BACKUP_INTENT` is set. |
| 18 | `SeRestorePrivilege` | AccessCheck (intent-gated) | Grants write-category rights, ownership-change, and `ACCESS_SYSTEM_SECURITY` on any object when `RESTORE_INTENT` is set. Also bypasses the "new owner must be self or owner-group" rule. |
| 19 | `SeShutdownPrivilege` | Kernel standalone | Local shutdown and reboot. |
| 20 | `SeDebugPrivilege` | Kernel standalone | Bypass process SD checks for cross-process inspection. **Does not** bypass PIP. |
| 21 | `SeAuditPrivilege` | Kernel standalone | Write events to the audit log. |
| 22 | `SeSystemEnvironmentPrivilege` | Reserved | Replaced by SDs on EFI variable files. |
| 23 | `SeChangeNotifyPrivilege` | Kernel standalone | Bypass traverse-checking during path resolution. **Granted to all principals by default.** |
| 24 | `SeRemoteShutdownPrivilege` | Kernel standalone | Shut down from a remote connection. Requires SeShutdown as well. |
| 25 | `SeUndockPrivilege` | Reserved | Server OS; not applicable. |
| 26 | `SeSyncAgentPrivilege` | Application | Read all directory objects regardless of per-object permissions. For AD replication agents. |
| 27 | `SeEnableDelegationPrivilege` | Application | Mark a principal as trusted for delegation. |
| 28 | `SeManageVolumePrivilege` | Reserved | Folded into `SeTcbPrivilege`. |
| 29 | `SeImpersonatePrivilege` | Kernel standalone | Impersonate another principal's identity on a thread. Required by services that handle user requests. |
| 30 | `SeCreateGlobalPrivilege` | Reserved | No per-session object namespaces in Peios. |
| 31 | `SeTrustedCredManAccessPrivilege` | Reserved | Reserved for future secrets infrastructure. |
| 32 | `SeRelabelPrivilege` | AccessCheck + Kernel | Permit setting an object's integrity label above the caller's own. Punches WRITE_OWNER through MIC during relabel. |
| 33 | `SeIncreaseWorkingSetPrivilege` | Reserved | Linux does not gate memory-residency hints. |
| 34 | `SeTimeZonePrivilege` | Reserved | Linux does not gate timezone changes. |
| 35 | `SeCreateSymbolicLinkPrivilege` | Kernel standalone | Create symbolic links. **Granted to all principals by default.** |
| 62 | `SeCreateJobPrivilege` | Reserved | For future job-management feature. |
| 63 | `SeBindPrivilegedPortPrivilege` | Kernel standalone | Bind TCP/UDP ports below 1024. Peios-custom privilege. |

Bit positions 0, 1, and 36–61 are unused / reserved for future privileges.

## Default-grant privileges

Two privileges are present on every token authd issues by default:

| Privilege | Bit | Why default |
|---|---|---|
| `SeChangeNotifyPrivilege` | 23 | Required for traverse-checking; almost every path resolution needs it. |
| `SeCreateSymbolicLinkPrivilege` | 35 | Required by tooling that creates symlinks (build systems, packagers). |

A token can have these stripped (via FilterToken) but the result is operationally limited. Default-grant means "you have it unless something specifically removed it".

## Privilege attribute flags

When a privilege is referenced in a `kacs_priv_entry` (for AdjustPrivileges), the attribute field uses:

| Flag | Value | Meaning |
|---|---|---|
| `SE_PRIVILEGE_ENABLED` | 0x00000002 | Enable this privilege. |
| `SE_PRIVILEGE_REMOVED` | 0x00000004 | Permanently remove this privilege. |
| `KACS_PRIV_RESET_ALL_DEFAULTS` | 0x80000000 | (With luid=0) Reset all privileges to enabled_by_default state. |

The value `0` (no flags) means "disable" — the privilege is left present on the token but not in effect.

## State-tracking bitmasks

Each token carries four 64-bit bitmasks for privileges:

| Mask | Meaning |
|---|---|
| `present` | Which privileges are on the token at all. Bit set → privilege is at least disabled. |
| `enabled` | Which privileges are currently in effect. Subset of `present`. |
| `enabled_by_default` | The initial state at token creation. Used for the reset-to-defaults operation. |
| `used` | Sticky bit set when the privilege has been exercised. Never cleared. |

The bit positions in all four masks are the same — the privilege's LUID bit. A privilege is in some "present + enabled + used" state at any time; the four masks express the orthogonal axes.

## Intent flags

For AccessCheck's `privilege_intent` parameter:

| Flag | Value | Privilege gated |
|---|---|---|
| `BACKUP_INTENT` | 0x01 | Activates `SeBackupPrivilege`. |
| `RESTORE_INTENT` | 0x02 | Activates `SeRestorePrivilege`. |

Without the flag, the corresponding privilege is invisible to AccessCheck — its presence on the token does not affect the access decision for that specific call.

## Catalog growth

The catalog is additive. Future versions may:

- Define new privilege names at bit positions 0, 1, 36–61, or beyond 63 (extending the bitmask).
- Promote reserved entries to defined entries.

Future versions will not:

- Renumber existing privileges.
- Change the meaning of an existing privilege.
- Remove a privilege from the catalog (it would become reserved-and-unused).

Programs that store privilege state by LUID bit will continue to work across versions; programs that enumerate all known privileges should expect new ones to appear.
