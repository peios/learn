---
title: DAC Neutralisation
description: Linux evaluates DAC before any LSM hook fires, so KACS has to neutralise it — the capability switchboard, the compatibility state and the LSM stack.
---

Linux evaluates DAC — UID, GID and mode-bit checks — *before*
consulting LSM hooks. If DAC denies an operation the hook never fires,
and KACS cannot override a DAC denial: LSM hooks are restrictive, able
to further deny what DAC would allow but never to grant what DAC has
refused.

KACS therefore neutralises DAC so the hooks always fire. Every process
receives a set of Linux capabilities that bypass the DAC gates, and
those capabilities are mandatory substrate rather than grants.

## The capability switchboard

Linux's capabilities fall into three categories, and
`security_capable()` is authoritative for all of them — the raw
capability sets on `struct cred` are compatibility-visible state that
answers nothing.

**ALLOW** capabilities exist to override UID-based permission checks
on operations KACS enforces through its own hooks, so DAC never blocks
something KACS will evaluate independently:

| CAP | Name | Rationale |
|---:|---|---|
| 0 | `CAP_CHOWN` | KACS file hooks enforce. |
| 1 | `CAP_DAC_OVERRIDE` | KACS file hooks enforce. |
| 2 | `CAP_DAC_READ_SEARCH` | KACS file hooks enforce. |
| 3 | `CAP_FOWNER` | KACS file hooks enforce. |
| 4 | `CAP_FSETID` | KACS file hooks enforce. |
| 5 | `CAP_KILL` | The `task_kill` hook enforces. |
| 6 | `CAP_SETGID` | Cosmetic under KACS. |
| 7 | `CAP_SETUID` | Cosmetic under KACS. |
| 11 | `CAP_NET_BROADCAST` | Unused in modern kernels. |
| 15 | `CAP_IPC_OWNER` | KACS IPC hooks enforce. |
| 28 | `CAP_LEASE` | KACS file hooks enforce. |
| 10 | `CAP_NET_BIND_SERVICE` | The port's reservation SD decides at `socket_bind`; the Linux privileged-port floor never refuses. |

**PRIVILEGE** capabilities gate operations no other KACS hook covers,
and map to a KACS privilege:

| CAP | Name | Privilege |
|---:|---|---|
| 9 | `CAP_LINUX_IMMUTABLE` | `SeTcbPrivilege` |
| 12 | `CAP_NET_ADMIN` | `SeTcbPrivilege` |
| 13 | `CAP_NET_RAW` | `SeTcbPrivilege` |
| 14 | `CAP_IPC_LOCK` | `SeLockMemoryPrivilege` |
| 16 | `CAP_SYS_MODULE` | `SeLoadDriverPrivilege` |
| 17 | `CAP_SYS_RAWIO` | `SeTcbPrivilege` |
| 18 | `CAP_SYS_CHROOT` | `SeTcbPrivilege` |
| 19 | `CAP_SYS_PTRACE` | `SeDebugPrivilege` |
| 20 | `CAP_SYS_PACCT` | `SeTcbPrivilege` |
| 21 | `CAP_SYS_ADMIN` | `SeTcbPrivilege` (but see the mount note below) |
| 22 | `CAP_SYS_BOOT` | `SeShutdownPrivilege` |
| 23 | `CAP_SYS_NICE` | `SeIncreaseBasePriorityPrivilege` |
| 24 | `CAP_SYS_RESOURCE` | `SeIncreaseQuotaPrivilege` |
| 25 | `CAP_SYS_TIME` | `SeSystemtimePrivilege` |
| 26 | `CAP_SYS_TTY_CONFIG` | `SeTcbPrivilege` |
| 27 | `CAP_MKNOD` | `SeTcbPrivilege` |
| 29 | `CAP_AUDIT_WRITE` | `SeAuditPrivilege` |
| 30 | `CAP_AUDIT_CONTROL` | `SeSecurityPrivilege` |
| 33 | `CAP_MAC_ADMIN` | `SeSecurityPrivilege` |
| 34 | `CAP_SYSLOG` | `SeTcbPrivilege` |
| 35 | `CAP_WAKE_ALARM` | `SeTcbPrivilege` |
| 36 | `CAP_BLOCK_SUSPEND` | `SeTcbPrivilege` |
| 37 | `CAP_AUDIT_READ` | `SeSecurityPrivilege` |
| 38 | `CAP_PERFMON` | `SeSystemProfilePrivilege` **or** `SeProfileSingleProcessPrivilege` **or** `SeLoadDriverPrivilege` |
| 39 | `CAP_BPF` | `SeTcbPrivilege` |
| 40 | `CAP_CHECKPOINT_RESTORE` | `SeTcbPrivilege` |

`CAP_PERFMON` is the one **OR-mapped** entry: the Linux capability
genuinely spans several Peios privilege tiers, and no single privilege
covers everything it gates. The check succeeds if the caller holds any
of the three, and every one it holds is marked used. Per-operation
enforcement then happens at the relevant syscall hook, which checks
the *specific* privilege the *specific* operation needs (§3.7).
OR-mapping stops the capability ceiling manufacturing false denials;
it grants nothing the holder does not already have.

