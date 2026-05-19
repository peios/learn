---
title: ACLs, ACEs, and access masks
type: concept
description: The DACL and SACL are both Access Control Lists — ordered sequences of Access Control Entries. Each ACE has a type, a set of flags, a 32-bit access mask, and a SID. This page covers the ACL structure, the catalog of ACE types, the ACE flags that control inheritance and audit, and the layout of the access mask.
related:
  - peios/security-descriptors/overview
  - peios/security-descriptors/dacl-evaluation
  - peios/security-descriptors/inheritance
  - peios/security-descriptors/the-sacl
  - peios/security-descriptors/conditional-aces
---

A DACL and a SACL are both **Access Control Lists** — sequences of **Access Control Entries** in a defined order. The two lists have different jobs (the DACL decides access; the SACL records system-level policy and audit), but they share a structure. This page covers that structure, plus the catalog of ACE types and the layout of the 32-bit access mask that almost every ACE carries.

## ACL structure

An ACL is, conceptually, an ordered array of ACEs. The binary form is a short header followed by the ACEs back-to-back:

| Field | Size | Meaning |
|---|---|---|
| AclRevision | 1 byte | Format revision. `0x02` for basic ACL, `0x04` for ACLs containing object or callback ACEs. |
| Reserved | 1 byte | Always zero. |
| AclSize | 2 bytes (LE) | Total size of the ACL in bytes, including the header. |
| AceCount | 2 bytes (LE) | Number of ACEs. |
| Reserved | 2 bytes (LE) | Always zero. |
| ACEs | variable | `AceCount` ACEs, packed without padding. |

The maximum ACL size is 64 KB — the AclSize field is a 16-bit value. An ACL is self-delimiting: a parser walks exactly `AceCount` ACEs starting after the header and stops when it has consumed `AclSize` bytes.

The two ACL revisions differ only in what ACE types they are allowed to contain. `0x02` is the basic revision; `0x04` additionally allows object ACEs (the type with property GUIDs) and callback ACEs (the type with conditional expressions). Parsers should accept whichever revision they see; writers should emit the minimum revision necessary for the ACEs they are including.

## ACE structure

Every ACE has a 4-byte header followed by a type-specific body.

| Field | Size | Meaning |
|---|---|---|
| AceType | 1 byte | Numeric ACE type (see below). |
| AceFlags | 1 byte | Inheritance and audit flags (see below). |
| AceSize | 2 bytes (LE) | Total size of the ACE, including the header. Always a multiple of 4. |
| Body | variable | Type-specific payload. |

The body's shape depends on the type. The two most common shapes:

- **Single-SID body** — `Mask (4 bytes) | SID (variable)`. Used by basic allow/deny/audit/alarm ACEs and by the integrity/scoped-policy/trust-label SACL types.
- **Object ACE body** — `Mask (4) | Flags (4) | optional ObjectType GUID (16) | optional InheritedObjectType GUID (16) | SID (variable)`. The flags field controls whether each GUID is present.
- **Callback (conditional) body** — same as the corresponding non-callback type, plus a trailing ApplicationData block holding the conditional expression bytecode. See [Conditional ACEs](~peios/security-descriptors/conditional-aces).

The detailed byte-level layouts live in the [Wire formats reference](~peios/wire-formats-reference/overview). For this page, what matters is that every ACE is self-describing — the parser reads the header, dispatches by type, and consumes exactly `AceSize` bytes.

## The ACE type catalog

There are twenty-one ACE types, split into three families: access-control, audit/alarm, and system-policy. Most SDs you will look at use only a small subset of these — typically `ACCESS_ALLOWED`, `ACCESS_DENIED`, `SYSTEM_AUDIT`, and `SYSTEM_MANDATORY_LABEL`.

### Access-control ACE family

These ACEs participate in the DACL walk.

| Type | Value | Body | Use |
|---|---|---|---|
| `ACCESS_ALLOWED` | 0x00 | Single SID | Grant the listed rights to the named principal. |
| `ACCESS_DENIED` | 0x01 | Single SID | Deny the listed rights to the named principal. |
| `ACCESS_ALLOWED_COMPOUND` | 0x04 | Reserved (not used in v0.20). | — |
| `ACCESS_ALLOWED_OBJECT` | 0x05 | Object ACE | Grant rights, scoped by property GUID or inherited only by certain child object types. |
| `ACCESS_DENIED_OBJECT` | 0x06 | Object ACE | Deny rights, same scoping. |
| `ACCESS_ALLOWED_CALLBACK` | 0x09 | Single SID + expression | Grant rights only if the conditional expression evaluates TRUE. |
| `ACCESS_DENIED_CALLBACK` | 0x0A | Single SID + expression | Deny rights when the expression evaluates TRUE or UNKNOWN. |
| `ACCESS_ALLOWED_CALLBACK_OBJECT` | 0x0B | Object ACE + expression | Grant rights, conditionally, scoped by GUID. |
| `ACCESS_DENIED_CALLBACK_OBJECT` | 0x0C | Object ACE + expression | Deny rights, conditionally, scoped by GUID. |

