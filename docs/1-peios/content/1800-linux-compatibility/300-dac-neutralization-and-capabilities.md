---
title: DAC neutralization and capabilities
type: concept
description: Linux's classical DAC (file mode bits) and capability checks run before KACS hooks. To prevent DAC from refusing accesses that KACS would allow, every process carries a mandatory capability substrate that defers DAC checks to LSM. The 41 Linux capabilities are classified as ALLOW, PRIVILEGE, or DENY. This page covers the model.
related:
  - peios/linux-compatibility/overview
  - peios/linux-compatibility/credential-projection
  - peios/linux-compatibility/setuid-and-uid0
  - peios/privileges/overview
  - peios/access-decisions/overview
---

Linux has its own access-control mechanisms below the LSM layer — DAC (file mode bits, owner/group checks) and capabilities (POSIX-style fine-grained privileges). When Peios's KACS runs as an LSM, it sees an access after these other layers have already had their say. If DAC has already refused the access for legacy reasons, KACS never gets a chance to evaluate.

The fix is **DAC neutralization** — Peios sets up every process with a specific set of mandatory Linux capabilities that effectively defer the DAC and capability decisions to the LSM layer. Combined with a classification of the 41 standard Linux capabilities (some always-on, some mapped to KACS privileges, some always-off), this lets KACS be the authoritative access-decision layer.

This page covers the model — what DAC neutralization is, how it works, and the three-way classification of Linux capabilities.

## The problem: DAC runs first

In a standard Linux kernel, an access proceeds through several layers:

1. The syscall (`open`, `read`, etc.) is called.
2. The kernel does its **DAC check** — file mode bits, owner UID, group GID. If DAC refuses, the syscall fails with `EACCES`.
3. The kernel does **capability checks** for operations that require specific capabilities.
4. **LSM hooks** fire. SELinux, AppArmor, etc. get to make additional decisions.

KACS is an LSM. It fires at step 4. By the time it runs, DAC has already had its say. If a file has mode `400` (read-only by owner), a non-owner attempting to read it gets `EACCES` from DAC before KACS sees the call. KACS may have a DACL granting the access, but it cannot help — DAC already refused.

The same applies to capabilities. Operations gated by Linux capabilities (`CAP_SYS_ADMIN`, `CAP_NET_BIND_SERVICE`, etc.) check the capability at the relevant point. If the process lacks the capability, the operation fails. KACS's privilege model (`SeBindPrivilegedPortPrivilege`, `SeTcbPrivilege`, etc.) is parallel but separate.

The naive answer would be to remove DAC from the kernel. But that breaks Linux compatibility — applications expect the kernel to enforce mode bits. Peios's answer is more subtle: keep DAC and capabilities, but neutralise them so they always defer to LSM.

## The fix: mandatory capabilities

Every process on a Peios system is set up with a mandatory set of Linux capabilities **always present in their effective set**:

- `CAP_DAC_OVERRIDE` — bypass DAC read/write checks.
- `CAP_DAC_READ_SEARCH` — bypass DAC read/search checks on directories.
- `CAP_FOWNER` — bypass ownership-based permission checks.
- `CAP_CHOWN` — bypass restrictions on chown.
- `CAP_SETUID` — bypass restrictions on setuid.
- `CAP_SETGID` — bypass restrictions on setgid.

These caps are present on every process's credentials, mandatorily, regardless of what the application's binary or the user requested. They cannot be removed by `capset()`.

Their effect: the DAC layer of the kernel sees these caps and treats the corresponding checks as already-passed. The check proceeds to the LSM layer, where KACS gets to make the actual decision.

This is the "neutralisation". DAC is not gone — the code paths still exist — but it never refuses anything by itself. Every access flows through to KACS.

The same approach is taken for the capability checks: capabilities relevant to access decisions are pre-allowed so the kernel does not stop the operation before LSM gets to see it. KACS then makes the call.

## The capability classification

There are 41 Linux capabilities defined in v0.20 (the standard set from Linux 5.x). Peios classifies each as one of three things:

