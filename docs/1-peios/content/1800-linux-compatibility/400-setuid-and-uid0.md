---
title: setuid and uid0
type: concept
description: The setuid family of syscalls is reinterpreted under Peios. Without SeAssignPrimaryTokenPrivilege the call is a no-op; with it, the call triggers a full identity swap via authd. The setuid bit on exec follows the same rule. The uid0 utility offers a cosmetic UID=0 view for legacy programs. This page covers the semantics.
related:
  - peios/linux-compatibility/overview
  - peios/linux-compatibility/credential-projection
  - peios/linux-compatibility/dac-neutralization-and-capabilities
  - peios/privileges/categories
  - peios/tokens/overview
---

The Linux `setuid()` family of syscalls — `setuid`, `seteuid`, `setreuid`, `setresuid`, plus the GID variants — is reinterpreted under Peios. Without a specific privilege, calling `setuid()` succeeds (returns 0) but **does not actually change anything**. With the privilege, it triggers a full identity swap through authd. The setuid-bit-on-exec mechanism (`S_ISUID` in a file's mode) follows the same rule.

For legacy programs that check `getuid() == 0` to detect administrative privilege, a separate utility — `uid0` — provides a cosmetic UID-0 view without actually changing the underlying token. This page covers all three: setuid syscalls, the setuid bit, and `uid0`.

## The setuid syscalls

The Linux setuid family has several variants:

- `setuid(uid_t uid)` — set real and effective UIDs to `uid`.
- `seteuid(uid_t euid)` — set effective UID to `euid`.
- `setreuid(uid_t ruid, uid_t euid)` — set real and effective independently.
- `setresuid(uid_t ruid, uid_t euid, uid_t suid)` — set real, effective, and saved-set independently.
- Corresponding `setgid`, `setegid`, `setregid`, `setresgid` for GIDs.

On Linux, these change the kernel's `cred->uid` (and related fields). The credential is updated; the next `getuid()` returns the new value.

On Peios, the behaviour depends on whether the calling token holds `SeAssignPrimaryTokenPrivilege`:

| Caller has `SeAssignPrimaryTokenPrivilege` | Behaviour |
|---|---|
| No | The syscall returns 0 but **nothing changes**. The token is unchanged. The projection is unchanged. `getuid()` returns the same value before and after. |
| Yes | The kernel makes an upcall to authd to perform a full identity swap. authd authenticates the new identity (or constructs the appropriate token), and the calling process's primary token is replaced with the new one. |

The no-op path is the default. The privileged path is reserved for a narrow set of components — typically authd itself, plus a small number of bootstrap services.

### Why no-op without privilege

A reasonable question: why does setuid succeed but do nothing? Why not just return an error?

The answer is compatibility. Linux programs assume `setuid()` works in the documented way. A program that does `setuid(geteuid())` to "drop" privileges expects success. A `setuid(0)` followed by `setuid(non-root)` is a common idiom for "elevate, do work, drop". If setuid simply returned an error, every Linux program that did this would fail on Peios.

By making the call succeed but not change anything, Peios preserves the contract — programs see success — without actually changing the token. The programs continue running on whatever identity they had; the kernel's KACS-level access control is unaffected.

The cost: programs that *rely on* the post-setuid identity having changed might do incorrect things. A program that drops to a less-privileged UID expecting that to limit it will find that KACS access checks are unaffected, and the process retains whatever access its token had. For most programs this is fine (they're using setuid as defence in depth, and KACS's gates are stricter); for a few it could be surprising.

The escape hatch: a program that genuinely needs to change identity at runtime needs to be running with `SeAssignPrimaryTokenPrivilege` (so the call actually does something) or to be re-architected to do the identity-swap work via the proper KACS channels (call authd directly, get a token, install it via `KACS_IOC_INSTALL`).

### What the privileged path does

When the calling token holds `SeAssignPrimaryTokenPrivilege` and `setuid(N)` is called, the kernel:

1. Looks up the SID corresponding to UID N (via the directory's reverse mapping).
2. Asks authd to construct a token for that principal.
3. Replaces the calling process's primary token with the new one.
4. Updates the credentials so subsequent `getuid()` returns N.

The token is genuinely different now. Privileges, groups, integrity level are whatever authd produced for that principal. The previous token is released (its references drop).

This is what login frontends do. A user signs in; the login frontend (running with `SeAssignPrimaryTokenPrivilege`) calls `setuid(target_user)`; the frontend's token is replaced with the user's token; the rest of the user's session runs as the user.

This is also the path for `su` and similar utilities — they run with the privilege and use the setuid syscall to actually become a different user.

### The privilege is rare

`SeAssignPrimaryTokenPrivilege` is held by:

- **authd** itself (which actually needs it to mint tokens).
- **Login frontends** that handle user sign-in (sshd, the console login, terminal services).
- **A few specific TCB tools** that need to launch processes as specific users (peinit at boot, certain administrative utilities).

Ordinary programs do not have it. A user-installed application that calls `setuid()` falls through to the no-op path.

This is the right distribution: only components that legitimately swap identities have the privilege. Everything else gets the compatibility behaviour.

## The setuid bit on exec

A file with `S_ISUID` set in its mode runs as the file's owner when exec'd (on Linux). The setuid bit is what makes `ping` run as root, makes `passwd` able to modify `/etc/shadow`, makes `sudo` work.

On Peios, the setuid bit's behaviour mirrors the setuid syscall:

| Calling token has `SeAssignPrimaryTokenPrivilege` | Setuid-bit behaviour |
|---|---|
| No | The euid/suid fields are cosmetically updated to match the binary's owner UID, but the **KACS token is unchanged**. The binary runs as the calling principal, just with a different `getuid()` return. |
| Yes | A full identity swap occurs at exec, as if `setuid(file_owner)` had been called between fork and exec. |

The cosmetic-only path is what most setuid-bit binaries get on Peios. The binary runs as the user who invoked it; the euid that `geteuid()` returns is the binary's owner; KACS sees no identity change.

For most uses this is correct. A setuid-root binary on a Linux system that just wants to do "is the caller root?" check sees `geteuid() == 0` even on Peios; the cosmetic euid update is enough for that.

For uses that actually need to perform privileged operations on the user's behalf, the cosmetic-only path is insufficient. The KACS access control sees the calling user, not the binary's owner. The binary fails its access checks. The fix is to either:

- Run the binary as a service launched by peinit with the appropriate token.
- Have the binary connect to a service (running with the appropriate identity) and ask the service to do the work.

This is the pattern for "privileged operations" on Peios. Rather than setuid-bit binaries, services run with the right token; clients connect to the services and ask for what they need.

The setuid-bit-as-identity-swap path (with `SeAssignPrimaryTokenPrivilege`) exists for compatibility with tooling that genuinely needs it — but it requires the parent process to hold the privilege.

## uid0 — cosmetic root for legacy programs

A specific class of legacy programs hard-code `getuid() == 0` (or `geteuid() == 0`) checks to detect root and refuse to run otherwise. The programs may have legitimate logic that requires elevated privileges, or they may just be checking out of paranoia.

For these programs, Peios provides the **`uid0`** utility. It is a small wrapper that:

1. Runs as a user with `SeAssignPrimaryTokenPrivilege` (or chains through one).
2. Sets the calling credentials' `cred->uid`, `cred->euid`, and `cred->suid` all to 0.
3. Execs the target binary.

The result: the target binary sees `getuid() == 0`, satisfies its root check, and proceeds.

Crucially, **`uid0` does not change the KACS token**. The `current_fsuid()` patch (from [Credential projection](~peios/linux-compatibility/credential-projection)) ensures that file-related credential lookups still return the projected UID from the token — *not* the cosmetic 0. So `uid0` is purely a cosmetic adjustment for legacy "am I root?" checks; it doesn't grant any actual privileges or change the security-relevant identity.

The use case: a legacy script that does `[ $(id -u) -eq 0 ] || exit 1` at the top. The script's actual work might be perfectly fine to run as the calling user, but the check refuses. `uid0` makes the check pass.

The `uid0` utility itself is signed and runs with the appropriate privilege; an ordinary user invoking `uid0` does not gain root authority — they gain a cosmetic UID-0 view for the duration of the wrapped program. The KACS token is unchanged; the access decisions still flow through KACS.

This is the right way to handle the "is root?" check pattern. The check is satisfied; the actual authority comes from KACS; the legacy code path works.

## Comparison: setuid syscall, setuid bit, uid0

A handy summary:

| Mechanism | Caller needs | Effect on token | Effect on getuid() / geteuid() |
|---|---|---|---|
| `setuid(N)` without privilege | (none) | Unchanged | Unchanged (call returns 0 but doesn't actually set anything) |
| `setuid(N)` with privilege | `SeAssignPrimaryTokenPrivilege` | Full swap via authd | Reflects the new identity |
| `exec` of setuid-bit binary without privilege | (none) | Unchanged | euid/suid cosmetically updated to binary owner; uid unchanged |
| `exec` of setuid-bit binary with privilege | `SeAssignPrimaryTokenPrivilege` | Full swap to binary owner | Reflects new identity |
| `uid0` wrapper | The wrapper itself runs with the privilege | Unchanged | Cosmetic uid/euid/suid all = 0; `current_fsuid()` still returns projected UID |

The pattern: real identity changes are gated by the privilege and go through authd. Cosmetic changes (for legacy compatibility) don't require the privilege and don't touch the token.

## What setuid semantics are not

A few clarifications:

- **They are not a way to elevate privilege.** A program calling `setuid(0)` without the privilege does not gain root authority — the call is a no-op. To genuinely gain authority, you need a different token, which requires authd.
- **They are not the way Peios changes identity.** The setuid syscall is a compatibility layer. The native way to change identity is to be assigned a different token by authd (typically through a re-authentication or through being launched with a specific token by peinit).
- **They are not bypass mechanisms for KACS.** Whatever the setuid syscall does, the KACS access checks continue to operate against the token. There is no setuid combination that gets around a DACL.
- **They are not how login frontends actually work.** Login frontends do use `setuid()` (with the privilege), but the actual identity-establishment work is in authd — minting the token, setting up the session, applying the privileges and claims. The `setuid()` call is the final step that installs the result on the calling process.

The cleanest mental model: setuid is a Linux-compatibility veneer on the actual Peios identity machinery. The veneer is enough for legacy programs to think they're operating on Linux; the actual identity changes (when they happen) go through authd.

## Migrating away from setuid

For new code or refactored services, the cleaner pattern is to avoid setuid entirely:

- **Services should be launched with the right token from the start.** peinit fork-installs the correct token before exec; the service never needs to setuid.
- **User-facing operations should be done as the user, not via setuid-to-root.** Impersonation (capturing the user's token via peer-token capture) is the right pattern — the service can act on the user's behalf without changing its own identity.
- **Cross-identity work happens through IPC.** A service needing to do something as another identity sends an IPC request to a service running with that identity; the latter does the work.

Setuid is the legacy compatibility path. Native Peios code paths look different.
