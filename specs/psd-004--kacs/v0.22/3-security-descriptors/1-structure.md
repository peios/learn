---
title: SD Structure
---

A Security Descriptor (SD) defines the complete security policy for a protected object. Every protected object in Peios -- every file, registry key, IPC endpoint, service, token, and process -- MUST have exactly one Security Descriptor. An object MUST NOT carry multiple SDs; the SD is the single authoritative security policy for the object.

An SD has four components and a set of control flags:

- **Owner SID** — the principal that owns the object. The owner has implicit rights (READ_CONTROL and WRITE_DAC) unless suppressed by an OWNER RIGHTS ACE.

- **Group SID** — a primary group associated with the object. Stored and returned on query, used during CREATOR GROUP substitution during inheritance, but no access control decision depends on it directly.

- **DACL** (Discretionary Access Control List) — an ordered list of ACEs that define who is allowed or denied access. The object's owner controls the DACL (via WRITE_DAC).

- **SACL** (System Access Control List) — an ordered list of ACEs that define system-level policy. Despite the name, the SACL carries several distinct ACE types:
  - Audit ACEs — which access attempts to log.
  - Mandatory label ACE — the object's integrity level for MIC.
  - Resource attribute ACEs — name-value attributes for conditional ACE evaluation.
  - Scoped policy ID ACEs — references to central access policies.
  - Process trust label ACE — the object's PIP trust level.

  Modifying the SACL requires ACCESS_SYSTEM_SECURITY, which in turn requires SeSecurityPrivilege.

Both the DACL and SACL use the standard binary ACL format defined in the ACL Format section.

## Binary format

SDs use the self-relative binary format defined in MS-DTYP section 2.4.6. The format is a 20-byte header followed by the owner SID, group SID, SACL, and DACL at offsets specified in the header.

| Offset | Size | Field |
|---|---|---|
| 0 | 1 | Revision (MUST be 1) |
| 1 | 1 | Reserved. Preserved for format compatibility but not interpreted by KACS. When SE_RM_CONTROL_VALID is set in the control flags, this byte carries resource manager control bits defined by the originating system. |
| 2 | 2 | Control flags (little-endian) |
| 4 | 4 | Offset to owner SID (little-endian, 0 if absent) |
| 8 | 4 | Offset to group SID (little-endian, 0 if absent) |
| 12 | 4 | Offset to SACL (little-endian, 0 if absent) |
| 16 | 4 | Offset to DACL (little-endian, 0 if absent) |

The self-relative format packs everything into a contiguous byte buffer with no pointers. This makes it suitable for storage (xattrs, database fields) and wire transmission (IPC, SMB).

KACS MUST use the self-relative format exclusively.

## Control flags

The SD's 16-bit Control field records metadata about the descriptor:

| Flag | Bit | Value | Description |
|---|---|---|---|
| SE_OWNER_DEFAULTED (OD) | 0 | 0x0001 | The owner was established by default means. |
| SE_GROUP_DEFAULTED (GD) | 1 | 0x0002 | The group was established by default means. |
| SE_DACL_PRESENT (DP) | 2 | 0x0004 | A DACL is present. If clear, AccessCheck treats the DACL as null (grants all access). |
| SE_DACL_DEFAULTED (DD) | 3 | 0x0008 | The DACL was established by default means. |
| SE_SACL_PRESENT (SP) | 4 | 0x0010 | A SACL is present. |
| SE_SACL_DEFAULTED (SD) | 5 | 0x0020 | The SACL was established by default means. |
| SE_DACL_TRUSTED (DT) | 6 | 0x0040 | Reserved. Preserved during round-trip serialization. No operational semantics in v0.22. |
| SE_SERVER_SECURITY (SS) | 7 | 0x0080 | When set on a creator SD, the inheritance algorithm appends server ACEs from the caller's primary token's default DACL. See the inheritance section. |
| SE_DACL_AUTO_INHERIT_REQ (AR) | 8 | 0x0100 | Requests that the DACL be auto-inherited from the parent. When clear on a creator SD, parent inheritance is suppressed even if SE_DACL_PROTECTED is not set. |
| SE_SACL_AUTO_INHERIT_REQ | 9 | 0x0200 | Requests that the SACL be auto-inherited from the parent. Same semantics as bit 8 for the SACL. |
| SE_DACL_AUTO_INHERITED (DI) | 10 | 0x0400 | The DACL was created through automatic inheritance. |
| SE_SACL_AUTO_INHERITED (SI) | 11 | 0x0800 | The SACL was created through automatic inheritance. |
| SE_DACL_PROTECTED (PD) | 12 | 0x1000 | The DACL is protected from inheritance. Inheritable ACEs from parent objects MUST NOT be merged. |
| SE_SACL_PROTECTED (PS) | 13 | 0x2000 | The SACL is protected from inheritance. |
| SE_RM_CONTROL_VALID (RM) | 14 | 0x4000 | The Sbz1 byte is interpreted as resource manager control bits. |
| SE_SELF_RELATIVE (SR) | 15 | 0x8000 | The SD is in self-relative format. MUST always be set for stored SDs. |

The architectural maximum SD size is 64 KB (constrained by the ACL header's 16-bit `AclSize` field).

The PROTECTED flags are operationally significant. Setting SE_DACL_PROTECTED prevents inheritance from parent objects -- the object keeps its current ACEs and stops accepting new inheritable ACEs from above.

## Null DACL vs empty DACL

The SE_DACL_PRESENT flag distinguishes two states with very different security consequences:

- **Null DACL** (SE_DACL_PRESENT not set) — no discretionary access control. AccessCheck grants all requested access to every caller. This SHOULD almost never be used.

- **Empty DACL** (SE_DACL_PRESENT set, zero ACEs) — AccessCheck grants no access to any caller (except the owner's implicit rights). An explicit statement that no principal has discretionary access.

Objects SHOULD always have a DACL. The SD creation algorithm ensures every new object receives one.
