---
title: Credential Projection
order: 1
---

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

Projected credentials reflect the process's primary token. They MUST NOT reflect impersonation state. When impersonation is active, `getuid()` and the KACS-evaluated identity may disagree. This is by design.

## Projected UIDs

Every token carries pre-computed projected UID/GID values, computed by authd at token creation time and stored on the token. KACS MUST NOT resolve SID-to-UID mappings at runtime.

> [!INFORMATIVE]
> Since SIDs are a single namespace but Linux UIDs and GIDs are separate namespaces, authd MUST allocate `uidNumber`/`gidNumber` values from a single unified counter across all principal types. This ensures every SID projects to a unique number regardless of which Linux namespace it lands in.
