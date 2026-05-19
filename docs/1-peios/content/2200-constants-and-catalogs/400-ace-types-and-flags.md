---
title: ACE types and flags
type: reference
description: The 21 ACE type values catalogued, plus the AceFlags bits (inheritance and audit), the SD control flags, and the canonical inheritance flag combinations.
related:
  - peios/constants-and-catalogs/overview
  - peios/security-descriptors/acls-and-aces
  - peios/wire-formats-reference/security-descriptors
---

This page catalogues the numeric values used in ACL/ACE encoding — ACE types, AceFlags, SD control flags, and canonical inheritance combinations. The conceptual model is in [ACLs, ACEs, and access masks](~peios/security-descriptors/acls-and-aces); the byte-level layout is in [Security descriptors (wire format)](~peios/wire-formats-reference/security-descriptors).

## ACE type values

The full catalog of `AceType` values:

| Value | Name | Body shape | Notes |
|---|---|---|---|
| 0x00 | `ACCESS_ALLOWED_ACE_TYPE` | Single-SID | Grant. |
| 0x01 | `ACCESS_DENIED_ACE_TYPE` | Single-SID | Deny. |
| 0x02 | `SYSTEM_AUDIT_ACE_TYPE` | Single-SID | Audit ACE. |
| 0x03 | `SYSTEM_ALARM_ACE_TYPE` | Single-SID | Alarm ACE (continuous audit). |
| 0x04 | `ACCESS_ALLOWED_COMPOUND_ACE_TYPE` | (reserved) | Reserved. Not used in v0.20. |
| 0x05 | `ACCESS_ALLOWED_OBJECT_ACE_TYPE` | Object | Allow, GUID-scoped. |
| 0x06 | `ACCESS_DENIED_OBJECT_ACE_TYPE` | Object | Deny, GUID-scoped. |
| 0x07 | `SYSTEM_AUDIT_OBJECT_ACE_TYPE` | Object | Audit, GUID-scoped. |
| 0x08 | `SYSTEM_ALARM_OBJECT_ACE_TYPE` | Object | Alarm, GUID-scoped. |
| 0x09 | `ACCESS_ALLOWED_CALLBACK_ACE_TYPE` | Callback | Conditional allow. |
| 0x0A | `ACCESS_DENIED_CALLBACK_ACE_TYPE` | Callback | Conditional deny. |
| 0x0B | `ACCESS_ALLOWED_CALLBACK_OBJECT_ACE_TYPE` | Callback object | Conditional allow, GUID-scoped. |
| 0x0C | `ACCESS_DENIED_CALLBACK_OBJECT_ACE_TYPE` | Callback object | Conditional deny, GUID-scoped. |
| 0x0D | `SYSTEM_AUDIT_CALLBACK_ACE_TYPE` | Callback | Conditional audit. |
| 0x0E | `SYSTEM_ALARM_CALLBACK_ACE_TYPE` | Callback | Conditional alarm. |
| 0x0F | `SYSTEM_AUDIT_CALLBACK_OBJECT_ACE_TYPE` | Callback object | Conditional audit, GUID-scoped. |
| 0x10 | `SYSTEM_ALARM_CALLBACK_OBJECT_ACE_TYPE` | Callback object | Conditional alarm, GUID-scoped. |
| 0x11 | `SYSTEM_MANDATORY_LABEL_ACE_TYPE` | Single-SID | Object's mandatory integrity label. SID is from `S-1-16-*`. |
| 0x12 | `SYSTEM_RESOURCE_ATTRIBUTE_ACE_TYPE` | Single-SID + claim entry | A typed key-value attribute. SID is always `S-1-1-0`. |
| 0x13 | `SYSTEM_SCOPED_POLICY_ID_ACE_TYPE` | Single-SID | Reference to a CAAP by policy SID. |
| 0x14 | `SYSTEM_PROCESS_TRUST_LABEL_ACE_TYPE` | Single-SID | Object's PIP trust label. SID is from `S-1-19-*`. |

ACE type values 0x15 and beyond are unused / reserved.

## ACE families

The ACE types fall into three families by SACL/DACL membership:

| Family | Types | Where they go |
|---|---|---|
| Access-control | 0x00, 0x01, 0x05, 0x06, 0x09–0x0C | DACL |
| Audit and alarm | 0x02, 0x03, 0x07, 0x08, 0x0D–0x10 | SACL |
| System-policy | 0x11, 0x12, 0x13, 0x14 | SACL |

A DACL containing audit ACEs (or vice versa) is malformed; the kernel does not enforce this strictly at parse time but ignores misplaced ACEs during evaluation.

