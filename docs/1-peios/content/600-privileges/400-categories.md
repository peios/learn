---
title: Privilege categories
type: concept
description: Privileges fall into four functional categories — kernel-standalone, AccessCheck-influencing, application-level, and reserved. This page covers what each category does and which privileges fall into each one.
related:
  - peios/privileges/overview
  - peios/privileges/lifecycle
  - peios/privileges/intent-gated
  - peios/constants-and-catalogs/overview
---

The privileges in Peios fall into four functional categories. Each category has a different relationship to the kernel and to the access check. Knowing which category a privilege is in tells you what it does, where it fires, and whether to expect it to participate in the DACL walk.

This page is organised around the four categories. The full per-privilege catalog — name, LUID bit, one-line description for every privilege — is in [Constants and catalogs](~peios/constants-and-catalogs/overview).

## The four categories

| Category | What the privileges do | Examples |
|---|---|---|
| **Kernel-standalone** | Gate specific kernel operations directly. Not consulted during the DACL walk. | `SeLoadDriverPrivilege`, `SeSystemtimePrivilege`, `SeCreateTokenPrivilege` |
| **AccessCheck-influencing** | Cause the access check to grant access the DACL alone would not. Consulted at specific points during the access pipeline. | `SeSecurityPrivilege`, `SeTakeOwnershipPrivilege`, `SeBackupPrivilege`, `SeRestorePrivilege`, `SeRelabelPrivilege` |
| **Application-level** | Defined for the directory and authd to interpret. The kernel records them on the token but does not enforce them itself. | `SeSyncAgentPrivilege`, `SeEnableDelegationPrivilege`, `SeMachineAccountPrivilege` |
| **Reserved** | Present in the catalog for ABI parity but not used in v0.20. | `SeCreatePagefilePrivilege`, `SeUndockPrivilege`, `SeTimeZonePrivilege` |

The categorisation is functional, not structural. A token's privilege bitmask does not partition by category; all bits live in the same 64-bit word. The category is a property of how each individual privilege is consumed.

## Kernel-standalone privileges

These are the largest category. A kernel-standalone privilege gates a specific kernel operation: the kernel checks at the entry point whether the caller's effective token has the privilege enabled, and refuses the operation if not. The DACL walk is not involved.

Representative members:

| Privilege | What it gates |
|---|---|
| `SeCreateTokenPrivilege` | `kacs_create_token`. Token minting. Held only by authd and peinit. |
| `SeAssignPrimaryTokenPrivilege` | Installing a token as another process's primary. Used by peinit. |
| `SeImpersonatePrivilege` | Impersonating any user (when not running as the same user). Held by every service that handles user requests. |
| `SeTcbPrivilege` | "Act as part of the TCB" — a catch-all for operations that should only happen in trusted code. Required for `KACS_IOC_LINK_TOKENS`, `kacs_set_caap`, mount-policy changes, and a handful of other system operations. |
| `SeLoadDriverPrivilege` | Loading and unloading kernel modules. Held only by peinit on its primary token; explicitly stripped via FilterToken from every other service. |
| `SeShutdownPrivilege` | Local shutdown and reboot. |
| `SeRemoteShutdownPrivilege` | Shutdown from a remote connection. Requires SeShutdown as well. |
| `SeDebugPrivilege` | Inspecting another process regardless of its SD. Crucially, **does not** bypass PIP dominance — a SeDebug holder can bypass an unrelated process's SD but still cannot cross a PIP boundary. |
| `SeSystemtimePrivilege` | Setting the system clock. |
| `SeIncreaseBasePriorityPrivilege` | Raising another process's scheduling priority or setting its CPU affinity. |
| `SeIncreaseQuotaPrivilege` | Overriding resource limits for a process. |
| `SeLockMemoryPrivilege` | Locking pages in physical memory (`mlock`/`mlockall`). |
| `SeAuditPrivilege` | Writing entries to the audit log. |
| `SeProfileSingleProcessPrivilege` | Using performance monitoring tools (`perf_event_open`). |
| `SeBindPrivilegedPortPrivilege` | Binding to TCP/UDP ports below 1024. A Peios-specific privilege. |
| `SeChangeNotifyPrivilege` | Bypassing traverse checks during path resolution. Granted to every principal by default; rarely the answer to a question. |
| `SeCreateSymbolicLinkPrivilege` | Creating symbolic links. Granted to every principal by default. |

For all of these, the calling pattern is the same: the kernel reads the calling token's privilege bitmask at the entry point of the gated operation; if the privilege is not enabled, the operation fails with the appropriate error.

The privileges in this category are mostly held in narrow ways. The most dangerous of them — SeCreateToken, SeTcb, SeLoadDriver — appear on only a handful of TCB token holders. Most other services hold a small, role-specific subset.

## AccessCheck-influencing privileges

These privileges, when enabled, change what the access check itself decides. They produce grants the DACL alone would not.

