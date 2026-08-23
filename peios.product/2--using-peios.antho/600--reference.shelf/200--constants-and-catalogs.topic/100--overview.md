---
title: Constants and catalogs
type: reference
description: Where every numeric constant in Peios is catalogued — access rights and GenericMappings here, ACE types and well-known SIDs in PCDS, privileges in the kernel manual.
related:
  - peios/constants-and-catalogs/access-mask-bits
  - peios/constants-and-catalogs/other-constants
  - peios/constants-and-catalogs/privilege-catalog
  - peios/constants-and-catalogs/well-known-sids
---

Numeric constants — right bits, type values, enum members, limits — are catalogued in exactly one place each. This topic is either that place or a pointer to it.

## What lives here

| Page | Holds |
|---|---|
| [Access mask bits](~peios/constants-and-catalogs/access-mask-bits) | Per-object-type rights for files, processes, tokens, registry keys and services; the GenericMapping tables; the `*_ALL_ACCESS` and `STANDARD_RIGHTS_*` aggregates. |
| [Other constants](~peios/constants-and-catalogs/other-constants) | Impersonation levels, integrity levels, logon types, elevation types, PIP tiers, audit policy flags, create dispositions, `SECURITY_INFORMATION` flags, and the kernel's size limits. |

## What lives elsewhere

Three catalogues are owned by documents that also define their semantics, and are not duplicated here.

| Catalogue | Canonical home |
|---|---|
| ACE types, ACE flags, and their numeric values | PCDS §5.4 — see [ACE types and flags](~peios/constants-and-catalogs/ace-types-and-flags) |
| Well-known SIDs | PCDS §4.4 — see [Well-known SIDs](~peios/constants-and-catalogs/well-known-sids) |
| Every privilege, with its LUID bit | Peios Kernel TRM §3.4.2 — see [Privilege catalog](~peios/constants-and-catalogs/privilege-catalog) |

The three pages above are signposts. Following one gets you to the table.

> [!NOTE]
> A constant with two spellings is listed under the name you would meet it by. Where a header and a specification disagree — and they do, for impersonation levels, create dispositions and the group attribute flags — the page says so and names both. The full mapping is the Peios Kernel TRM §3.A.

## Related catalogues

- Every **event type** the system emits: the [Peios Events Index](~peios/all-event-types).
- Every **audit event's payload schema**: the same book, chapters 3 to 8.
