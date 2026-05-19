---
title: Constants and catalogs
type: reference
description: The numeric constants, named values, and lookup tables that appear throughout the KACS surface — well-known SIDs, privilege LUIDs, ACE types and flags, access mask bits per object type, mitigation flags, mount policy values, error codes. This page is the map.
related:
  - peios/constants-and-catalogs/well-known-sids
  - peios/constants-and-catalogs/privilege-catalog
  - peios/constants-and-catalogs/ace-types-and-flags
  - peios/constants-and-catalogs/access-mask-bits
  - peios/constants-and-catalogs/other-constants
  - peios/kernel-abi-reference/overview
---

KACS uses many fixed numeric values — well-known SIDs, ACE type values, access right bit positions, privilege LUIDs, integrity levels, error codes, magic numbers. This topic catalogues all of them in one place.

The constants are documented in their conceptual context elsewhere — well-known SIDs in [Identity](~peios/identity/well-known-principals), privileges in [Privileges](~peios/privileges/overview), ACE types in [ACLs, ACEs, and access masks](~peios/security-descriptors/acls-and-aces), and so on. This topic is the reference: when you want to look up "what's the LUID bit for `SeBackupPrivilege`?" or "what's the access right value for `PROCESS_VM_READ`?", this is the place.

## What's in this reference

The catalogue is split into five pages:

| Page | Contents |
|---|---|
| [Well-known SIDs](~peios/constants-and-catalogs/well-known-sids) | Every SID that has fixed value, organised by authority. Universal SIDs, NT Authority SIDs, BUILTIN aliases, integrity labels, PIP trust labels, confinement and capability SIDs. |
| [Privilege catalog](~peios/constants-and-catalogs/privilege-catalog) | All privilege names with their LUID bit positions and categorical classification. |
| [ACE types and flags](~peios/constants-and-catalogs/ace-types-and-flags) | The 21 ACE type values, the AceFlags bits, the inheritance flag combinations. |
| [Access mask bits](~peios/constants-and-catalogs/access-mask-bits) | Per-object-type catalogues of access mask bits — file, process, token, plus standard rights, special rights, generic rights, and GenericMapping tables. |
| [Other constants](~peios/constants-and-catalogs/other-constants) | Mitigation flags, mount policy values, integrity levels, impersonation levels, logon types, error codes, magic numbers, sizes and limits. |

## Conventions

A few conventions apply across the catalogues:

**Hex for bit values.** Bit-flag values are written in hex (`0x0001`, `0x000F01FF`). This makes the bit positions obvious — the bit count from the LSB equals the log2 of the value for single-bit flags.

**Decimal for numeric IDs and counts.** SID sub-authority values, integrity RIDs, etc. are written in decimal to match how they appear in tools and logs.

**Names in code style.** Constants are named like `SE_GROUP_MANDATORY` or `FILE_READ_DATA`; this page renders them in code style for consistency with the syscall and ABI references.

## Pre-defined value ranges

Some value ranges are pre-allocated for KACS:

| Range | Use |
|---|---|
| Syscall numbers 1000–1027 | KACS-specific syscalls |
| Ioctl magic `'K'` (0x4B) | Token ioctls |
| SID sub-authority `S-1-5-21-*` | Domain-allocated SIDs |
| SID sub-authority `S-1-5-32-*` | BUILTIN aliases |
| SID sub-authority `S-1-16-*` | Integrity labels |
| SID sub-authority `S-1-19-*` | PIP trust labels |
| SID sub-authority `S-1-15-2-*` | Confinement domains |
| SID sub-authority `S-1-15-3-*` | Capabilities |

These ranges are stable. Numbers within each range are also stable once assigned. Additions go to the next available slot within the range.

## Reserved values

A handful of values are reserved for future use:

- Privilege LUIDs that have catalogue names but no implementation in v0.20 (`SeCreateGlobalPrivilege`, `SeCreatePagefilePrivilege`, etc. — see [Privilege catalog](~peios/constants-and-catalogs/privilege-catalog)).
- Capability SID sub-authorities `S-1-15-3-4` through `S-1-15-3-7` — reserved.
- The `Isolated` PIP type (1024) — reserved; no v0.20 signing key targets it.
- The `UI_ACCESS` mitigation flag (0x010) — reserved.
- Ace type 0x04 (`ACCESS_ALLOWED_COMPOUND`) — reserved.
- Several SD control flags with no v0.20 semantics.

Reserved values appear in the catalogues with a note. They are not currently used; future versions may give them meaning.

## Where the constants come from

The numeric values are decided at three levels:

- **Spec-level.** Values like ACE type values, SID format constants, access mask bit positions are part of the documented KACS specification. They are stable for v0.20 and will not change.
- **Kernel-implementation-level.** Values like syscall numbers and ioctl numbers are part of the kernel's ABI; they are stable as long as the kernel is.
- **Catalogue-level.** Some values (PIP catalogue entries, BUILTIN alias RIDs) are conventional — they could in principle be different but everyone agrees on these specific numbers.

The pages in this reference document all three levels uniformly. When a value is changed-able (the catalog could grow with new entries) vs frozen (the value is what it is), the relevant page calls out the distinction.

## Versioning

The constants documented here are stable for the v0.20 line. Future versions may:

- Add new constants (new privileges, new well-known SIDs, new mitigation flags).
- Promote reserved values to defined values.
- Add new entries to per-object-type access-mask catalogues.

Future versions will not:

- Renumber existing constants.
- Change the meaning of an existing constant.
- Remove constants (deprecated values become reserved-and-unused rather than reused).

Consumers should treat the catalogues as additive — code that uses a value defined here today will continue to work in future versions, and additional values are something the code should be tolerant of (ignore unknown enum values rather than crashing).
