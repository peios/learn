---
title: setuid Behaviour
description: Under KACS a UID has no security properties — what the setuid syscalls do, what the setuid bit does at exec, and the compatibility gaps that remain.
---

Under KACS a UID has no security properties whatever. It is not
consulted in any access decision, appears in no descriptor, and is
referenced by no ACE. It is a compatibility value stored in
`struct cred` for the sole purpose of answering `getuid()`.

## The setuid syscalls

The `setuid` family — `setuid`, `setgid`, `setresuid`, `setresgid`,
`setgroups` — changes Linux credentials.

**Without `SeAssignPrimaryTokenPrivilege`**, which is the common case,
the call is a silent no-op. It returns success, and every credential
field is restored from the old credential: UIDs, GIDs, supplementary
groups, capabilities. Neither the credential nor the token changes,
and the process's authority before and after is identical.

The silent success preserves consistency between the visible UID and
the KACS identity. Changing the UID without changing the token would
produce subtle failures — the wrong home directory from `getpwuid()`,
for instance — for no security benefit.

**With `SeAssignPrimaryTokenPrivilege`** the design calls for the
credential change to trigger a full identity swap, redirected to authd
to obtain a token for the target UID's principal, so that both token
and credential change together.

That is not what happens. A caller holding the privilege receives
`EOPNOTSUPP` and the call **fails**. There is no authd redirect
anywhere in the LSM. The practical effect is that the privileged path
is unavailable rather than dangerous: a TCB component cannot change
identity this way, and has to install a token directly instead
(§3.2.3).

## The setuid bit on exec

The filesystem setuid bit tells the kernel to change the effective UID
to the file owner's on exec.

**Without the privilege**, the Linux-visible UID and GID slots change
to the file owner's identity while the token is untouched — a cosmetic
escalation in which the process sees `geteuid() == 0` while KACS
continues to enforce the original token. Concretely `uid` and `suid`
are set from `euid`, the GID counterparts mirror that, `fsuid` and
`fsgid` are carried over unchanged from the old credential, and the
token is cloned as-is.

**With the privilege**, the design calls for the slots *and* the token
to change — genuine escalation. As with the syscall, this is not
implemented: an exec that would change UID or GID under a token
holding `SeAssignPrimaryTokenPrivilege` returns `EOPNOTSUPP` and the
exec fails.

The asymmetry between the two mechanisms is intentional in the design.
`setuid()` is de-escalation, so leaving everything unchanged is the
safe failure mode. The setuid bit is escalation, and the target binary
expects the euid and will check it — `sudo` verifies
`geteuid() == 0` — so the euid has to change for the binary to
function at all.

| Mechanism | With privilege | Without privilege |
|---|---|---|
| `setuid()` syscall | Designed: all UIDs and token change. Actual: fails with `EOPNOTSUPP`. |  Silent no-op |
| Setuid bit on exec | Designed: euid/suid and token change. Actual: exec fails with `EOPNOTSUPP`. | euid/suid change, token unchanged |

## The current_fsuid patch

The kernel calls `current_fsuid()` whenever it needs a UID for a
filesystem operation — file creation ownership, quota tracking,
keyring lookup, NFS credentials. KACS redefines it, along with
`current_fsgid()` and `current_fsuid_fsgid()`, to return the projected
value from the effective token rather than `cred->fsuid`.

So files are created owned by the projected UID, quotas track against
it, per-user keyrings are keyed by it, and an NFS server sees the real
identity rather than UID 0.

## Compatibility gaps

**The privilege-drop pattern.** A daemon that calls `setuid(target)`
and then checks `getuid() != target` to confirm the drop sees success
returned with the UID unchanged. This is intentional — UIDs carry no
security meaning here — and software ported to Peios should use
KACS-native token operations for privilege management instead.

**Direct capability manipulation.** Software that manipulates
capabilities with `capset()` and `capget()`, writes seccomp filters,
or inspects its own capability set may behave unexpectedly (§3.10.2).

**`setfsuid()`** is a no-op for filesystem purposes, since
`current_fsuid()` ignores `cred->fsuid`; and cosmetic setuid-bit exec
transitions do not flow into the projected values either.

**`access()` and `faccessat()`** use the effective token rather than
the real credential — the entire native credential-override machinery
those calls normally use is compiled out. The concept of a "real
identity" separate from the acting one does not exist in KACS.

**`SO_PEERCRED`** returns projected UIDs rather than token
information, and because the switchboard allows `CAP_SETUID`, cosmetic
UID forgery in `SCM_CREDENTIALS` is possible. Both are Linux
compatibility metadata, not peer-token authorities: a service needing
authoritative identity uses stream or seqpacket peer-token capture, or
explicit token descriptor passing (§3.5.3).

**Legacy `auditd`** records projected UIDs, so KACS audit through KMES
replaces Linux audit for security-relevant logging.

A `uid0` utility — running a program with `cred->uid` forced to 0 for
legacy programs that refuse to start otherwise — is described in the
design and does not exist in the tree. The kernel-side guarantee it
would rely on does hold: `current_fsuid()` ignores `cred->uid`
entirely, so even with such a utility active, filesystem operations
would use the projected UID and files would be owned by the real user.
