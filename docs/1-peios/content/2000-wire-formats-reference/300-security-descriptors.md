---
title: Security descriptors
type: reference
description: The self-relative binary format used to encode security descriptors everywhere they cross the kernel boundary. This page covers the SD header, the layout-relevant control-flag interactions, ACL and ACE binary layouts, and the access mask byte layout.
related:
  - peios/wire-formats-reference/overview
  - peios/wire-formats-reference/conditional-ace-bytecode
  - peios/security-descriptors/overview
  - peios/security-descriptors/acls-and-aces
  - peios/constants-and-catalogs/overview
---

A security descriptor in wire form uses the **self-relative** layout — a single contiguous byte buffer with the components (owner, group, DACL, SACL) stored at offsets specified in the header. The format is self-contained: no external pointers, no fixup needed on transport.

This page covers the byte-level layout. The conceptual model of SDs is in [Security descriptors](~peios/security-descriptors/overview); this page is the parser/encoder reference.

All multi-byte integers are little-endian on x86_64.

## SD header

Every SD starts with a 20-byte header:

| Offset | Size | Field | Meaning |
|---|---|---|---|
| 0 | 1 | `Revision` | `0x01` for v0.20. |
| 1 | 1 | `Sbz1` | Reserved; must be 0 unless `SE_RM_CONTROL_VALID` is set (in which case this is the resource-manager control byte, opaque to KACS). |
| 2 | 2 | `Control` | Flags; see below. |
| 4 | 4 | `OffsetOwner` | Offset (from SD start) to the owner SID. 0 if absent. |
| 8 | 4 | `OffsetGroup` | Offset to the primary group SID. 0 if absent. |
| 12 | 4 | `OffsetSacl` | Offset to the SACL. 0 if absent. |
| 16 | 4 | `OffsetDacl` | Offset to the DACL. 0 if absent. |

Total: 20 bytes. Variable-length component data follows.

### Control flags (16 bits)

The `Control` field is a bitmask of 16 `SE_*` flags. The canonical bit-by-bit catalogue is in [ACE types and flags](~peios/constants-and-catalogs/ace-types-and-flags) — this page does not re-tabulate it.

Bit interactions worth noting for the parser/encoder:

- `SE_DACL_PRESENT` (0x0004) = 0 means NULL DACL (grant all). `SE_DACL_PRESENT` = 1 with zero ACEs in the DACL means empty DACL (grant none).
- `SE_SELF_RELATIVE` (0x8000) must be set on any SD passed across the kernel boundary. An SD without it would be in absolute (pointer-based) format, which is not valid on the wire.
- `SE_RM_CONTROL_VALID` (0x4000) changes the meaning of the `Sbz1` header byte — it becomes the resource-manager control byte instead of a must-be-zero reserved byte.
- `SE_SERVER_SECURITY` (0x0080) is fail-closed in v0.20 — SDs with this flag set are rejected.

### Offsets

The four offsets (`OffsetOwner`, `OffsetGroup`, `OffsetSacl`, `OffsetDacl`) point into the buffer from the SD's start. An offset of 0 means the component is absent.

The kernel validates:

- All non-zero offsets must point within the SD buffer.
- Each component must fit within the SD buffer.
- Components must not overlap each other or the header.
- Absent components must have offset 0 and the corresponding PRESENT control flag clear (for DACL/SACL).

Components are typically laid out in a stable order (header, owner SID, group SID, SACL, DACL) but the format allows any non-overlapping arrangement.

## SID encoding

SIDs in the SD (owner, group, ACE SIDs) use the standard binary SID form — 8 + 4 × SubAuthorityCount bytes, big-endian authority, little-endian sub-authorities. The canonical layout is in the [wire formats overview](~peios/wire-formats-reference/overview), under "SIDs in wire format".

## ACL encoding

A DACL or SACL has an 8-byte header followed by ACEs:

| Offset | Size | Field | Meaning |
|---|---|---|---|
| 0 | 1 | `AclRevision` | `0x02` (basic) or `0x04` (DS — supports object/callback ACEs). |
| 1 | 1 | `Sbz1` | Reserved; 0. |
| 2 | 2 | `AclSize` | Total ACL size in bytes (header + ACEs). Max 64 KB. |
| 4 | 2 | `AceCount` | Number of ACEs. |
| 6 | 2 | `Sbz2` | Reserved; 0. |

