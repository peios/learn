---
title: Binary Format
description: The variable-length SID — revision, identifier authority, and up to fifteen sub-authorities, with the size limits that bound it.
---

A SID (Security Identifier) is a variable-length binary value that
uniquely identifies a principal — a user, group, service, machine, or
well-known entity. SIDs are the fundamental identity primitive of the
Peios security model: they appear in tokens as identity, in security
descriptors as access rules, and as references throughout the system.

A SID is encoded as a contiguous binary structure with the following
layout:

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 1 | Revision | MUST be 1. |
| 1 | 1 | SubAuthorityCount | Number of sub-authorities. MUST be between 0 and 15 inclusive. |
| 2 | 6 | IdentifierAuthority | A 6-byte big-endian value identifying the authority that issued the SID. |
| 8 | 4 × SubAuthorityCount | SubAuthority[] | Array of 32-bit unsigned integers in little-endian byte order. |

The total size of a SID in bytes is `8 + (4 × SubAuthorityCount)`.
The minimum size is 8 bytes (zero sub-authorities). The maximum size
is 68 bytes (15 sub-authorities).

The last sub-authority in a SID is the **Relative Identifier (RID)**
— the portion that distinguishes individual principals within a
domain.

> [!NOTE]
> The IdentifierAuthority is the one big-endian field among the
> structures in this document — an MS-DTYP inheritance. The
> sub-authorities that follow it are ordinary little-endian integers.
