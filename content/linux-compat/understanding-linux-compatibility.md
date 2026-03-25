---
title: Understanding Linux Compatibility
type: concept
order: 10
description: How Peios projects Linux credentials from tokens and neutralizes DAC so the token-based security model governs all access.
---

Peios uses the Linux kernel as its base. Many Linux applications run on Peios without modification. But Peios's security model is fundamentally different from Linux's — tokens and security descriptors replace UIDs and mode bits. This page explains how the two coexist.

## UIDs have no security meaning

On Peios, the **token** is the sole identity for all access decisions. UIDs, GIDs, and Linux capabilities play no role in access control. The kernel does not check UIDs when a process opens a file, sends a signal, or performs any other operation. AccessCheck evaluates the token against the security descriptor — UIDs are not part of that evaluation.

UIDs still exist because the Linux kernel ABI requires them. Applications call `getuid()` and expect a number. `/proc/<pid>/status` contains UID fields. `stat()` returns an owner UID on files. These values are populated, but they are **observational compatibility data**, not security properties.

## Credential projection

When a token is installed on a process, Peios **projects** Linux credentials from it:

- The token's user SID maps to a UID via the directory's `uidNumber` attribute
- The token's primary group SID maps to a GID via the `gidNumber` attribute
- The token's group SIDs map to supplementary GIDs where mappings exist
- `getuid()`, `getgid()`, `getgroups()` return these projected values

The projected UID is real and consistent — `getpwuid(getuid())` returns the correct home directory, and processes running under different service accounts get different UIDs. But the UID does not determine what the process can do. Two processes with different UIDs but the same token have identical authority.

## DAC neutralization

Linux evaluates its own access control (DAC — discretionary access control based on UIDs, GIDs, and mode bits) **before** consulting the LSM hooks where Peios enforces its security model. If Linux DAC denies an operation, the LSM hook never fires — Peios cannot override a DAC denial.

To prevent Linux DAC from interfering, Peios gives all processes a full set of Linux capabilities in their credentials. This ensures the kernel's initial UID-based permission checks pass and reach the LSM hooks, where Peios evaluates the token against the security descriptor.

The capabilities themselves are not real authority. Peios intercepts each capability check and either allows it (for capabilities that bypass DAC checks that Peios enforces via other hooks) or maps it to a specific Peios privilege. A process that appears to have `CAP_SYS_ADMIN` in its Linux credentials does not actually have unrestricted system administration access — the Peios privilege check determines whether the operation is allowed.

## What setuid() does

Linux applications sometimes call `setuid()` to change their identity — typically to drop privileges after initialization. Under Peios, this call is a **silent no-op** for most processes. It returns success but does not change anything — neither the Linux credential nor the Peios token.

This is safe because UIDs have no security properties. Whether or not the UID changes, the token — the sole authority for all access decisions — is unchanged. A process that calls `setuid(nobody)` and gets a no-op retains exactly the same authority as it would if the UID had actually changed.

For the rare TCB processes that hold `SeAssignPrimaryTokenPrivilege`, a `setuid()` call triggers a full identity swap — the token and the Linux credentials both change. This path exists for trusted system services that need to perform genuine identity transitions.

## What this means in practice

- Applications that call `getuid()` get a sensible number
- Applications that check `getuid() == 0` to refuse running as root see a non-zero UID (unless the process holds the SYSTEM token)
- Home directories, file ownership in `stat()`, and `/proc` entries all show consistent projected values
- Applications that rely on UIDs for access control decisions are making decisions based on data that has no security meaning — but in practice this is harmless, because the kernel enforces access through tokens regardless

Linux compatibility is best-effort. The security model is not negotiable — compatibility is. Most unmodified Linux applications work. Some behave differently because their assumptions about UID semantics are no longer true. Where this causes problems, the solution is Peios-native configuration or application-level workarounds.