| Class | Meaning |
|---|---|
| **ALLOW** | Always present in the process's effective set. Cannot be cleared. Used to neutralise the DAC and capability checks that need to defer to LSM. |
| **PRIVILEGE** | Mapped to a KACS privilege. `cap_capable()` returns "granted" iff the calling token holds the corresponding KACS privilege. |
| **DENY** | Permanently denied. The check always says "no", regardless of the credential state. Used for capabilities that have no useful semantic on Peios. |

The classification is per-capability and is hard-coded into the kernel.

### ALLOW capabilities

The DAC-neutralisation set is the core of ALLOW:

| Capability | What it would normally gate | Why ALLOW |
|---|---|---|
| `CAP_DAC_OVERRIDE` | DAC mode-bit checks | KACS replaces DAC entirely; the bit must be on so DAC always defers. |
| `CAP_DAC_READ_SEARCH` | DAC read/search on directories | Same. |
| `CAP_FOWNER` | Owner-based bypasses (chmod own files, etc.) | Same. |
| `CAP_CHOWN` | Restriction on `chown()` | Linux normally requires CAP_CHOWN to chown; Peios redirects chown through KACS anyway. |
| `CAP_SETUID` | Restriction on `setuid()` | `setuid()` is itself reinterpreted by Peios; the cap must be present for the syscall to even get to the LSM hook. |
| `CAP_SETGID` | Same for `setgid()` | Same. |

These are mandatory. No process can clear them; `capset()` ignores attempts to remove them.

### PRIVILEGE capabilities

Many Linux capabilities map cleanly to a KACS privilege. Examples:

| Capability | Maps to KACS privilege |
|---|---|
| `CAP_NET_ADMIN` | (administrative network operations, gated by appropriate KACS privileges in v0.20) |
| `CAP_SYS_TIME` | `SeSystemtimePrivilege` |
| `CAP_SYS_BOOT` | `SeShutdownPrivilege` |
| `CAP_SYS_NICE` | `SeIncreaseBasePriorityPrivilege` |
| `CAP_IPC_LOCK` | `SeLockMemoryPrivilege` |
| `CAP_SYS_RESOURCE` | `SeIncreaseQuotaPrivilege` |
| `CAP_NET_BIND_SERVICE` | `SeBindPrivilegedPortPrivilege` (Peios-custom) |
| `CAP_AUDIT_CONTROL`, `CAP_AUDIT_READ`, `CAP_MAC_ADMIN` | `SeSecurityPrivilege` |

When the kernel asks "does this caller have CAP_X?", the answer is computed by consulting the token's privileges. The kernel's `security_capable()` hook is what does this lookup — Peios's PKM module overrides the default capability check to consult KACS privileges instead of (or in addition to) the credential's capability set.

This means a process's *Linux-capability* state and its *KACS-privilege* state are kept consistent for the PRIVILEGE-class capabilities. A user with `SeSystemtimePrivilege` enabled on their token gets the answer "yes" from `cap_capable(CAP_SYS_TIME)`; a user without it gets "no".

### DENY capabilities

A few Linux capabilities have no useful semantics on Peios and are always denied:

| Capability | Why DENY |
|---|---|
| `CAP_SETFCAP` | Linux file capabilities (`security.capability` xattr) are dead on Peios. The xattr can't be set; there's nothing for this capability to do. |
| Reserved / future capabilities | Caps the kernel has defined but Peios has no mapping for, default to DENY. |

These are denied unconditionally. No combination of token state grants them.

## security_capable() is authoritative

The kernel exposes a function `security_capable()` that callers use to check "is this caller allowed to do the thing this capability gates?". Peios's PKM module hooks this function:

- For ALLOW caps: always returns granted.
- For PRIVILEGE caps: returns granted iff the corresponding KACS privilege is enabled on the calling token.
- For DENY caps: always returns denied.

**`security_capable()` is authoritative.** The actual bit state of the credentials (the cap masks visible to `capget()`) is informational; the security decision comes from `security_capable()`.