The most common ACEs you will write are `ACCESS_ALLOWED` and `ACCESS_DENIED` — plain "this principal gets these rights" or "this principal does not get these rights". The object variants matter when you are protecting directory-style objects with per-property permissions. The callback variants are how conditional expressions show up in ACEs.

### Audit and alarm ACE family

These ACEs sit in the SACL and decide when access produces an audit event.

| Type | Value | Body | Use |
|---|---|---|---|
| `SYSTEM_AUDIT` | 0x02 | Single SID | Emit an audit event when the named principal attempts the listed rights. Flags decide whether success, failure, or both. |
| `SYSTEM_AUDIT_OBJECT` | 0x07 | Object ACE | Same, scoped by GUID. |
| `SYSTEM_AUDIT_CALLBACK` | 0x0D | Single SID + expression | Audit conditionally. UNKNOWN result emits the event (fail-open for auditing). |
| `SYSTEM_AUDIT_CALLBACK_OBJECT` | 0x0F | Object ACE + expression | Conditional, scoped by GUID. |
| `SYSTEM_ALARM` | 0x03 | Single SID | Configure per-operation continuous audit on the open handle. Each matching operation produces an event. |
| `SYSTEM_ALARM_OBJECT` | 0x08 | Object ACE | Same, scoped by GUID. |
| `SYSTEM_ALARM_CALLBACK` | 0x0E | Single SID + expression | Conditional continuous audit. |
| `SYSTEM_ALARM_CALLBACK_OBJECT` | 0x10 | Object ACE + expression | Conditional, scoped by GUID. |

The distinction between AUDIT and ALARM is important: AUDIT fires at the moment of handle creation (one event per access attempt), ALARM configures a per-operation mask on the open handle that fires on every subsequent operation. See [The SACL](~peios/security-descriptors/the-sacl) and [Auditing](~peios/auditing/overview) for the full story.

### System-policy ACE family

These ACEs sit in the SACL and carry policy other than audit.

| Type | Value | Body | Use |
|---|---|---|---|
| `SYSTEM_MANDATORY_LABEL` | 0x11 | Integrity SID + mask | The object's mandatory integrity label and the policy bits that govern who can write/read/execute up. |
| `SYSTEM_RESOURCE_ATTRIBUTE` | 0x12 | Everyone SID + claim entry | A name-value attribute on the object, referenceable as `@Resource.<name>` in conditional expressions. |
| `SYSTEM_SCOPED_POLICY_ID` | 0x13 | Policy SID | A reference to a central access policy that should be evaluated alongside the object's own DACL. |
| `SYSTEM_PROCESS_TRUST_LABEL` | 0x14 | PIP SID + mask | The object's PIP trust label and the explicit allowed mask for non-dominant callers. |

These four are how the SACL extends the access decision beyond what the DACL alone can express. Each has its own evaluation rules (covered in the relevant topics — MIC under [Access decisions](~peios/access-decisions/overview), resource attributes under [Resource attributes](~peios/security-descriptors/resource-attributes), CAAP under [Central access policies](~peios/central-access-policies/overview), PIP under [Process integrity protection](~peios/process-integrity-protection/overview)).

## ACE flags

The `AceFlags` field is a bitmask. Most flags control inheritance — whether and how an ACE on a parent object propagates to children. Two flags control audit firing on SYSTEM_AUDIT and SYSTEM_ALARM ACEs.

| Flag | Value | Effect |
|---|---|---|
| `OBJECT_INHERIT_ACE` | 0x01 | The ACE inherits to non-container child objects (files, not directories). |
| `CONTAINER_INHERIT_ACE` | 0x02 | The ACE inherits to container child objects (directories). |
| `NO_PROPAGATE_INHERIT_ACE` | 0x04 | The ACE is inherited by direct children but its `OBJECT_INHERIT_ACE` and `CONTAINER_INHERIT_ACE` flags are cleared in the inherited copy — it stops propagating after one level. |
| `INHERIT_ONLY_ACE` | 0x08 | The ACE is for inheritance only. The access check skips it; it exists only to be copied to children. |
| `INHERITED_ACE` | 0x10 | Set on ACEs that were created by inheritance, not by an explicit add. Tools use this flag to distinguish "this came from the parent" from "the user set this explicitly". |
| `SUCCESSFUL_ACCESS_ACE_FLAG` | 0x40 | (Audit/alarm only) Fire on successful access. |
| `FAILED_ACCESS_ACE_FLAG` | 0x80 | (Audit/alarm only) Fire on denied access. |

The inheritance flags compose in non-obvious ways. Combinations you will see often:

