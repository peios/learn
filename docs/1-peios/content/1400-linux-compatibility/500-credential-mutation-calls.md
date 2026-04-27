---
title: Credential Mutation Calls
type: concept
description: How the Linux setuid family, the setuid bit on exec, and PR_SET_NO_NEW_PRIVS behave on Peios — all the calls that traditionally mutate identity, all of them either silently no-op or cosmetically present-and-not-authoritative.
related:
  - peios/linux-compatibility/credential-projection
  - peios/linux-compatibility/understanding-linux-compatibility
  - peios/identity/how-tokens-work
---

The Linux ABI exposes a family of syscalls and an exec-time mechanism that traditionally **change a process's identity**: `setuid()`, `setgid()`, `setresuid()`, `setresgid()`, `setfsuid()`, `setfsgid()`, the `setuid` and `setgid` bits on executable files, and the related accessors. On a traditional Unix system these are how a process drops privilege, switches user, or gains access to a different identity's resources.

On Peios the **token** is the sole source of authority. Calls that mutate the Linux credential surface continue to exist for ABI compatibility, but they cannot move the process between security identities. This page describes exactly what each call does on Peios — which is in most cases nothing, and in the remaining cases either a cosmetic credential-field write that has no security effect, or, with a specific TCB privilege, a genuine token swap mediated by authd.

## The five Linux UID/GID slots

Linux carries five distinct identity values on every process credential. All five exist on Peios for compatibility but none of them are consulted by AccessCheck:

| Slot | Linux purpose | What it is on Peios |
|---|---|---|
| **Real UID/GID** (`uid`, `gid`) | The user this process is running as | Projected UID/GID from the primary token, set at token install time |
| **Effective UID/GID** (`euid`, `egid`) | The identity used for permission checks | Projected UID/GID from the *effective* token (impersonation if active, primary otherwise) |
| **Saved set-UID/GID** (`suid`, `sgid`) | Stored value letting setuid binaries swap back | Projected UID/GID, populated identically to real on Peios |
| **Filesystem UID/GID** (`fsuid`, `fsgid`) | UID used by filesystem operations specifically | Read-through view of the effective token's projected UID. See [Credential projection](credential-projection). |
| **Supplementary GIDs** | Additional groups the user belongs to | Projected supplementary GIDs from the token's group SIDs that have `gidNumber` mappings |

Because every slot is derived from the token (or one of two tokens, in the case of impersonation), the values stay coherent automatically. There is no risk of a process being in some inconsistent in-between state where, say, `euid` claims one identity and the actual security state thinks another. The token is authoritative; the slots reflect it.

## The `setuid()` family

The `setuid()` family of syscalls — `setuid`, `setgid`, `setresuid`, `setresgid`, `setgroups` — is the traditional way a Linux program changes its credentials at runtime. On Peios the behaviour is bimodal, controlled by a single privilege:

**Without `SeAssignPrimaryTokenPrivilege` (the common case).** The call is a **silent no-op**. It returns 0 (success), but nothing changes — neither the Linux credential nor the KACS token. The process's authority before and after the call is identical. `getuid()` returns the same value afterwards as before.

The silent success is deliberate. A traditional Linux program that calls `setuid(target)` to drop privileges expects success on the typical path; returning an error would either crash the program or send it down a defensive code path it never gets exercised. Returning success and doing nothing is the safest failure mode: the program continues to function, and because UIDs have no authorisation meaning on Peios, the failure to "drop" doesn't grant any extra power.

**With `SeAssignPrimaryTokenPrivilege` (TCB-only).** The call is intercepted and redirected to authd, which obtains a token for the target UID's corresponding principal. Both the KACS token and the Linux credential change — a genuine identity transition, just routed through authd instead of taking the kernel-only Linux path.

This is how legitimate identity transitions happen on Peios: a TCB process holds the privilege, calls `setuid()`, and authd produces the appropriate target token. The kernel-side credential field updates as a side effect.

## The `setuid` bit on executable files

The filesystem `setuid` bit on an executable historically tells the kernel to change the process's effective UID to the file owner's UID at exec time. This is the mechanism behind `sudo`, `passwd`, `ping`, and other classic setuid-root binaries.

Peios applies a different rule than the `setuid()` syscall, deliberately:

**Without `SeAssignPrimaryTokenPrivilege`.** The `euid` and `suid` *do* change to the file owner's UID at the Linux-credential level. The KACS token is unchanged. The process sees `geteuid() == 0` (if the binary is owned by root) and proceeds to run, but KACS continues to enforce the original token. This is **cosmetic escalation** — visible to userspace, ignored by the security model.

**With `SeAssignPrimaryTokenPrivilege`.** The `euid` and `suid` change *and* the KACS token swaps to the corresponding identity, just like the syscall path. Genuine privilege escalation, mediated by authd.

The asymmetry between the syscall and the bit — the syscall no-ops, the bit cosmetically escalates — is intentional:

- **`setuid()` is deescalation.** A program calling it expects to drop privileges. Doing nothing is the safe failure mode; the program runs with its existing authority, which is at most what it had before.
- **The setuid bit is escalation.** A `sudo`-style binary that runs and finds `geteuid() != 0` will refuse to function — it explicitly checks for root and exits. The `euid` change *must* happen at the Linux-credential level for the program to run at all, even when no real escalation occurs underneath. The token doesn't move, but the binary continues to function and KACS keeps it under its original token's authority.

| Mechanism | With `SeAssignPrimaryTokenPrivilege` | Without |
|---|---|---|
| `setuid()` syscall | All UIDs + token change | Silent no-op |
| `setuid` bit on exec | UIDs + token change | UIDs change, token unchanged |