Why this matters: a program that reads `/proc/self/status` sees a capability bitmask. That bitmask is the "what the credentials currently say" view — for compatibility with tools that parse the file. But the kernel's enforcement uses `security_capable()`, which goes through KACS.

The two views are kept consistent for ALLOW (the bits are always on) and DENY (the bits are always off). For PRIVILEGE, the visible bitmask reflects the KACS privilege state — a privilege enabled on the token corresponds to the cap appearing in the bitmask.

## capset() limitations

`capset()` lets a process modify its capability set. Under Peios:

- **It cannot clear ALLOW bits.** Attempts to remove `CAP_DAC_OVERRIDE` etc. silently leave them set. The process cannot opt out of DAC neutralisation.
- **It cannot grant DENY bits.** Attempts to add `CAP_SETFCAP` etc. silently fail (the bit stays clear).
- **For PRIVILEGE bits**, `capset()` cannot grant capabilities the corresponding KACS privilege does not provide. A process can drop the bit (which would normally drop the capability), but this does not affect the underlying KACS privilege — the privilege is the source of truth.

The kernel maintains the apparent capability state consistent with the KACS privileges (and the ALLOW/DENY rules). A program using `capset()` to try to drop privileges sees the visible mask drop, but the underlying KACS state is what `security_capable()` consults.

This is intentional: programs that drop capabilities for security hardening (the standard "drop CAP_NET_ADMIN before processing untrusted input" pattern) do not get the semantics they expect, because the kernel's authoritative decision uses KACS. To actually drop authority on Peios, use AdjustPrivileges to remove the corresponding KACS privilege.

## prctl(PR_SET_KEEPCAPS) and the secure bits

A program that does setuid and wants to preserve some capabilities afterward sets `PR_SET_KEEPCAPS` via `prctl()`. Under Peios:

- `prctl(PR_SET_KEEPCAPS, 1)` is accepted but does not change the effective behaviour. The Linux capability state is reset across setuid by default; the KACS token state is unaffected by setuid (unless `SeAssignPrimaryTokenPrivilege` triggers the full identity swap path).
- `prctl(PR_SET_SECUREBITS, ...)` is similarly accepted but does not modify the KACS state.

These are operations that affect the Linux credentials view. The KACS authority continues to live on the token.

## Capabilities at exec — file capabilities are dead

Linux supports file-bearing capabilities via the `security.capability` xattr. A binary with this xattr gets the listed capabilities at exec, regardless of who launched it. This is how (for example) `ping` gets `CAP_NET_RAW` on a Linux system.

Under Peios, **file capabilities are dead**:

- Writing the `security.capability` xattr is unconditionally denied.
- Existing `security.capability` xattrs on files are ignored at exec.
- The mechanism's role on Peios is filled by KACS privileges, applied at token creation time by authd.

A binary that needs special capabilities on Peios doesn't carry them as a file xattr. Instead, authd's privilege policy decides which principals get which privileges; the binary running under one of those principals' tokens gets the corresponding KACS privileges naturally.

The capability `CAP_SETFCAP` (set file capabilities) is in the DENY class as a consequence — there are no file capabilities to set.

## What this looks like in practice

For an application running on Peios:

- **Linux DAC checks are invisible.** The application's mode-bit-aware code paths work, but the mode bits don't refuse anything. KACS makes the call.
- **Capability checks (via `security_capable()`) return the KACS-derived answer.** A process that holds `SeSystemtimePrivilege` on its token sees `CAP_SYS_TIME` as granted; one that doesn't sees it as denied.
- **`capset()` does not grant or remove ALLOW/DENY capabilities.** The mask returned by `capget()` is informational.
- **File capabilities don't work.** Binaries that depended on `security.capability` need to be run under tokens with the appropriate KACS privileges instead.

For most applications this is transparent. They make their normal calls; the access decisions come out as KACS decides. The exceptions are programs that explicitly manipulate Linux capabilities — a paranoid daemon that calls `prctl(PR_CAPBSET_DROP)` to drop unneeded capabilities — and these programs see their drops not take effect in the way they expect. Migrating to use KACS privileges via AdjustPrivileges is the right pattern.