After the header, `AceCount` ACEs are packed back-to-back without padding (each ACE's `AceSize` is a multiple of 4 bytes).

## ACE encoding

Every ACE starts with a 4-byte header:

| Offset | Size | Field |
|---|---|---|
| 0 | 1 | `AceType` |
| 1 | 1 | `AceFlags` |
| 2 | 2 | `AceSize` (multiple of 4) |

The body's shape depends on `AceType`.

### AceType values and AceFlags

The full catalogue of `AceType` values and `AceFlags` bits is in [ACE types and flags](~peios/constants-and-catalogs/ace-types-and-flags) — this page does not re-tabulate the values. For parsing, only the mapping from type to **body shape** matters:

| Body shape | AceType values |
|---|---|
| Single-SID | 0x00–0x03, 0x11, 0x13, 0x14 |
| Single-SID + claim entry | 0x12 |
| Object | 0x05–0x08 |
| Callback (single-SID + expression) | 0x09, 0x0A, 0x0D, 0x0E |
| Callback object | 0x0B, 0x0C, 0x0F, 0x10 |
| (reserved) | 0x04 |

The `AceFlags` byte carries inheritance and audit-firing flags; it does not affect the body layout.

### Single-SID ACE body

For ACE types 0x00–0x03, 0x11, 0x12, 0x13, 0x14:

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | Header (AceType, AceFlags, AceSize) |
| 4 | 4 | `Mask` |
| 8 | variable | `SID` (binary form, consumes remainder of ACE) |

For `SYSTEM_RESOURCE_ATTRIBUTE_ACE` (0x12), the SID is always `S-1-1-0` (Everyone), and additional ApplicationData (one claim entry) follows. The claim entry format is in [Token and session specs](~peios/wire-formats-reference/token-and-session-specs).

### Object ACE body

For ACE types 0x05–0x08:

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | Header |
| 4 | 4 | `Mask` |
| 8 | 4 | `Flags` (bit 0x01 = ObjectType present; bit 0x02 = InheritedObjectType present) |
| 12 | 16 | `ObjectType` GUID (if `Flags & 0x01`) |
| 28 | 16 | `InheritedObjectType` GUID (if `Flags & 0x02`) |
| variable | `SID` | |

GUID fields are present only when the corresponding flag bit is set. If both are absent, the SID starts at offset 12; if only ObjectType is present, SID starts at 28; etc.

### Callback ACE body (non-object)

For ACE types 0x09, 0x0A, 0x0D, 0x0E:

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | Header |
| 4 | 4 | `Mask` |
| 8 | variable | `SID` |
| variable | variable | `ApplicationData` (conditional ACE bytecode) |

The ApplicationData consumes the rest of the ACE after the SID. The format starts with the four magic bytes `0x61 0x72 0x74 0x78` ("artx") and contains conditional ACE bytecode — see [Conditional ACE bytecode](~peios/wire-formats-reference/conditional-ace-bytecode).

### Callback object ACE body

For ACE types 0x0B, 0x0C, 0x0F, 0x10: same as object ACE plus trailing ApplicationData.

## Access mask layout

The 32-bit access mask used in every ACE:

| Bits | Region | Examples |
|---|---|---|
| 0–15 | Object-specific rights | `FILE_READ_DATA`, `PROCESS_TERMINATE`, `TOKEN_QUERY`, etc. (16 type-specific bits) |
| 16–20 | Standard rights | `DELETE` (0x10000), `READ_CONTROL` (0x20000), `WRITE_DAC` (0x40000), `WRITE_OWNER` (0x80000), `SYNCHRONIZE` (0x100000) |
| 21–23 | Reserved | Must be 0 |
| 24 | `ACCESS_SYSTEM_SECURITY` | 0x01000000 |
| 25 | `MAXIMUM_ALLOWED` | 0x02000000 |
| 26–27 | Reserved | Must be 0 |
| 28–31 | Generic rights | `GENERIC_ALL` (0x10000000), `GENERIC_EXECUTE` (0x20000000), `GENERIC_WRITE` (0x40000000), `GENERIC_READ` (0x80000000) |

This region layout is canonical here; the *values* of the named rights, and the per-object-type catalogues for bits 0–15, are in [Access mask bits](~peios/constants-and-catalogs/access-mask-bits).

The generic bits are expanded at evaluation time via the object type's GenericMapping table. They never appear in stored SDs as final rights; the kernel maps them before walking.

## Limits

The format's own field widths impose the limits: max SD size 65,535 bytes, max ACL size 64 KB (16-bit `AclSize`), SIDs 8–68 bytes, ACE sizes a multiple of 4 bytes. The consolidated limits catalogue is in [Other constants](~peios/constants-and-catalogs/other-constants). The kernel rejects SDs that exceed these limits or have malformed internal sizes with `-EINVAL`.

## Self-relative round trips

Because the format is self-contained and has no embedded pointers, an SD blob can be:

- Stored verbatim in an xattr.
- Sent over the wire (a domain controller replicating an SD to a member system).
- Backed up byte-for-byte and restored.

The validation rules are also self-contained — the kernel can validate an SD without external state. The same blob is valid on every Peios system, regardless of the deployment.

This is the property that makes SDs portable. They are not "for this machine"; they are universally interpretable.
