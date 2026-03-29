---
title: DAC Neutralization
order: 2
---

Linux evaluates DAC (UID/GID/mode-bit checks) before consulting LSM hooks. If DAC denies an operation, the LSM hook never fires — KACS cannot override a DAC denial. LSM hooks are restrictive: they can further deny what DAC would allow, but cannot grant what DAC has denied.

KACS neutralizes DAC so that LSM hooks always fire. Every process in Peios receives a set of Linux capabilities that bypass DAC gates:

- **CAP_DAC_OVERRIDE** — bypass read, write, and execute permission checks on files.
- **CAP_DAC_READ_SEARCH** — bypass read and search permission checks on directories.
- **CAP_FOWNER** — bypass permission checks requiring the process's fsuid to match the file's owner.
- **CAP_CHOWN** — bypass the restriction that only the file owner can change ownership.
- **CAP_SETUID** / **CAP_SETGID** — allow UID/GID credential changes (cosmetic under KACS).

These capabilities MUST be present on every credential. KACS MUST deny any attempt to clear them (via `capset()`, bounding set drops, or ambient capability manipulation).

## The capability switchboard

Linux's 41 capabilities are classified into three categories:

**ALLOW** — DAC-bypass capabilities. These exist to override UID-based permission checks on operations that KACS enforces via LSM hooks. Allowing them ensures DAC never blocks an operation that KACS will evaluate independently.

**PRIVILEGE** — capabilities that gate operations not covered by other KACS hooks. These are mapped to specific KACS privileges. The `security_capable()` hook checks whether the calling thread's token holds the corresponding privilege. If not, the capability check fails. This is **fail-closed**: an unmapped or unknown capability is denied by default.

**DENY** — capabilities that are dead under KACS or MUST NOT be granted. Denied unconditionally.

### ALLOW — DAC bypass

| CAP | Name | Rationale |
|---|---|---|
| 0 | CAP_CHOWN | KACS file hooks enforce. |
| 1 | CAP_DAC_OVERRIDE | KACS file hooks enforce. |
| 2 | CAP_DAC_READ_SEARCH | KACS file hooks enforce. |
| 3 | CAP_FOWNER | KACS file hooks enforce. |
| 4 | CAP_FSETID | KACS file hooks enforce. |
| 5 | CAP_KILL | KACS task_kill hook enforces. |
| 6 | CAP_SETGID | Cosmetic under KACS. |
| 7 | CAP_SETUID | Cosmetic under KACS. |
| 11 | CAP_NET_BROADCAST | Unused in modern kernels. |
| 15 | CAP_IPC_OWNER | KACS IPC hooks enforce. |
| 28 | CAP_LEASE | KACS file hooks enforce. |

### PRIVILEGE — mapped to KACS privileges

| CAP | Name | KACS privilege |
|---|---|---|
| 9 | CAP_LINUX_IMMUTABLE | SeTcbPrivilege |
| 10 | CAP_NET_BIND_SERVICE | SeBindPrivilegedPortPrivilege |
| 12 | CAP_NET_ADMIN | SeTcbPrivilege |
| 13 | CAP_NET_RAW | SeTcbPrivilege |
| 14 | CAP_IPC_LOCK | SeLockMemoryPrivilege |
| 16 | CAP_SYS_MODULE | SeLoadDriverPrivilege |
| 17 | CAP_SYS_RAWIO | SeTcbPrivilege |
| 18 | CAP_SYS_CHROOT | SeTcbPrivilege |
| 19 | CAP_SYS_PTRACE | SeDebugPrivilege |
| 20 | CAP_SYS_PACCT | SeTcbPrivilege |
| 21 | CAP_SYS_ADMIN | SeTcbPrivilege |
| 22 | CAP_SYS_BOOT | SeShutdownPrivilege |
| 23 | CAP_SYS_NICE | SeIncreaseBasePriorityPrivilege |
| 24 | CAP_SYS_RESOURCE | SeIncreaseQuotaPrivilege |
| 25 | CAP_SYS_TIME | SeSystemtimePrivilege |
| 26 | CAP_SYS_TTY_CONFIG | SeTcbPrivilege |
| 27 | CAP_MKNOD | SeTcbPrivilege |
| 29 | CAP_AUDIT_WRITE | SeAuditPrivilege |
| 30 | CAP_AUDIT_CONTROL | SeSecurityPrivilege |
| 33 | CAP_MAC_ADMIN | SeSecurityPrivilege |
| 34 | CAP_SYSLOG | SeTcbPrivilege |
| 35 | CAP_WAKE_ALARM | SeTcbPrivilege |
| 36 | CAP_BLOCK_SUSPEND | SeTcbPrivilege |
| 37 | CAP_AUDIT_READ | SeSecurityPrivilege |
| 38 | CAP_PERFMON | SeProfileSingleProcessPrivilege |
| 39 | CAP_BPF | SeTcbPrivilege |
| 40 | CAP_CHECKPOINT_RESTORE | SeTcbPrivilege |

### DENY — dead or dangerous

| CAP | Name | Rationale |
|---|---|---|
| 8 | CAP_SETPCAP | Capabilities are dead under KACS. |
| 31 | CAP_SETFCAP | Capabilities are dead under KACS. |
| 32 | CAP_MAC_OVERRIDE | KACS is the active LSM — MUST NOT be bypassable. |

## LSM stack invariant

The supported LSM stack is exactly `commoncap, kacs`. No other LSMs are permitted. SELinux, AppArmor, and BPF LSM MUST be disabled in the kernel config. KACS MUST verify the stack at initialization and refuse to activate if any unexpected LSM is present.

> [!INFORMATIVE]
> Any additional stacked LSM could independently deny operations, undermining KACS's claim as the sole identity-based authorization mechanism and FACS's claim as the sole file access authority.
