---
title: Privilege catalog
type: reference
description: Where the per-privilege catalogue lives — the Peios Kernel TRM — and the two privileges that are enforced but unnamed.
related:
  - peios/constants-and-catalogs/overview
  - peios/privileges/overview
  - peios/privileges/categories
---

The per-privilege catalogue — every name, its LUID bit position, and what it does — is in the **Peios Kernel TRM §3.4.2**, "Catalogue". It is not duplicated here.

The conceptual treatment is [Privileges](~peios/privileges/overview), and the four-category model is [Categories](~peios/privileges/categories).

## Five privileges influence an access check

Only five can contribute bits to a granted mask, and therefore only five can appear in a `privilege-use` event:

- `SeSecurityPrivilege`
- `SeTakeOwnershipPrivilege`
- `SeBackupPrivilege`
- `SeRestorePrivilege`
- `SeRelabelPrivilege`

Any other bit fails the audit encoder closed rather than emitting an unnamed privilege. See the [Events Index §3.3](~peios/kernel-access-events/privilege-use).

## Two are enforced but not nameable

`SeTakeOwnershipPrivilege` and `SeRelabelPrivilege` are enforced by KACS but absent from the published privilege table, so they cannot be named in a service's `RequiredPrivileges`. A service needing either declares nothing and takes its source token's defaults, or fails to start if it tries to name one.

That asymmetry is peinit's, not the kernel's — see the peinit TRM §4.5.
