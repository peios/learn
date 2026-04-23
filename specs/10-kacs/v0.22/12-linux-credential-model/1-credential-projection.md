---
title: Credential Projection
---

## Compatibility model

Peios is its own operating system with its own security model. Because it is based on Linux, it supports Linux applications — but the compatibility shims in this section are designed to minimise total failure of unmodified Linux applications, not to ensure they operate securely. A Linux daemon that calls `setuid()` to drop privileges will not crash, but it also will not achieve privilege separation under KACS. The KACS token is unchanged; the UID change is cosmetic.

In production, Linux applications that require KACS-aware security behavior should be wrapped in custom shims that intercept security-sensitive syscalls and translate them to KACS token operations. The compatibility layer is a crash-prevention mechanism, not a security mechanism.

## Credential projection

KACS tokens are the sole identity-based authorization mechanism. Linux applications do not know tokens exist — they call `getuid()`, `getgid()`, `getgroups()`, read `/proc/self/status`, and assume the numbers they see determine their access rights. KACS projects token identity onto standard Linux credentials so unmodified applications function normally.

When a KACS token is installed on a process, the process's Linux credentials are set to match:

- The token's user SID maps to a UID via the directory's `uidNumber` attribute. If no `uidNumber` is set, the UID defaults to 65534 (nobody). No algorithmic mapping.
- The token's primary group SID maps to a GID via the directory's `gidNumber` attribute, with the same fallback.
- The token's group SIDs map to supplementary GIDs where `gidNumber` attributes exist.
- `getuid()`, `getgid()`, `getgroups()` return these projected values.
- `/proc/<pid>/status` reflects them.

## Consequences

- Under normal token projection, no process runs as UID 0 unless it holds the SYSTEM token (`S-1-5-18`).
- Home directories work naturally — `getpwuid(getuid())` returns the correct home directory because the UID is real and consistent with NSS/LDAP.
- Different services get different UIDs, providing incidental defense-in-depth alongside KACS enforcement.

## Projection is one-way

Token state flows into credential fields, never the reverse. The projected credentials are observational compatibility data; the token is the authority.

Projection reflects all groups regardless of their enabled/disabled state — AdjustGroups MUST NOT trigger projection recalculation.

Projected credentials reflect the **effective token** — which is the impersonated token during impersonation, or the primary token otherwise. When a service thread impersonates a client and creates a file, the file is owned by the client's projected UID, quotas are charged to the client, and audit is attributed to the client. This matches the Windows model where the impersonation token governs all operations during impersonation.

The `current_fsuid()` patch reads the projected UID from `current->cred` (the effective credential), which carries the effective token. During impersonation, this is the impersonated token's projected UID. After `kacs_revert`, it returns to the primary token's projected UID.

`getuid()` reads `current->real_cred->uid` (the primary credential's UID), which is always the primary token's projected UID regardless of impersonation. This means during impersonation: `getuid()` returns the service's UID, `current_fsuid()` returns the client's UID. This is the correct and intended behavior.

> [!INFORMATIVE]
> The `uid0` utility (see the setuid section) explicitly overrides `cred->uid` to 0 for legacy compatibility. In that case, `getuid()` returns 0 rather than the projected UID. `current_fsuid()` still returns the projected UID from the effective token — uid0 affects the Linux credential fields but not the KACS projection path.

## Projected UIDs

Every token carries pre-computed projected UID/GID values, computed by authd at token creation time and stored on the token. KACS MUST NOT resolve SID-to-UID mappings at runtime.

> [!INFORMATIVE]
> Since SIDs are a single namespace but Linux UIDs and GIDs are separate namespaces, authd MUST allocate `uidNumber`/`gidNumber` values from a single unified counter across all principal types. This ensures every SID projects to a unique number regardless of which Linux namespace it lands in.
