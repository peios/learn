---
title: Privilege Catalogue
description: Every Peios privilege with the bit it occupies in the token's four privilege words, grouped by what it governs.
---

The complete set of Peios privileges, with the bit each occupies in
the token's four 64-bit privilege words. Format-compatible privileges
sit at their standard Windows LUID positions in bits 2–35; custom
Peios privileges are allocated downward from bit 63, so that a
privilege defined by a future AD release cannot collide with one of
ours.

Enforcement classes are: **kernel standalone**, enforced at a specific
operation boundary independently of AccessCheck; **AccessCheck**,
evaluated inside the pipeline; **AccessCheck + standalone**, both;
**application-level**, checked by a userspace service rather than the
kernel; and **reserved**, allocated for format compatibility with no
enforcement point.

## Identity and token management

| Privilege | Bit | Mask | Enforcement |
|---|---:|---|---|
| `SeCreateTokenPrivilege` | 2 | 0x4 | Kernel standalone |
| `SeAssignPrimaryTokenPrivilege` | 3 | 0x8 | Kernel standalone |
| `SeImpersonatePrivilege` | 29 | 0x20000000 | Kernel standalone |

`SeCreateTokenPrivilege` mints tokens from scratch, and only TCB
components — authd and peinit — carry it. `SeImpersonatePrivilege`
lets a service impersonate a principal other than itself, and every
service that handles requests on behalf of users needs it; it is
checked in exactly one place, the impersonation identity gate (§3.5.2).

`SeAssignPrimaryTokenPrivilege` gates installing a token as a
process's primary identity. Installation is **self-directed**:
`KACS_IOC_INSTALL` acts on the calling process and fans out to the
sibling threads of its own thread group. There is no mechanism for
installing a token on a different process (§3.2.3). The kernel also
requires the new token to carry the same user SID and the same
LogonSession as the outgoing one, unless the caller additionally holds
`SeTcbPrivilege`. The privilege is also consulted as a *deny* gate on
the exec and credential projection paths.

## Access control

| Privilege | Bit | Mask | Enforcement |
|---|---:|---|---|
| `SeSecurityPrivilege` | 8 | 0x100 | AccessCheck + standalone |
| `SeTakeOwnershipPrivilege` | 9 | 0x200 | AccessCheck |
| `SeBackupPrivilege` | 17 | 0x20000 | AccessCheck + standalone |
| `SeRestorePrivilege` | 18 | 0x40000 | AccessCheck + standalone |
| `SeRelabelPrivilege` | 32 | 0x1_0000_0000 | AccessCheck + standalone |
| `SeChangeNotifyPrivilege` | 23 | 0x800000 | Kernel standalone |
| `SeCreateSymbolicLinkPrivilege` | 35 | 0x8_0000_0000 | Kernel standalone |

`SeSecurityPrivilege` reads and writes an object's SACL, and also
gates `CAP_AUDIT_CONTROL`, `CAP_MAC_ADMIN` and `CAP_AUDIT_READ`
through the capability mapping, the KMES ring buffer attach, and
supplying a SACL at object creation.

`SeTakeOwnershipPrivilege` takes ownership of any object regardless of
its permissions. It is the only privilege here with no standalone
enforcement point at all — it exists purely inside AccessCheck.

`SeBackupPrivilege` and `SeRestorePrivilege` read and write any object
regardless of the DACL. Inside AccessCheck they are intent-gated
(§3.4.1), but both are also used as plain standalone gates outside it:
restore on the descriptor replacement path when the cache is invalid
and on owner assignment to a SID the subject does not hold, and both
on the registry key backup and restore paths.

`SeRelabelPrivilege` changes an object's integrity label, punching
`WRITE_OWNER` through MIC for non-dominant callers and removing the
at-or-below-own-level restriction when a label is written.

`SeChangeNotifyPrivilege` bypasses traverse checking — without it,
reaching a file requires `FILE_TRAVERSE` on every intermediate
directory. The bypass has one exception the name does not suggest: it
is suppressed when the access carries `MAY_CHDIR`, so an explicit
`chdir` takes a full `FILE_TRAVERSE` check whether or not the caller
holds the privilege. The privilege additionally gates
`open_by_handle_at`, which has nothing to do with traversal. It is
checked once per intermediate directory on every path resolution, and
each check takes the token's mutation lock for a snapshot and then
performs a used-bit update, so the cost is O(depth) locked operations
per path walk.

`SeCreateSymbolicLinkPrivilege` creates symbolic links, and is
required in addition to `FILE_ADD_FILE` on the parent directory.

## System operations

| Privilege | Bit | Mask | Enforcement |
|---|---:|---|---|
| `SeTcbPrivilege` | 7 | 0x80 | Kernel standalone |
| `SeLockMemoryPrivilege` | 4 | 0x10 | Kernel standalone |
| `SeIncreaseQuotaPrivilege` | 5 | 0x20 | Kernel standalone |
| `SeLoadDriverPrivilege` | 10 | 0x400 | Kernel standalone |
| `SeSystemProfilePrivilege` | 11 | 0x800 | Kernel standalone |
| `SeSystemtimePrivilege` | 12 | 0x1000 | Kernel standalone |
| `SeProfileSingleProcessPrivilege` | 13 | 0x2000 | Kernel standalone |
| `SeIncreaseBasePriorityPrivilege` | 14 | 0x4000 | Kernel standalone |
| `SeManageVolumePrivilege` | 28 | 0x10000000 | Kernel standalone |
| `SeShutdownPrivilege` | 19 | 0x80000 | Kernel standalone |
| `SeDebugPrivilege` | 20 | 0x100000 | Kernel standalone |
| `SeAuditPrivilege` | 21 | 0x200000 | Kernel standalone |
| `SeRemoteShutdownPrivilege` | 24 | 0x1000000 | Kernel standalone |

