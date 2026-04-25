---
title: setuid Behaviour
---

Under KACS, UIDs have zero security properties. The UID is not consulted during any access control decision. It does not appear in any Security Descriptor. No ACE references a UID. The UID is a compatibility value stored in `struct cred` for the sole purpose of answering `getuid()` calls.

## The setuid() syscall

The `setuid()` family (`setuid`, `setgid`, `setresuid`, `setresgid`, `setgroups`) change Linux credentials. Under KACS:

**Without SeAssignPrimaryTokenPrivilege (common case):** the call is a silent no-op. It returns 0 (success) but nothing changes — neither the Linux credential nor the KACS token. The process's authority before and after the call is identical.

**With SeAssignPrimaryTokenPrivilege (rare, TCB-only):** the credential change triggers a full identity swap. The call is intercepted and redirected to authd, which obtains a token for the target UID's corresponding principal. Both the KACS token and the Linux credential change — a genuine identity transition.

> [!INFORMATIVE]
> The silent no-op preserves consistency between the process's visible UID (`getuid()`) and its KACS identity. Changing the UID without changing the token would cause subtle failures (wrong home directory from `getpwuid()`) without providing any security benefit.

## The setuid bit on exec

The filesystem setuid bit tells the kernel to change the process's effective UID to the file owner's UID on exec. Under KACS:

**With SeAssignPrimaryTokenPrivilege:** the euid/suid change to the file owner's UID AND the KACS token swaps to the corresponding identity. Genuine privilege escalation.

**Without SeAssignPrimaryTokenPrivilege:** the euid/suid change to the file owner's UID but the KACS token is unchanged. Cosmetic escalation — the process sees `geteuid() == 0` but KACS continues to enforce the original token.

This differs from the `setuid()` syscall (which is a no-op without the privilege). The difference is intentional:

- `setuid()` is deescalation. Keeping everything unchanged is the safe failure mode.
- The setuid bit is escalation. The target binary expects the euid and will verify it (e.g., `sudo` checks `geteuid() == 0`). The euid MUST change for the binary to function.

| Mechanism | With privilege | Without privilege |
|---|---|---|
| `setuid()` syscall | All UIDs + token change | Silent no-op |
| Setuid bit on exec | euid/suid + token change | euid/suid change, token unchanged |

## The current_fsuid() patch

The kernel calls `current_fsuid()` whenever it needs the UID for filesystem operations (file creation ownership, quota tracking, keyring lookup, NFS credentials). KACS redefines this function to return the projected UID from the token instead of `cred->fsuid`.

This ensures:

| Subsystem | Effect |
|---|---|
| File creation | Files owned by projected UID. |
| Disk quotas | Quotas track against projected UID. |
| Kernel keyring | Per-user keyrings keyed by projected UID. |
| NFS client | Server sees real identity, not UID 0. |

## The uid0 utility

`uid0` is a Peios utility that runs a program as UID 0. It sets `cred->uid`, `cred->euid`, and `cred->suid` to 0, then execs the target. The program's `getuid()` returns 0. The KACS token is unaffected.

This exists solely for legacy programs that check `getuid() == 0` and refuse to run otherwise. Because UIDs carry no authorization meaning, changing the UID is not a security operation.

The `current_fsuid()` patch ensures that even with uid0 active, filesystem operations use the projected UID from the token. Files are owned by the real user, not UID 0.

## Compatibility gaps

The following cases are not fully handled by the compatibility mechanisms:

- **Privilege-drop pattern.** Daemons that call `setuid(target)` then check `getuid() != target` to verify the drop succeeded will see success returned but the UID unchanged. This is intentional — UIDs carry no security meaning under KACS. Software ported to Peios SHOULD use KACS-native token operations for privilege management rather than the setuid-based pattern.
- Software that directly manipulates capabilities (`capset()`/`capget()`), writes seccomp filters, or inspects its own capability set MAY behave unexpectedly.
- `setfsuid()` becomes a no-op for filesystem purposes — `current_fsuid()` ignores `cred->fsuid`.
- `access()` / `faccessat()` uses the effective token (not the real credential). The concept of "real identity" does not exist in KACS.
- `SO_PEERCRED` returns projected UIDs, not token information. The capability switchboard allows CAP_SETUID, permitting cosmetic UID forgery in `SCM_CREDENTIALS`.
- Legacy `auditd` records projected UIDs. KACS audit (via KMES) MUST replace Linux audit for security-relevant logging.