| Privilege | What it does |
|---|---|
| `SeSecurityPrivilege` | Grants `ACCESS_SYSTEM_SECURITY` on any object (SACL read/write). Also gates kernel-standalone audit-system operations. |
| `SeTakeOwnershipPrivilege` | Grants `WRITE_OWNER` on any object regardless of the DACL. Subject to MIC and PIP — does not bypass those. |
| `SeBackupPrivilege` | Grants read-category rights on any object when `BACKUP_INTENT` is set. Intent-gated. |
| `SeRestorePrivilege` | Grants write, metadata, and ownership-change rights on any object when `RESTORE_INTENT` is set. Intent-gated. Also bypasses the "new owner must be self or SE_GROUP_OWNER group" restriction. |
| `SeRelabelPrivilege` | Permits setting an object's mandatory integrity label above the caller's own. Also acts as the kernel-standalone gate for `kacs_set_sd` with `LABEL_SECURITY_INFORMATION` set to a higher label. |

These privileges fire at specific points in the access pipeline:

- `SeSecurityPrivilege` is consulted when AccessCheck sees `ACCESS_SYSTEM_SECURITY` in the requested mask.
- `SeBackupPrivilege` and `SeRestorePrivilege` are consulted near the start of AccessCheck, but only if the corresponding intent flag is set in `privilege_intent`. See [Intent-gated privileges](~peios/privileges/intent-gated).
- `SeTakeOwnershipPrivilege` is consulted after the DACL walk: if the walk did not grant `WRITE_OWNER` and the mandatory policy did not block it, the privilege grants it.
- `SeRelabelPrivilege` is consulted by `kacs_set_sd` when the caller is trying to set an integrity label.

When any of these privileges contributes to the final granted mask, the access check records the fact so audit events can attribute the grant correctly. Audit consumers can distinguish "the user got read access because the DACL allowed it" from "the user got read access because they hold SeBackup and asked to use it".

## Application-level privileges

These privileges are defined for authd, the directory, and federation services to interpret. The kernel records them on the token (so authd has somewhere to put them) but does not enforce them itself.

| Privilege | What it does |
|---|---|
| `SeSyncAgentPrivilege` | Lets the holder read all directory objects regardless of per-object permissions. Used by Active Directory replication agents. |
| `SeEnableDelegationPrivilege` | Lets the holder mark a principal as trusted for delegation in the directory. |
| `SeMachineAccountPrivilege` | Lets the holder add computer accounts to the domain. |

From the kernel's point of view, these are token attributes that no kernel path checks. They appear on the token's privilege bitmask; AdjustPrivileges can enable, disable, or remove them like any other privilege; but no AccessCheck path consults them. Their effect happens entirely in user-space services that read the token and act on its privilege bitmask themselves.

The kernel still enforces the present/enabled/removed/used state machine for these privileges as it does for others — AdjustPrivileges treats them identically. The application-level distinction is about *who consumes them*, not how they are stored or transitioned.

## Reserved privileges

A handful of privileges appear in the catalog for binary compatibility with the spec lineage but have no implementation in v0.20:

| Privilege | Why it is reserved |
|---|---|
| `SeCreateGlobalPrivilege` | No per-session object namespaces in Peios. |
| `SeCreatePagefilePrivilege` | Folded into `SeTcbPrivilege`. |
| `SeCreatePermanentPrivilege` | No Linux equivalent. |
| `SeIncreaseWorkingSetPrivilege` | Linux does not gate memory-residency hints. |
| `SeManageVolumePrivilege` | Folded into `SeTcbPrivilege`. |
| `SeTrustedCredManAccessPrivilege` | Reserved for future secrets infrastructure. |
| `SeSystemEnvironmentPrivilege` | Replaced by SDs on EFI variable files under FACS. |
| `SeSystemProfilePrivilege` | Folded into `SeProfileSingleProcessPrivilege`. |
| `SeTimeZonePrivilege` | Linux does not gate timezone changes. |
| `SeUndockPrivilege` | Server OS; not applicable. |

A reserved privilege's LUID position in the bitmask is allocated, but no kernel path consults it. authd will refuse to issue a token containing one of these privileges (the privilege policy validator rejects them at token-creation time). They are placeholders that keep the bitmask layout stable for future use.

## Default-grant privileges

Two privileges deserve a special note: `SeChangeNotifyPrivilege` and `SeCreateSymbolicLinkPrivilege` are **granted to every principal by default**. authd's policy includes both on every token it mints. The reason is that they are needed for almost every program to function normally — without `SeChangeNotifyPrivilege`, a process cannot traverse a directory to reach a file; without `SeCreateSymbolicLinkPrivilege`, a process cannot create the symlinks that build systems and packaging tools depend on.

Their effect is broad-but-uninteresting: every token has them, so any reasoning about access that does not explicitly involve their absence can ignore them. They are mentioned here for completeness; they will rarely be the answer to a question about who can do what.

A token can have these stripped by FilterToken if a sandbox wants to operate without them. Doing so creates a token that cannot traverse arbitrary directories — useful in a tightly confined sandbox, not useful much elsewhere.

## How to find the catalog

The four-category model on this page is the conceptual structure. The byte-level catalog — every privilege name, its LUID bit position, its one-line effect — lives in [Constants and catalogs](~peios/constants-and-catalogs/overview). Cross-reference between the two when you need to look up a specific privilege.

The naming convention is uniform: every privilege starts with `Se` and ends with `Privilege`. The middle is descriptive: `SeLoadDriver`, `SeBackup`, `SeChangeNotify`. There are no privileges outside this convention.