`SeTcbPrivilege` is the catch-all for system operations with no more
specific privilege, and only TCB services need it. It has by far the
widest reach of any privilege: fourteen Linux capability mappings,
several token operations, the mount policy paths, the central access
policy cache, LogonSession creation and destruction, removal of
mandatory resource attribute ACEs during descriptor merge, a KMES rate
limit exemption, the LCS source authentication path, and the upgrade
of a linked-token query from an Identification-level copy to the real
token at full access.

`SeShutdownPrivilege` shuts down or reboots the machine, mapped
through `CAP_SYS_BOOT`. `SeRemoteShutdownPrivilege` is required *in
addition* when the request originates from a Network,
NetworkCleartext, or NewCredentials logon.

`SeLoadDriverPrivilege` loads and unloads kernel modules through
`CAP_SYS_MODULE`. `SeDebugPrivilege` attaches to and inspects any
process regardless of its descriptor, and does not bypass PIP (§3.7).
`SeSystemtimePrivilege` changes the clock,
`SeIncreaseBasePriorityPrivilege` raises scheduling priority and sets
CPU affinity for other processes, `SeIncreaseQuotaPrivilege` overrides
resource limits, `SeLockMemoryPrivilege` locks pages in physical
memory, and `SeAuditPrivilege` writes events to the audit log — it is
what KMES requires for userspace event emission.

`SeProfileSingleProcessPrivilege` attaches `perf_event_open()` to a
specific other process. It respects PIP dominance, and own-task
profiling requires nothing. `SeSystemProfilePrivilege` covers
system-wide profiling — per-CPU events, all-task sampling, kernel-mode
events — and does not respect PIP at the per-sample level, since
system-wide samples include PIP-protected tasks. It is an
operator-class privilege.

Those two and `SeLoadDriverPrivilege` share one mapping: `CAP_PERFMON`
is satisfied by **any** of the three, and every one the caller holds is
marked used. The two profiling privileges are otherwise disjoint
tiers.

## Network

No privilege. Binding a port is an access check against the port's
reservation — a security descriptor keyed by protocol and port range —
not a privilege test; see [Port reservations](~peios/network-objects/port-reservations).
Bit 63 was `SeBindPrivilegedPortPrivilege` until that object existed; the
bit is retired and not reused.

## Directory and domain operations

| Privilege | Bit | Enforcement |
|---|---:|---|
| `SeSyncAgentPrivilege` | 26 | Application-level |
| `SeEnableDelegationPrivilege` | 27 | Application-level |
| `SeMachineAccountPrivilege` | 6 | Application-level |

`SeSyncAgentPrivilege` reads every object in the directory regardless
of per-object permissions, for AD replication agents.
`SeEnableDelegationPrivilege` marks a principal as trusted for
delegation. `SeMachineAccountPrivilege` adds computer accounts to the
domain. None has a kernel definition, which is consistent with their
being application-level — but none has a userspace definition in the
tree either, so at present nothing anywhere enforces them.

## Reserved

Allocated for format compatibility so that tokens from Active
Directory environments carry them without information loss. None is
defined in the kernel and none has an enforcement point.

| Privilege | Bit | Reservation rationale |
|---|---:|---|
| `SeCreatePagefilePrivilege` | 15 | Absorbed into `SeTcbPrivilege`. |
| `SeCreatePermanentPrivilege` | 16 | No Linux equivalent. |
| `SeSystemEnvironmentPrivilege` | 22 | Gated by descriptors on efivar files under FACS. |
| `SeUndockPrivilege` | 25 | Server operating system. |
| `SeCreateGlobalPrivilege` | 30 | Peios has no per-LogonSession object namespaces. |
| `SeTrustedCredManAccessPrivilege` | 31 | Reserved for future secrets infrastructure. |
| `SeIncreaseWorkingSetPrivilege` | 33 | Linux does not gate memory residency hints. |
| `SeTimeZonePrivilege` | 34 | Linux does not gate timezone changes. |

## Unallocated and unnamed bits

`SeCreateJobPrivilege` is allocated bit 62 and is unused: no kernel
definition exists for it and nothing consults it. Submitting a
supervised job is not a privilege at all — it is governed by the file
Security Descriptor on the service manager's jobs socket, checked by
the kernel when a process connects (the Peinit TRM). The bit is
nevertheless included in the boot SYSTEM token's privilege set, which
covers bits 2–35 together with 62 and 63, so the SYSTEM token holds
bit 62 present and enabled with no name attached to it and no gate
that consults it.

Nothing validates a privilege mask against the allocated set. Token
creation checks only that the enabled set is a subset of the present
set, and adjustment accepts any bit index from 0 to 63. Bits 0, 1, and
36–61 — positions the catalogue does not allocate at all — can
therefore be set at creation and disabled or removed afterwards
without error, and are simply inert.

## Default grants

`SeChangeNotifyPrivilege` is granted to every principal, as an authd
policy decision rather than a kernel one: the issuer's floor grants it
to Everyone. `SeCreateSymbolicLinkPrivilege` is **not** granted by
default despite being the other traditional default-grant privilege —
authd deliberately omits it from the floor, and no shipped seed grants
it. Either can be removed from a specific token by FilterToken.
