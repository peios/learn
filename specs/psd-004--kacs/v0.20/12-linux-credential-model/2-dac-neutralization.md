---
title: DAC Neutralization
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

**PRIVILEGE** — capabilities that gate operations not covered by other KACS hooks. Most are mapped to a single KACS privilege. A small number — capabilities that genuinely span multiple Peios privilege tiers, where no single privilege covers all the operations the Linux capability gates — use **OR-mapping**: `security_capable()` succeeds if the caller holds *any* of the listed privileges. The actual per-operation enforcement happens at the relevant syscall hook (e.g. `perf_event_open`, `security_bpf`), which checks the *specific* privilege required for the *specific* operation. OR-mapping prevents the cap_capable ceiling from creating false denials when a Linux capability spans multiple Peios privileges; it does not grant any authority that the holder does not already have via the listed privileges.

If none of the listed privileges are held, the capability check fails. This is **fail-closed**: an unmapped or unknown capability is denied by default.

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
| 38 | CAP_PERFMON | SeSystemProfilePrivilege OR SeProfileSingleProcessPrivilege OR SeLoadDriverPrivilege |
| 39 | CAP_BPF | SeTcbPrivilege |
| 40 | CAP_CHECKPOINT_RESTORE | SeTcbPrivilege |

### DENY — dead or dangerous

| CAP | Name | Rationale |
|---|---|---|
| 8 | CAP_SETPCAP | Capabilities are dead under KACS. |
| 31 | CAP_SETFCAP | Capabilities are dead under KACS. |
| 32 | CAP_MAC_OVERRIDE | KACS is the active LSM — MUST NOT be bypassable. |

## Credential-set state

The Linux capability sets on `struct cred` remain compatibility-visible state.
Programs MAY inspect them with `capget()` or `/proc/<pid>/status` and MAY
attempt to mutate the non-ALLOW subset with `capset()` or `prctl()`. This
state is not authoritative for privilege-bearing operations:
`security_capable()` is authoritative and MUST answer from the capability
switchboard above.

`capget()` MUST report the mandatory ALLOW capability substrate as present in
the effective, permitted, and inheritable result sets. Non-ALLOW bits remain
compatibility-visible state: if a non-ALLOW bit is present in the Linux
credential state, `capget()` MAY report it, but that bit does not grant
authority.

`/proc/<pid>/status` MUST report the mandatory ALLOW capability substrate as
present in `CapInh`, `CapPrm`, `CapEff`, and `CapBnd`. Non-ALLOW bits remain
compatibility-visible state: if a non-ALLOW bit is present in the Linux
credential state, `/proc/<pid>/status` MAY report it, but that bit does not
grant authority. `CapAmb` reports raw Linux ambient compatibility state; KACS
does not require ambient capability state for the ALLOW substrate.

The strict invariant is that the ALLOW capabilities are mandatory substrate.
They MUST remain present wherever Linux capability mechanics would otherwise
drop them out from under KACS:

- `capset()` MUST reject any request that clears an ALLOW capability from the
  effective, permitted, or inheritable sets.
- bounding-set drops and ambient-capability manipulation MUST reject attempts
  that would clear or exclude an ALLOW capability from the compatibility state
  KACS relies on.

`capset()` follows Linux ambient-capability compatibility behavior after the
ALLOW-clear validation above: ambient bits that are no longer present in both
the requested permitted and inheritable sets MAY be cleared from raw ambient
compatibility state. Because `capset()` requests that clear ALLOW bits from
permitted or inheritable are denied, this intersection rule cannot indirectly
clear an existing ALLOW ambient bit.

Direct mutation of non-ALLOW capability state is therefore compatibility-only.
It MAY change what `capget()` or `/proc/self/status` report, but it MUST NOT
change the actual authority answer for a capability-gated operation.

Native commoncap helper paths that make raw Linux capability-subset decisions
before a KACS hook MUST be neutralized when KACS has a corresponding
authoritative hook. This includes the raw subset gates in ptrace access,
`PTRACE_TRACEME`, and `task_setnice` / `task_setscheduler` /
`task_setioprio`. The KACS process-SD and PIP hooks are authoritative for
those operations. Capability checks that reach `security_capable()` directly
remain governed by the KACS capability switchboard.

For raw xattr operations, KACS/FACS metadata hooks are authoritative.
Native security-xattr capability prechecks that would run before the KACS hook
MUST be skipped so the FACS xattr rules decide access. This does not revive
Linux file capabilities: installing or replacing non-empty
`security.capability` file-capability data remains denied by the dead
`CAP_SETFCAP` policy, and exec-time file-capability grants remain suppressed.
Removing stale Linux file-capability metadata is allowed only through the
normal FACS `FILE_WRITE_EA` path.

`capget()` targeting the current process, or another thread sharing the same
process security state, is not a process-boundary operation. `capget(pid)`
targeting another process is a detailed process information query: it requires
`PROCESS_QUERY_INFORMATION` on the target process SD plus PIP dominance.
`SeDebugPrivilege` bypasses only the process-SD check and MUST NOT bypass PIP.

## LSM stack invariant

MAC LSMs (SELinux, AppArmor, SMACK, TOMOYO) and BPF LSM MUST be disabled in the kernel config. Non-MAC security LSMs (landlock, lockdown, yama, integrity) are permitted — they provide complementary hardening without conflicting with KACS's identity-based authorization model. PKM MUST verify the stack at initialization and refuse to activate if any MAC or BPF LSM is present.

> [!INFORMATIVE]
> MAC LSMs could independently deny operations based on their own label/policy systems, undermining KACS's claim as the sole identity-based authorization mechanism and FACS's claim as the sole file access authority. Non-MAC LSMs do not make identity-based access decisions and are safe to stack.
