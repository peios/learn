---
title: Linux compatibility
type: concept
description: Peios runs Linux software with little to no modification. The Linux identity APIs — getuid, getgid, capset, setuid — return values projected from the KACS model. Compatibility is best-effort; Peios does not carve out exceptions in KACS to accommodate Linux. This page covers how the projection works and where the compatibility boundary lies.
related:
  - peios/linux-compatibility/credential-projection
  - peios/linux-compatibility/dac-neutralization-and-capabilities
  - peios/linux-compatibility/setuid-and-uid0
  - peios/linux-compatibility/peer-credentials
  - peios/tokens/overview
  - peios/identity/overview
---

Peios runs Linux applications with little to no modification. The Linux identity APIs — `getuid`, `getgid`, `getgroups`, `setuid`, `setgid`, `capset`, `capget`, the credential xattr, the credential-bearing socket controls — all continue to work. Many programs built against the Linux ABI need no changes; they call the same syscalls, see the same return values, and observe semantics close enough to Linux that nothing breaks. Some programs need adjustments; a few cannot work at all on Peios without restructuring.

The boundary between "works as-is" and "needs work" comes from a single principle: **Peios does not carve out exceptions in the KACS model for Linux compatibility**. The compatibility layer is built on top of KACS; it does not bend KACS to fit Linux. When a Linux API can be satisfied by deriving the answer from KACS state — `getuid()` returns a UID computed from the token — that works cleanly. When a Linux API expects to *modify* state that KACS owns — `setuid()` expects to change the kernel's notion of the calling process's identity — the compatibility layer either no-ops (preserving the syscall's contract without actually changing KACS state) or routes the request through KACS-aware mechanisms (and only succeeds when the calling token has the appropriate KACS privileges).

The result is best-effort compatibility. The values Linux APIs return are **derived** from the KACS model, not parallel to it. The token is the authoritative identity; the Linux credentials are a projection of it. The Linux compatibility layer is the bridge between "what Linux applications expect" and "how Peios actually works" — but it is a bridge that respects KACS at every point. Where a Linux semantic conflicts with KACS, KACS wins; the Linux call gets the closest reasonable approximation.

This page covers the model: how the projection works, what the Linux APIs see, and where the compatibility boundary lies.

## The projection model in one sentence

**The token's identity is projected into Linux's UID/GID/capability fields, but only flows that direction — Linux APIs never write back to the token.**

A process's primary identity is the user SID on its token. The kernel computes a corresponding UID (via the directory's SID-to-UID mapping) and stores it as part of the token's projection state. When the process calls `getuid()`, the value returned is the projection. The kernel does not consult the actual `cred->uid` field that Linux usually uses for this; it consults the token.

The same applies to GID and supplementary GIDs. They are projections from the token, not authoritative on their own.

This is the **one-way** rule. Token → cred always; cred → token never. There is no API in the compatibility layer that lets Linux semantics override the token. A `setuid()` call either causes the token to change (via authd, on the rare paths where that is allowed) or does nothing. It does not write a new UID into the token.

## What you see vs what counts

A Linux process running on Peios sees:

- `getuid()`, `getgid()` return UID/GID values consistent with the token's projection.
- `getgroups()` returns supplementary GIDs from the projection.
- `stat()` on a file returns UID/GID values consistent with the file's owner SID (also projected).
- `/proc/<pid>/status` shows the token's projected UIDs and capabilities.
- `capget()` returns the mandatory capability substrate (covered in the capabilities page).

What the kernel actually uses for access decisions is the **token**, not what `getuid()` returns. If a process's token has user SID `S-1-5-21-...-1001` and that SID projects to UID 1001, then `getuid()` returns 1001 — but the access check uses the SID. The two values are kept consistent by the projection, but the SID is authoritative.

Tools that work this way include: `ls -l`, `ps`, `top`, `who`, anything that uses standard POSIX APIs to query identity and ownership. They all see the projection; the underlying KACS state is what actually controls access.

## What works, what changes

A handful of Linux behaviours map cleanly into KACS; others are deliberately redirected. Quick summary:

| Linux API | What Peios does |
|---|---|
| `getuid`, `getgid`, `getgroups` | Returns the projection from the token. |
| `setuid`, `setgid` | No-op without `SeAssignPrimaryTokenPrivilege`. With the privilege, becomes a full identity swap via authd. |
| `setuid`-on-exec (setuid bit) | Cosmetic euid change without privilege; full token swap with privilege. |
| `capget`, `capset` | Returns the kernel's mandatory capability substrate; `capset` cannot clear ALLOW bits. |
| `prctl(PR_CAPBSET_*)` | Operates on the capability substrate per the same rules. |
| `setfacl` / POSIX ACL xattrs | Unconditionally denied — KACS replaces POSIX ACLs. |
| `fchmod`, `chmod` | Denied on FACS-managed fds. Redirect through `kacs_set_sd`. |
| `fchown`, `chown` | Same. |
| `setcap` on files (file capabilities) | Denied. Linux file capabilities are dead under KACS. |
| `SO_PEERCRED`, `SCM_CREDENTIALS` | Returns projected UIDs (compat-only). Services needing real identity use `kacs_open_peer_token`. |
| `getxattr`/`setxattr` on `security.peios.sd` / `system.ntfs_security` | Denied; use `kacs_get_sd` / `kacs_set_sd`. |
| `auditd` and the Linux audit subsystem | Replaced by KMES and eventd. The legacy audit records projected UIDs only. |

