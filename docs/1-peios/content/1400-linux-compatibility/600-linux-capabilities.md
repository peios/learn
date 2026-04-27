---
title: Linux Capabilities
type: concept
description: How Peios reinterprets the 41 Linux capabilities — which are always allowed (DAC bypass), which map to a Peios Privilege, and which are denied outright.
related:
  - peios/linux-compatibility/credential-projection
  - peios/linux-compatibility/credential-mutation-calls
  - peios/identity/how-tokens-work
---

Linux's **capability system** is the mechanism that gates operations the kernel considers privileged: binding low ports, loading kernel modules, sending arbitrary signals, manipulating system clocks, and so on. A traditional Linux process is checked against a set of named capabilities (`CAP_NET_BIND_SERVICE`, `CAP_SYS_ADMIN`, and 39 others) that may or may not be present in its credential. If the relevant capability is present, the operation is allowed; if not, it's denied.

Peios uses tokens and Privileges instead. Linux capabilities still exist as an ABI surface, but every capability is reinterpreted by KACS at the LSM hook layer, classified into one of three categories that determine what the capability check actually does.

## Three categories

KACS classifies all 41 Linux capabilities into a single fixed scheme — the **capability switchboard**. The three categories:

| Category | What happens at `cap_capable()` | Why |
|---|---|---|
| **ALLOW** | Always succeeds | Required for DAC neutralisation. KACS enforces these operations independently via its own LSM hooks, so the capability must be present to let the operation reach those hooks. |
| **PRIVILEGE** | Maps to a specific Peios Privilege; the check succeeds if the calling thread's effective token holds that Privilege | Captures privileged operations that don't have an LSM hook KACS otherwise enforces. The Privilege is the real authorisation. |
| **DENY** | Always fails | The capability is dead, dangerous, or would let userspace bypass KACS itself. |

The switchboard is **fail-closed**: any capability not explicitly listed in ALLOW or PRIVILEGE is denied. There is no "default allow" path. Adding a new capability to the kernel without updating the switchboard would result in it being denied to every process, which is the safe failure mode.

## ALLOW: DAC bypass

A handful of capabilities exist on Peios solely to neutralise Linux DAC (the UID-based mode-bit permission system). Linux evaluates DAC before consulting LSM hooks; if DAC denies an operation, the LSM never fires, and KACS cannot override the denial. To prevent DAC from blocking operations KACS would actually allow, every Peios process is granted the DAC-bypass capabilities unconditionally:

- **`CAP_DAC_OVERRIDE`** — bypass file read/write/execute permission checks
- **`CAP_DAC_READ_SEARCH`** — bypass directory read/search checks
- **`CAP_FOWNER`** — bypass checks requiring `fsuid` to match the file owner
- **`CAP_CHOWN`** — bypass the restriction that only the file owner can change ownership
- **`CAP_FSETID`** — bypass restrictions on setuid/setgid bit modifications
- **`CAP_SETUID`** / **`CAP_SETGID`** — allow Linux credential changes (cosmetic on Peios)
- **`CAP_KILL`** — bypass UID-based signal-delivery checks (the real check is in KACS's `task_kill` hook)
- **`CAP_IPC_OWNER`** — bypass UID-based SysV IPC ownership checks
- **`CAP_LEASE`** — bypass file-lease ownership checks

These capabilities **must be present on every credential**. KACS denies any attempt to clear them — via `capset()`, via bounding-set drops, or via ambient capability manipulation. A process that successfully cleared `CAP_DAC_OVERRIDE` would find itself unable to do anything, because DAC would start refusing operations and KACS's LSM hooks would never fire.

The DAC-bypass set looks like privilege from a Linux perspective, but on Peios it represents the absence of authority — the capabilities exist to make Linux's old gatekeeping mechanism transparent, not to grant power. The actual enforcement is in KACS's LSM hooks, which evaluate the token against the security descriptor on whatever object is being accessed.

## PRIVILEGE: mapped to Peios Privileges

Capabilities that gate operations *not* covered by KACS's other hooks are routed through the Peios Privilege system. When Linux calls `cap_capable()` to check one of these capabilities, KACS's `security_capable` hook evaluates whether the calling thread's effective token holds the corresponding Privilege.

A few illustrative examples:

| Linux capability | Peios Privilege | Operation gated |
|---|---|---|
| `CAP_NET_BIND_SERVICE` | `SeBindPrivilegedPortPrivilege` | Binding TCP/UDP sockets to ports below 1024 |
| `CAP_SYS_PTRACE` | `SeDebugPrivilege` | Attaching a debugger, reading another process's memory |
| `CAP_SYS_TIME` | `SeSystemtimePrivilege` | Adjusting the system clock |
| `CAP_SYS_BOOT` | `SeShutdownPrivilege` | Triggering reboot/halt |
| `CAP_AUDIT_WRITE` | `SeAuditPrivilege` | Writing audit records |
| `CAP_SYS_NICE` | `SeIncreaseBasePriorityPrivilege` | Raising scheduling priority, real-time class, affinity outside cpuset |

A handful of capabilities — `CAP_SYS_ADMIN`, `CAP_SYS_RAWIO`, `CAP_SYS_CHROOT`, `CAP_SYSLOG`, `CAP_BPF`, and others that have no direct Peios equivalent — all map to **`SeTcbPrivilege`**, the highest-tier "act as part of the operating system" privilege. This reflects the reality that these capabilities are Linux's catch-all for "extremely privileged"; Peios collapses them onto its single highest privilege.

The full mapping is documented authoritatively in the KACS spec under `linux-credential-model/dac-neutralization.md`. The learn doc deliberately does not duplicate the full table — the spec is the source of truth, and the mapping is more useful as a single canonical list than as something replicated and potentially drifting.

When a Linux program calls `cap_capable(CAP_X)`, the answer depends on what's in the calling thread's effective token. If the corresponding Privilege is present and enabled, the call returns success; otherwise it returns denied. The result is that traditional Linux software's capability checks "just work" against Peios's Privilege model, with no source-level changes required.

## DENY: dead or dangerous

A small number of capabilities are denied unconditionally:

| Capability | Why denied |
|---|---|
| `CAP_SETPCAP` | Manipulates the bounding set and inheritable set. Capabilities are dead on Peios; granting this would let a process erase its own DAC-bypass capabilities, breaking the mechanism that keeps it functional. |
| `CAP_SETFCAP` | Sets file capability xattrs. File capabilities are not honoured by KACS, so granting this would only enable a misleading no-op. |
| `CAP_MAC_OVERRIDE` | Designed to let a process bypass MAC LSM decisions. KACS is the active LSM — bypassing it would defeat the security model. |

A `cap_capable()` check for any of these always returns denied, regardless of token contents.

## File capabilities

Linux supports **file capabilities** stored as extended attributes on executables. When a binary with file capabilities is exec'd, the kernel grants those capabilities to the new process — the modern alternative to setuid root for granting limited privilege.

Peios does not honour file capabilities. The KACS LSM hook `security_bprm_creds_from_file` suppresses the file capability set at exec time. Capabilities on the resulting process come exclusively from the switchboard's interpretation of the token's Privileges, never from xattrs on the binary.

The reasoning is the same as for the setuid bit: identity and authority on Peios are determined by the token, and the token is decided at process creation by the supervisor, not by metadata on the file being exec'd. A binary cannot grant itself authority by carrying capability xattrs any more than it can grant itself authority by being owned by root.

## The five capability sets

Linux defines a richer model of capability state than just "what's the current cap set." Each thread carries five named cap sets:

| Set | Linux purpose | Peios behaviour |
|---|---|---|
| **Permitted** | The ceiling of capabilities the thread may activate. A capability cannot be made effective unless it is also in the permitted set. | Substrate-as-is at the credential level. The set always contains the DAC-bypass caps; KACS denies any drop that would clear them. Has no role in `cap_capable`'s answer — the switchboard does. |
| **Effective** | The capabilities currently active. `cap_capable` consults this set on Linux. | Substrate-as-is at the credential level. Always contains the DAC-bypass caps. Linux's `cap_capable` consults it; KACS's `security_capable` LSM hook overrides with the switchboard answer. |
| **Inheritable** | The set preserved across `execve` to interact with file capabilities on the executed binary. | Substrate-as-is at the credential level. File capabilities are suppressed at exec on Peios, so the inheritable set has no effect on what the new process actually has. |
| **Bounding** | The maximum capabilities the thread can ever hold, even after `execve` with file caps. Once dropped, cannot be re-added. | Drops denied for DAC-bypass caps via `security_task_prctl`. Otherwise honoured at the credential level, but cosmetic — `cap_capable` does not consult it. |
| **Ambient** | Capabilities automatically added at `execve`, even without file caps or setuid. Introduced in Linux 4.3. | Drops and raises denied when affecting DAC-bypass caps. Otherwise honoured at the credential level, cosmetic. Manipulated via `prctl(PR_CAP_AMBIENT, ...)`. |

The picture is consistent across the table: credential-level set membership remains state that programs can read, and (for non-DAC-bypass caps) mutate, but the actual authority answer comes from `security_capable` reading the token's Privileges via the switchboard. Cap set state is observational, with one strict invariant: **DAC-bypass capabilities must remain present in all sets at all times**.

In practice this means defensive programs that drop unneeded capabilities continue to function — `capset()` returns success, `capget()` reports the dropped state — but the dropping doesn't move them between trust tiers. That's the token's job.

## Capability transformation across `execve`

Linux defines a complex algorithm for how each cap set transforms across `execve` based on the file's stored capabilities, the executing thread's existing sets, and the process's securebits flags. The algorithm is documented in detail in `capabilities(7)`.

On Peios, the transformation collapses into something much simpler:

- **File capabilities are suppressed at exec** by `security_bprm_creds_from_file`. The file's stored caps do not contribute to the new process's capabilities, regardless of file capability version (1, 2, or 3).
- The Permitted, Effective, Inheritable, and Bounding sets at exec time are computed via the standard Linux algorithm, but the result is always constrained so that DAC-bypass caps remain present in all of them.
- The Ambient set survives `execve` as on Linux, modulo the same DAC-bypass invariant.
- The actual authority of the new process comes from the token, not from any of these sets.

The net effect is that programs reading or manipulating cap sets continue to see consistent state across `execve`, but the only path to changing what the new process can actually do is changing its token (set by the supervisor before `execve`).

## Securebits

Linux **securebits** are a small set of per-process flags that modify capability and `setuid` behaviour. They are read and set via `prctl(PR_GET_SECUREBITS)` / `prctl(PR_SET_SECUREBITS)`.

| Securebit | Linux effect |
|---|---|
| `SECBIT_NOROOT` | Disable the special "root grants all caps" behaviour (real or effective UID 0 normally implies all capabilities). |
| `SECBIT_NO_SETUID_FIXUP` | Disable the kernel-level setuid → cap-set adjustment logic. |
| `SECBIT_KEEP_CAPS` | Preserve the permitted cap set across `setuid()` to a non-zero UID. |
| `SECBIT_NO_CAP_AMBIENT_RAISE` | Lock out the ambient-capability raise operation for this process. |

Each securebit also has a `_LOCKED` companion that, once set, prevents the bit from being cleared.

On Peios, all four bits are retained as state at the credential level — programs can read them and, where Linux would allow, set them — but their substantive effects are largely moot because the underlying behaviours they modify are themselves moot:

- `setuid()` is a silent no-op without `SeAssignPrimaryTokenPrivilege`, so the setuid → cap-set fixup logic that `SECBIT_NO_SETUID_FIXUP` and `SECBIT_KEEP_CAPS` modify is itself dormant.
- "Root grants all caps" doesn't apply on Peios — caps come from the switchboard, not from `cred->uid == 0` — so `SECBIT_NOROOT` has nothing to disable.
- `SECBIT_NO_CAP_AMBIENT_RAISE` continues to lock ambient raises (subject to the DAC-bypass denial), but ambient cap state is itself observational.

Defensive code that sets securebits continues to work and is harmless. Code that depends on securebits to enforce a security boundary should be ported to use Privilege adjustments on the token instead.

## `capset()` / `capget()`

The userspace interface for inspecting and manipulating capabilities — `capset()` and `capget()` (and the older `cap_get_proc()` / `cap_set_proc()` library wrappers) — work on Peios with the same constraints described above. `capget()` returns whatever caps the credential currently holds (DAC-bypass caps always present, others reflecting drops the program has made). `capset()` is constrained by the deny rules: anything that would clear a DAC-bypass capability is rejected.

Software that introspects its own capability set will see expected values; software that depends on capability changes for security boundaries should be ported to use Privilege adjustments on the token via the KACS APIs instead.

## Practical guidance

For application code that checks capabilities defensively (e.g., "do I have `CAP_NET_BIND_SERVICE` before I try to bind to port 80?"), the usual idioms continue to work — `cap_capable()` returns the right answer based on the token's Privileges, and the operation either succeeds or is denied accordingly.

For application code that *manipulates* capabilities — drops them at startup, raises them via file caps, etc. — the operations either become no-ops or fail in expected ways. Native Peios services should not perform capability manipulation; their authority is defined by the token they were started with, set by their supervisor.