## AceFlags bits

The single-byte `AceFlags` field:

| Bit | Name | Meaning |
|---|---|---|
| 0x01 | `OBJECT_INHERIT_ACE` | Inherits to non-container child objects (files). |
| 0x02 | `CONTAINER_INHERIT_ACE` | Inherits to container child objects (directories). |
| 0x04 | `NO_PROPAGATE_INHERIT_ACE` | Inherits one level; `OI`/`CI` cleared in the inherited copy. |
| 0x08 | `INHERIT_ONLY_ACE` | Applies to children only; skipped on this object. |
| 0x10 | `INHERITED_ACE` | This ACE was created by inheritance, not explicit assignment. |
| 0x40 | `SUCCESSFUL_ACCESS_ACE_FLAG` | (Audit/alarm) Fire on success. |
| 0x80 | `FAILED_ACCESS_ACE_FLAG` | (Audit/alarm) Fire on failure. |

Bits 0x20 and 0x21 are unused.

## Canonical inheritance flag combinations

The combinations that appear most often:

| Flags | Notation | Effect |
|---|---|---|
| `CI \| OI` | "Container and Object Inherit" | Inherits to every descendant (files and directories), recursively. |
| `CI` | "Container Inherit" | Inherits to descendant directories only. |
| `OI` | "Object Inherit" | Inherits to descendant files only. |
| `CI \| OI \| IO` | "...Inherit Only" | Applies to descendants but not to this object. |
| `CI \| OI \| NP` | "...No Propagate" | Applies to immediate children only, not grandchildren. |
| (none) | (no flags) | Applies only to this object; does not inherit. |

A typical "permission grant on this directory and all files inside" uses `CI | OI`. A "permission grant that applies only when looking up children, not when listing this directory" uses `CI | OI | IO`.

## SD control flags

The 16-bit `Control` field in an SD header:

| Bit | Name | Meaning |
|---|---|---|
| 0x0001 | `SE_OWNER_DEFAULTED` | Owner SID was defaulted. |
| 0x0002 | `SE_GROUP_DEFAULTED` | Primary group SID was defaulted. |
| 0x0004 | `SE_DACL_PRESENT` | DACL present. Clear means NULL DACL (grant all). |
| 0x0008 | `SE_DACL_DEFAULTED` | DACL was defaulted. |
| 0x0010 | `SE_SACL_PRESENT` | SACL present. |
| 0x0020 | `SE_SACL_DEFAULTED` | SACL was defaulted. |
| 0x0040 | `SE_DACL_TRUSTED` | Informational; KACS does not act on this flag. |
| 0x0080 | `SE_SERVER_SECURITY` | Server-security mode. **Fail-closed in v0.20**. |
| 0x0100 | `SE_DACL_AUTO_INHERIT_REQ` | Auto-inheritance was requested. |
| 0x0200 | `SE_SACL_AUTO_INHERIT_REQ` | Same for SACL. |
| 0x0400 | `SE_DACL_AUTO_INHERITED` | The DACL was auto-inherited. |
| 0x0800 | `SE_SACL_AUTO_INHERITED` | Same. |
| 0x1000 | `SE_DACL_PROTECTED` | DACL does not accept inherited ACEs from parent. |
| 0x2000 | `SE_SACL_PROTECTED` | Same for SACL. |
| 0x4000 | `SE_RM_CONTROL_VALID` | The Sbz1 byte is a resource-manager control byte. |
| 0x8000 | `SE_SELF_RELATIVE` | The SD is in self-relative format. Always set on the wire. |

## ACL revision values

| Value | Meaning |
|---|---|
| 0x02 | `ACL_REVISION` — basic ACE types only. |
| 0x04 | `ACL_REVISION_DS` — permits object and callback ACEs. |

Writers should use the minimum revision necessary for the ACEs they include. Parsers accept either. Other values are rejected with `-EINVAL`.

## Standard generic right name → bit mapping

For reference, the four generic right flags:

| Flag | Value |
|---|---|
| `GENERIC_READ` | 0x80000000 |
| `GENERIC_WRITE` | 0x40000000 |
| `GENERIC_EXECUTE` | 0x20000000 |
| `GENERIC_ALL` | 0x10000000 |

These expand to object-specific bits via the object type's GenericMapping table — see [Access mask bits](~peios/constants-and-catalogs/access-mask-bits).

## Standard rights

These access rights are shared across all object types:

| Right | Value |
|---|---|
| `DELETE` | 0x00010000 |
| `READ_CONTROL` | 0x00020000 |
| `WRITE_DAC` | 0x00040000 |
| `WRITE_OWNER` | 0x00080000 |
| `SYNCHRONIZE` | 0x00100000 |
| `STANDARD_RIGHTS_REQUIRED` | 0x000F0000 (DELETE | READ_CONTROL | WRITE_DAC | WRITE_OWNER) |
| `STANDARD_RIGHTS_READ` | 0x00020000 (READ_CONTROL) |
| `STANDARD_RIGHTS_WRITE` | 0x00020000 (READ_CONTROL) |
| `STANDARD_RIGHTS_EXECUTE` | 0x00020000 (READ_CONTROL) |
| `STANDARD_RIGHTS_ALL` | 0x001F0000 (all five) |

`STANDARD_RIGHTS_REQUIRED` is the conventional minimum mask included in `*_ALL_ACCESS` constants. The other STANDARD_RIGHTS_* values are aliases.

## Special rights

| Right | Value | Meaning |
|---|---|---|
| `ACCESS_SYSTEM_SECURITY` | 0x01000000 | Read/write the SACL. Gated by SeSecurityPrivilege. |
| `MAXIMUM_ALLOWED` | 0x02000000 | Request flag; not a real right. AccessCheck returns the maximum grantable mask. |

`MAXIMUM_ALLOWED` MUST NOT appear in an ACE — it is a desired-access modifier only.

## Mandatory integrity label policy bits

In the mask field of `SYSTEM_MANDATORY_LABEL_ACE`:

| Bit | Name | Meaning |
|---|---|---|
| 0x00000001 | `SYSTEM_MANDATORY_LABEL_NO_READ_UP` | Block read-category from lower integrity. |
| 0x00000002 | `SYSTEM_MANDATORY_LABEL_NO_WRITE_UP` | Block write-category. (The default for unlabelled objects.) |
| 0x00000004 | `SYSTEM_MANDATORY_LABEL_NO_EXECUTE_UP` | Block execute-category. |

## Audit ACE flags (extended ACE Flags)

The high-bit `AceFlags` values specific to audit and alarm ACEs:

| Bit | Name | Meaning |
|---|---|---|
| 0x40 | `SUCCESSFUL_ACCESS_ACE_FLAG` | Fire on successful access. |
| 0x80 | `FAILED_ACCESS_ACE_FLAG` | Fire on failed access. |

Both can be set in one ACE — fires on both. Neither set — the ACE applies but never fires. Either combination is valid.

## Conditional ACE expression magic

The 4-byte magic at the start of conditional ApplicationData:

| Bytes | ASCII | Meaning |
|---|---|---|
| `0x61 0x72 0x74 0x78` | "artx" | Marks the start of a conditional expression. |

Absent or truncated magic causes the expression to evaluate to UNKNOWN.

## Claim value type values

For claim entries (in resource attribute ACEs and token claims):

| Value | Type | Encoding |
|---|---|---|
| 0x0001 | `INT64` | 8 bytes signed LE |
| 0x0002 | `UINT64` | 8 bytes unsigned LE |
| 0x0003 | `STRING` | Length-prefixed UTF-16LE |
| 0x0004 | `FQBN` | Reserved (not supported in v0.20) |
| 0x0005 | `SID` | Length-prefixed binary SID |
| 0x0006 | `BOOLEAN` | 8 bytes; non-zero is TRUE |
| 0x0010 | `OCTET` | Length-prefixed bytes |

## Claim flags

For claim entries:

| Bit | Name | Meaning |
|---|---|---|
| 0x0002 | `CLAIM_SECURITY_ATTRIBUTE_VALUE_CASE_SENSITIVE` | String/octet comparisons against this claim are case-sensitive. |
| 0x0004 | `CLAIM_SECURITY_ATTRIBUTE_USE_FOR_DENY_ONLY` | Invisible to allow-ACE conditions; visible to deny. |
| 0x0010 | `CLAIM_SECURITY_ATTRIBUTE_DISABLED` | Invisible to all conditions. |
| 0x0020 | `CLAIM_SECURITY_ATTRIBUTE_MANDATORY` | Cannot be removed/modified without SeTcbPrivilege. |

## Limits

Sizes that apply to ACLs and SDs:

| Limit | Value |
|---|---|
| Max SD size | 65,535 bytes |
| Max ACL size | 64 KB (16-bit AclSize) |
| ACE AceSize granularity | Multiple of 4 bytes |
| Min ACL header | 8 bytes |
| Min ACE header | 4 bytes |
| Min Single-SID ACE | 12 bytes (header + mask + 8-byte SID minimum) — varies with SID size |
| Conditional expression recommended max stack depth | 1024 |