## `setfsuid` and `setfsgid`

`setfsuid()` and `setfsgid()` were a workaround for a specific Linux concern: NFS server code wanted to per-thread-impersonate clients without affecting the rest of the process's credentials. They allow the filesystem-credential slot to deviate from `euid`/`egid`.

On Peios these calls are **even more strictly no-op** than the rest of the setuid family. The kernel's `current_fsuid()` is patched to return the projected UID from the effective token, ignoring `cred->fsuid` entirely. Even if a successful `setfsuid()` did write the field, no kernel consumer would read it for filesystem operations. The function exists as an ABI surface; the value behind it is dead state.

Filesystem credentials always reflect the effective token — the impersonation token if one is active, the primary token otherwise — and the only way to change them is via `kacs_impersonate_*`. See [Credential projection](credential-projection) for the full rule.

## The `uid0` utility

A small number of legacy Linux programs explicitly check `getuid() == 0` and refuse to run otherwise — package managers, some daemons, init-style tools that originated on systems where root was meaningful. For these, Peios provides the `uid0` utility.

`uid0 program args...` sets `cred->uid`, `cred->euid`, and `cred->suid` to 0, then execs the target program. The program's `getuid()`, `geteuid()`, and `getresuid()` calls all return 0. The KACS token is unchanged.

The `current_fsuid()` patch is unaffected by this — filesystem operations still use the projected UID from the token, so files created under `uid0` are owned by the real user, not by root. This means `uid0` cannot be used to "create things as root." It exists strictly for legacy binaries that gate themselves on `getuid() == 0` and would otherwise refuse to run.

## `PR_SET_NO_NEW_PRIVS`

Linux's `PR_SET_NO_NEW_PRIVS` is a sticky per-process flag (settable but not clearable) that, on Linux, has four substantive effects:

1. `exec()` ignores `setuid` and `setgid` bits on executable files.
2. `exec()` ignores file capability xattrs.
3. `AT_SECURE` is set in the new process's auxiliary vector, instructing libc and similar runtimes to behave defensively (e.g., `glibc` strips `LD_PRELOAD`).
4. Some LSMs apply additional restrictions; on mainline Linux this is also the prerequisite for installing a seccomp BPF filter as an unprivileged process.

> [!INFORMATIVE]
> The KACS spec does not currently address `PR_SET_NO_NEW_PRIVS` semantics. The behaviour described below is the position taken by these compatibility docs and may be revisited as the spec evolves.

On Peios, the substantive Linux effects collapse:

- (1) The `setuid` bit is already cosmetic without `SeAssignPrimaryTokenPrivilege` — there is no privilege gain from setuid bits to gate. Setting `NO_NEW_PRIVS` adds nothing here.
- (2) File capabilities are already suppressed at exec by KACS's LSM hooks. Capabilities derive from the token via the switchboard, not from file xattrs. There is no cap gain from xattrs to gate. Setting `NO_NEW_PRIVS` adds nothing here either.
- (3) `AT_SECURE` *does* propagate — userspace runtimes can still inspect the flag and behave defensively. This effect is preserved.
- (4) Seccomp filter installation is not yet supported on Peios; if and when it is, `NO_NEW_PRIVS` will gate unprivileged installation in the same way it does on Linux.

In summary: `NO_NEW_PRIVS` on Peios is a flag that exists, propagates across exec, and is sticky once set, but most of its Linux-side security effects are no-ops because the underlying mechanisms it disables are already neutralised. Code that defensively sets `NO_NEW_PRIVS` continues to work and is harmless. Code that depends on `AT_SECURE` continues to work. The remaining substantive effect — gating seccomp — will become meaningful when seccomp ships.

## Known compatibility gaps

A few Linux patterns do not survive the projection model unchanged. Software ported to Peios should be aware of them:

- **Privilege-drop pattern.** Daemons that call `setuid(target)` and then check `getuid() != target` to verify the drop succeeded will see `setuid()` return success but `getuid()` return the original value. The sanity check fails. Code performing privilege management should use KACS-native token operations instead of the setuid-based pattern.
- **`capset()` / `capget()`.** Software that directly inspects or manipulates Linux capabilities may behave unexpectedly. Capabilities are derived from the token via the switchboard, not from `cred->cap_*` fields, so direct manipulation has limited effect. See [Linux Capabilities](linux-capabilities) for the model.
- **`setfsuid()` for filesystem effect.** As described above, `current_fsuid()` ignores `cred->fsuid` and reads the token's projected UID directly. `setfsuid()` calls have no filesystem-visible effect.
- **`access()` / `faccessat()`.** These syscalls answer "would this thread be allowed to access this file?" using the effective token. There is no concept of "real identity" answer in KACS — the access check uses the token actually in effect, including impersonation.
- **`SO_PEERCRED` and `SCM_CREDENTIALS`.** Both surfaces carry projected UIDs from the token at the time of the connection. Because `CAP_SETUID` is in the ALLOW class of the capability switchboard, a process can write any UID into an `SCM_CREDENTIALS` ancillary message — but this is cosmetic forgery; the receiving side cannot rely on the value for any access decision. Receivers that need authoritative peer identity should use the KACS token APIs.
- **Legacy `auditd`.** Linux audit records projected UIDs because that's what its kernel hooks see. KACS audit (via KMES) is the authoritative log for security-relevant events; legacy `auditd` is observational and may attribute actions to UIDs that don't reflect the actual token behind them.

The general rule: anything that depends on a UID being a security boundary should be ported to use tokens. Anything that uses UIDs as observational identifiers — log lines, file ownership display, tool output — continues to work.