`CAP_SYS_ADMIN` maps to `SeTcbPrivilege` and is **not** OR-mapped, which
would be the obvious way to let administrators mount and is the wrong
one: `CAP_SYS_ADMIN` gates dozens of unrelated operations, so widening
it would hand out far more than mounting.

Mounting is handled outside the capability table instead. `may_mount()`
(`fs/namespace.c`, patched) calls `pkm_kacs_may_manage_volumes()`, which
accepts `SeManageVolumePrivilege` **or** `SeTcbPrivilege`, before falling
back to the ordinary `CAP_SYS_ADMIN` check. Every other `CAP_SYS_ADMIN`
caller still needs the TCB.

It has to be asked there rather than through the `sb_mount` LSM hook:
`may_mount()`'s capability check runs *before* `security_sb_mount()`, so
an LSM is never consulted about a mount the capability check already
refused. A hook can narrow that decision; it cannot widen it.

`CAP_SYS_BOOT` carries an extra condition the table cannot express: a
token whose logon session is of a remote origin — Network,
NetworkCleartext or NewCredentials — additionally requires
`SeRemoteShutdownPrivilege`.

**DENY** capabilities are refused unconditionally, whatever privilege
the caller holds: `CAP_SETPCAP` (8) and `CAP_SETFCAP` (31), because
capabilities are dead under KACS, and `CAP_MAC_OVERRIDE` (32), because
KACS is the active LSM and must not be bypassable.

An unmapped or unknown capability is denied by default. The
switchboard fails closed.

## Compatibility state

Programs may inspect the credential capability sets with `capget()` or
`/proc/<pid>/status`, and may attempt to mutate the non-ALLOW subset
with `capset()` or `prctl()`. None of that is authoritative.

`capget()` and `/proc/<pid>/status` report the ALLOW substrate as
present in the effective, permitted and inheritable sets — reported as
`CapEff`, `CapPrm` and `CapInh`, and additionally `CapBnd`, by the proc
interface. Non-ALLOW bits present in the
credential state may also be reported, but grant no authority.
`CapAmb` reports raw Linux ambient state; the ALLOW substrate does not
depend on ambient capabilities.

The strict invariant is that the ALLOW set is mandatory substrate and
has to survive wherever Linux capability mechanics would otherwise
drop it out from under KACS. `capset()` rejects any request clearing
an ALLOW capability from the effective, permitted or inheritable sets,
and bounding-set drops and ambient manipulation reject anything that
would clear or exclude one. The implementation is slightly stricter
than that: an ambient *raise* of an ALLOW capability is refused too,
not only a clear.

After that validation, `capset()` follows ordinary Linux ambient
behaviour — ambient bits no longer present in both the requested
permitted and inheritable sets may be cleared. Because requests
clearing ALLOW bits from permitted or inheritable are denied outright,
that intersection can never indirectly clear an existing ALLOW ambient
bit.

Direct mutation of non-ALLOW state is therefore compatibility-only. It
may change what `capget()` reports and cannot change the authority
answer for any capability-gated operation.

## Neutralised native paths

Native commoncap helpers that make raw capability-subset decisions
*before* a KACS hook are neutralised where KACS has an authoritative
hook of its own. That covers the subset gates in ptrace access,
`PTRACE_TRACEME`, and `task_setnice`, `task_setscheduler` and
`task_setioprio` — each replaced by an unconditional allow, leaving
the KACS process-descriptor and PIP hooks to decide. Capability checks
that reach `security_capable()` directly stay under the switchboard.

For raw xattr operations the FACS metadata hooks are authoritative, so
the native security-xattr capability prechecks that would run first
are skipped. This does not revive Linux file capabilities: installing
or replacing non-empty `security.capability` data stays denied by the
dead `CAP_SETFCAP` policy, with the single exception of the
KACS-owned StrataFS clone (§3.9.7), and exec-time file-capability
grants remain suppressed. Removing stale metadata goes through the
ordinary `FILE_WRITE_EA` path.

One structural wrinkle: `security_capable()` reaches the KACS
switchboard twice — once through the patched commoncap entry point and
once through the KACS `capable` hook — so a privilege consulted this
way is marked used twice. The authorization answer is unaffected; the
privilege-use accounting double-counts.

## The LSM stack

MAC LSMs — SELinux, AppArmor, SMACK, TOMOYO — and the BPF LSM have to
be disabled. They would independently deny operations from their own
label and policy systems, undermining KACS's claim to be the sole
identity-based authorization mechanism and FACS's to be the sole file
access authority. Non-MAC LSMs are permitted: landlock, lockdown, yama
and integrity make no identity-based access decisions and stack
safely.

The check is made at initialisation and KACS refuses to activate if it
fails — but it is a **build-configuration** test rather than an
inspection of the live LSM stack. It tests whether each conflicting
LSM is enabled in the kernel config, and never parses `CONFIG_LSM` or
enumerates what is actually registered.
