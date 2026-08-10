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

Value 0x15 (`SYSTEM_ACCESS_FILTER_ACE_TYPE`) is defined in the uapi header for format parity but has no v0.20 semantics; values beyond it are unused. Unrecognised ACE types are silently skipped during evaluation and preserved on round-trip serialisation.

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

Bit 0x20 is unused.

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

## Access rights

The value catalogues for generic rights, standard rights (and the `STANDARD_RIGHTS_*` aliases), the special rights (`ACCESS_SYSTEM_SECURITY`, `MAXIMUM_ALLOWED`), and the per-object-type rights are all on [Access mask bits](~peios/constants-and-catalogs/access-mask-bits). The byte layout of the 32-bit mask itself is in [Security descriptors (wire format)](~peios/wire-formats-reference/security-descriptors).

## Mandatory integrity label policy bits

In the mask field of `SYSTEM_MANDATORY_LABEL_ACE`:

| Bit | Name | Meaning |
|---|---|---|
| 0x00000001 | `SYSTEM_MANDATORY_LABEL_NO_READ_UP` | Block read-category from lower integrity. |
| 0x00000002 | `SYSTEM_MANDATORY_LABEL_NO_WRITE_UP` | Block write-category. (The default for unlabelled objects.) |
| 0x00000004 | `SYSTEM_MANDATORY_LABEL_NO_EXECUTE_UP` | Block execute-category. |

## Audit ACE flags

The flags specific to audit and alarm ACEs — `SUCCESSFUL_ACCESS_ACE_FLAG` (0x40) and `FAILED_ACCESS_ACE_FLAG` (0x80) — are the two high bits in the AceFlags table above. Both can be set in one ACE — fires on both. Neither set — the ACE applies but never fires. Either combination is valid.

## Conditional ACE expression magic

Conditional ApplicationData starts with the 4-byte magic `0x61 0x72 0x74 0x78` ("artx"); absent or truncated magic causes the expression to evaluate to UNKNOWN. The bytecode encoding — including the full opcode catalogue — is owned by [Conditional ACE bytecode](~peios/wire-formats-reference/conditional-ace-bytecode).

## Claim value type values

For claim entries (in resource attribute ACEs and token claims):

| Value | Type | Notes |
|---|---|---|
| 0x0001 | `INT64` | Signed 64-bit integer |
| 0x0002 | `UINT64` | Unsigned 64-bit integer |
| 0x0003 | `STRING` | UTF-16LE string |
| 0x0004 | `FQBN` | Reserved (not supported in v0.20) |
| 0x0005 | `SID` | Binary SID |
| 0x0006 | `BOOLEAN` | Stored as u64; non-zero is TRUE |
| 0x0010 | `OCTET` | Byte array |

The per-type value-record encodings are part of the claim entry wire format — see [Token and session specs](~peios/wire-formats-reference/token-and-session-specs).

## Claim flags

For claim entries:

| Bit | Name | Meaning |
|---|---|---|
| 0x0002 | `CLAIM_SECURITY_ATTRIBUTE_VALUE_CASE_SENSITIVE` | String/octet comparisons against this claim are case-sensitive. |
| 0x0004 | `CLAIM_SECURITY_ATTRIBUTE_USE_FOR_DENY_ONLY` | Invisible to allow-ACE conditions; visible to deny. |
| 0x0010 | `CLAIM_SECURITY_ATTRIBUTE_DISABLED` | Invisible to all conditions. |
| 0x0020 | `CLAIM_SECURITY_ATTRIBUTE_MANDATORY` | Cannot be removed/modified without SeTcbPrivilege. |

## Limits

The size limits that apply to ACLs and SDs are catalogued in [Other constants](~peios/constants-and-catalogs/other-constants) under "Size and count limits"; the byte-layout constraints they derive from are in [Security descriptors (wire format)](~peios/wire-formats-reference/security-descriptors).