| Flags | Effect |
|---|---|
| `CONTAINER_INHERIT_ACE \| OBJECT_INHERIT_ACE` (`CI \| OI`) | Inherit to all descendants (files and directories), recursively. |
| `CONTAINER_INHERIT_ACE` (`CI`) | Inherit to descendant containers only. |
| `OBJECT_INHERIT_ACE` (`OI`) | Inherit to descendant non-containers only. |
| `CI \| OI \| INHERIT_ONLY_ACE` | Apply to descendants but not to this object. |
| `CI \| OI \| NO_PROPAGATE_INHERIT_ACE` | Apply to immediate children only, not grandchildren. |

The full inheritance machinery is on [Inheritance](~peios/security-descriptors/inheritance).

## The access mask

Every ACE that participates in the DACL walk, and every audit/alarm ACE, carries a 32-bit access mask. The mask uses four regions, partitioned by bit position.

| Region | Bits | Purpose |
|---|---|---|
| Object-specific rights | 0–15 | 16 bits whose meaning depends on the object type. For a file: `FILE_READ_DATA`, `FILE_WRITE_DATA`, etc. For a registry key: `KEY_QUERY_VALUE`, `KEY_SET_VALUE`, etc. For a process: `PROCESS_TERMINATE`, `PROCESS_VM_READ`, etc. |
| Standard rights | 16–20 | 5 bits shared across all object types: `DELETE` (0x10000), `READ_CONTROL` (0x20000), `WRITE_DAC` (0x40000), `WRITE_OWNER` (0x80000), `SYNCHRONIZE` (0x100000). |
| Reserved | 21–23 | Must be zero. |
| Special rights | 24–25 | `ACCESS_SYSTEM_SECURITY` (0x01000000) — gates SACL read/write. `MAXIMUM_ALLOWED` (0x02000000) — a request flag, not a real right. |
| Reserved | 26–27 | Must be zero. |
| Generic rights | 28–31 | `GENERIC_ALL` (0x10000000), `GENERIC_EXECUTE` (0x20000000), `GENERIC_WRITE` (0x40000000), `GENERIC_READ` (0x80000000). Abstract — mapped to object-specific rights at evaluation time. |

A few things worth noting about the layout:

- **The same bit means different things on different object types.** Bit 0 is `FILE_READ_DATA` on a file but `KEY_QUERY_VALUE` on a registry key. The object-specific portion of the mask is reusable across types because the object manager knows what kind of object it is.
- **Standard rights are uniform.** `DELETE` always means delete the object; `READ_CONTROL` always means read the SD; `WRITE_DAC` always means modify the DACL; `WRITE_OWNER` always means change the owner. These bits work identically regardless of object type.
- **Generic rights are abstract.** `GENERIC_READ` does not name a specific right. It is a placeholder that gets mapped to a concrete combination of object-specific and standard rights at the moment of evaluation, using the object type's GenericMapping table.

### Generic mapping

When an access check sees a generic right in either an ACE mask or a requested mask, it consults the object type's GenericMapping table to substitute concrete rights. The mapping is per-type:

| Object type | GENERIC_READ maps to |
|---|---|
| File | `FILE_READ_DATA \| FILE_READ_ATTRIBUTES \| FILE_READ_EA \| READ_CONTROL \| SYNCHRONIZE` |
| Token | `TOKEN_QUERY \| READ_CONTROL` |
| Process | `PROCESS_QUERY_INFORMATION \| PROCESS_VM_READ \| READ_CONTROL` |

The full GenericMapping tables live in the [Constants and catalogs](~peios/constants-and-catalogs/overview) reference. The key idea for now is: generic rights let an ACE author say "give the read permission for this thing" without knowing exactly which bits "read" means for this object type. The access check fills in the concrete bits at evaluation time.

This is also why an ACE that grants `GENERIC_READ` to a principal will produce different concrete grants depending on which object the ACE is on. The bit pattern in the ACE is the same; the meaning depends on where it lives.

### MAXIMUM_ALLOWED is a request, not a right

`MAXIMUM_ALLOWED` (bit 25) is special. It is not a right an ACE can grant — it is a marker the **caller** sets in a desired-access mask when asking "what is the maximum access I could be granted right now?". The access check sees the flag, evaluates the DACL fully, and returns every right the caller could be granted.

`MAXIMUM_ALLOWED` MUST NOT appear in an ACE. It is meaningless there.

## Sizes and limits

For reference:

| Limit | Value |
|---|---|
| Maximum SD size | 65,535 bytes |
| Maximum ACL size | 64 KB (16-bit AclSize field) |
| Maximum ACEs per ACL | Bounded only by AclSize and the per-ACE minimum size |
| Maximum SID size | 68 bytes |
| ACE size granularity | Multiple of 4 bytes |

A practical SD on a typical object is far below these limits — a few hundred bytes at most. The limits exist for the pathological cases.
