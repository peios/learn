---
title: SID Format
order: 1
---

A Security Identifier (SID) is a variable-length binary value that uniquely identifies a principal -- a user, group, service, machine, or well-known entity. SIDs are the fundamental identity primitive in KACS. They appear in tokens (as identity), in Security Descriptors (as access rules), and as references throughout the system.

## Binary format

A SID is encoded as a contiguous binary structure (MS-DTYP section 2.4.2):

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 1 | Revision | MUST be 1. |
| 1 | 1 | SubAuthorityCount | Number of sub-authorities. MUST be between 0 and 15 inclusive. |
| 2 | 6 | IdentifierAuthority | A 6-byte big-endian value identifying the authority that issued the SID. |
| 8 | 4 × SubAuthorityCount | SubAuthority[] | Array of 32-bit unsigned integers in little-endian byte order. |

The total size of a SID in bytes is `8 + (4 × SubAuthorityCount)`. The minimum size is 8 bytes (zero sub-authorities). The maximum size is 68 bytes (15 sub-authorities).

The last sub-authority in a SID is the **Relative Identifier (RID)** -- the portion that distinguishes individual principals within a domain.

## String format

SIDs are represented in string form as:

```
S-1-{authority}-{sub1}-{sub2}-...-{subN}
```

Where:

- `S` is a literal prefix.
- `1` is the revision number.
- `{authority}` is the IdentifierAuthority. If the upper 2 bytes are zero, this is the decimal representation of the lower 4 bytes. Otherwise, it is a hexadecimal representation prefixed with `0x`.
- Each `{subN}` is the decimal representation of the corresponding 32-bit sub-authority.

> [!INFORMATIVE]
> Example SIDs: `S-1-5-18` (Local System), `S-1-5-32-544` (BUILTIN\Administrators), `S-1-5-21-3623811015-3361044348-30300820-1013` (a domain user).

## Comparison

Two SIDs are equal if and only if their binary representations are byte-for-byte identical. Comparison MUST be performed on the binary encoding, not the string form. There is no case sensitivity, normalization, or equivalence relation -- equality is exact binary match.

## SID_AND_ATTRIBUTES

Groups, restricted SIDs, device groups, and confinement capabilities are stored as SID_AND_ATTRIBUTES structures -- a SID paired with a 32-bit attributes field.

| Field | Type | Description |
|---|---|---|
| Sid | SID | The security identifier. |
| Attributes | u32 | Bitfield controlling how the SID participates in access evaluation. |

The following attribute flags are defined:

| Flag | Value | Description |
|---|---|---|
| SE_GROUP_MANDATORY | 0x00000001 | The group cannot be disabled via AdjustGroups. |
| SE_GROUP_ENABLED_BY_DEFAULT | 0x00000002 | The group is enabled when the token is created. |
| SE_GROUP_ENABLED | 0x00000004 | The group is currently enabled for access checking. Allow ACEs match only enabled groups. |
| SE_GROUP_OWNER | 0x00000008 | The group can be set as the default owner for new objects. |
| SE_GROUP_USE_FOR_DENY_ONLY | 0x00000010 | The group matches deny ACEs but not allow ACEs. Set permanently by FilterToken; cannot be reverted. |
| SE_GROUP_INTEGRITY | 0x00000020 | Used to identify an integrity level SID. |
| SE_GROUP_INTEGRITY_ENABLED | 0x00000040 | Used with SE_GROUP_INTEGRITY. |
| SE_GROUP_LOGON_ID | 0x40000000 | Identifies the logon SID -- the per-session SID generated at authentication time. Cannot be disabled. |
| SE_GROUP_RESOURCE | 0x20000000 | The group is a domain-local group from the resource domain. |

A group participates in allow-ACE matching only if SE_GROUP_ENABLED is set and SE_GROUP_USE_FOR_DENY_ONLY is not set. A group participates in deny-ACE matching if SE_GROUP_ENABLED is set OR SE_GROUP_USE_FOR_DENY_ONLY is set.