The pattern: identity-querying APIs see the projection; identity-modifying APIs either no-op (preserving the Linux contract) or are redirected through KACS-aware paths.

## Why the compatibility layer exists

A reasonable question: why bother with Linux compatibility at all? Why not require applications to be rewritten?

The answer is operational: the ecosystem of Linux software is large. Forcing every application to be ported to a Peios-native API surface would be a barrier to adoption that the value of native integration does not justify. The compatibility layer lets most Linux software run with little or no modification.

The cost is the indirection of the projection — every `getuid()` consults the token rather than `cred->uid`, every `setuid()` is interpreted through the privilege model. The cost is small at runtime; the operational benefit is large.

The compatibility layer is **not** a translation layer. It does not "convert Linux access control to KACS"; KACS is what runs. The compatibility layer is the set of rules that make Linux APIs return sensible values when called on a system whose actual access control is KACS. Where a Linux behaviour cannot be satisfied without compromising KACS, the layer prefers approximation to special-casing — the Linux call returns something reasonable rather than the kernel making a KACS exception. This is why "best-effort" is the right framing: most things work, some things approximate, a few things require the application to be aware of the underlying model.

## DAC neutralization

A specific aspect of the compatibility layer worth flagging: the kernel sets every process up with a mandatory set of Linux capabilities — `CAP_DAC_OVERRIDE`, `CAP_DAC_READ_SEARCH`, `CAP_FOWNER`, `CAP_CHOWN`, `CAP_SETUID`, `CAP_SETGID` — that effectively neutralise the legacy Linux DAC checks.

The reason: Linux's traditional DAC (file mode bits, UID/GID checks) would otherwise run **before** the KACS LSM hooks. A Linux file mode of `400` (read-only by owner) would block a write attempt by a non-owner before KACS could evaluate the DACL. The mandatory capabilities tell the Linux DAC to defer to the LSM layer; KACS then makes the authoritative decision.

This is why the file's mode bits don't enforce access in Peios — DAC is neutralised. The mode is informational (derived from the SD); KACS is the authority.

The capability story is more nuanced than just "neutralise DAC"; it's covered in detail in [DAC neutralization and capabilities](~peios/linux-compatibility/dac-neutralization-and-capabilities).

## What about the `root` user

A common question: what about `root`? Linux's `root` is UID 0; programs that check `geteuid() == 0` to detect administrative privilege rely on this. On Peios, who is "root"?

The mapping is:

- The **SYSTEM** principal (`S-1-5-18`) projects to UID 0. Processes running on the SYSTEM token see `getuid()` return 0.
- A user in `BUILTIN\Administrators` (`S-1-5-32-544`) projects to their normal UID, typically non-zero. They are administratively privileged in KACS terms but `getuid()` does not return 0.
- The `uid0` utility lets a process *with* `SeAssignPrimaryTokenPrivilege` and the right authority cosmetically set its UID to 0 without changing the underlying token. Useful for legacy applications that hard-code `geteuid() == 0` checks but where the actual identity should remain non-SYSTEM.

The `uid0` mechanism is covered in [setuid and uid0](~peios/linux-compatibility/setuid-and-uid0). The short version: legacy "is this root?" checks see UID 0 when the calling code has explicitly arranged for them to; otherwise the real projection is what they see.

## Where to start

If you want the projection mechanism in detail — how the token's identity becomes UID/GID values, how the projection handles impersonation, how the kernel maintains consistency — read [Credential projection](~peios/linux-compatibility/credential-projection).

If you want the capability story — DAC neutralisation, the 41 Linux capabilities classified, why `security_capable()` is authoritative — read [DAC neutralization and capabilities](~peios/linux-compatibility/dac-neutralization-and-capabilities).

If you want setuid semantics and the `uid0` utility, read [setuid and uid0](~peios/linux-compatibility/setuid-and-uid0).

If you want peer credentials — `SO_PEERCRED`, `SCM_CREDENTIALS`, the rules for migrating Linux services to KACS-aware peer-identity APIs — read [Peer credentials](~peios/linux-compatibility/peer-credentials).
