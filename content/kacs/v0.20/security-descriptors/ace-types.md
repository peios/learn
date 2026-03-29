---
title: ACE Types
order: 3
---

An Access Control Entry (ACE) is a single rule in an ACL. Each ACE has a header, an access mask, and a principal SID, with optional extensions for object-type and conditional ACEs.

## ACE header

Every ACE begins with a 4-byte header:

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 1 | AceType | Identifies the ACE type. |
| 1 | 1 | AceFlags | Inheritance and audit flags. |
| 2 | 2 | AceSize | Total size of the ACE in bytes, including the header. MUST be a multiple of 4. |

## DACL ACE types

### Basic ACEs

| Type | Value | Effect |
|---|---|---|
| ACCESS_ALLOWED_ACE | 0x00 | Grants the specified rights to the SID. |
| ACCESS_DENIED_ACE | 0x01 | Denies the specified rights to the SID. |

### Object-type ACEs

Extend basic ACEs with one or two GUIDs that scope the rule to a specific property or object class. Used for Active Directory access control.

| Type | Value | Effect |
|---|---|---|
| ACCESS_ALLOWED_OBJECT_ACE | 0x05 | Grants rights scoped to a property/class GUID. |
| ACCESS_DENIED_OBJECT_ACE | 0x06 | Denies rights scoped to a property/class GUID. |

The ObjectType GUID identifies the property or property set the ACE applies to. The InheritedObjectType GUID restricts inheritance to child objects of a specific class. Either or both GUIDs MAY be absent (indicated by a flags field), in which case the ACE behaves like a basic ACE for that dimension.

### Conditional ACEs

Extend basic and object-type ACEs with a conditional expression. The ACE only takes effect if the expression evaluates to TRUE against the caller's token attributes and the object's resource attributes.

| Type | Value | Effect |
|---|---|---|
| ACCESS_ALLOWED_CALLBACK_ACE | 0x09 | Conditional allow. |
| ACCESS_DENIED_CALLBACK_ACE | 0x0A | Conditional deny. |
| ACCESS_ALLOWED_CALLBACK_OBJECT_ACE | 0x0B | Conditional allow, scoped to GUID. |
| ACCESS_DENIED_CALLBACK_OBJECT_ACE | 0x0C | Conditional deny, scoped to GUID. |

> [!INFORMATIVE]
> The term "callback" is historical. KACS evaluates conditional expressions inline during AccessCheck. The name is preserved for binary format compatibility. UI and UX layers MAY refer to callback ACEs exclusively as "conditional ACEs" for simplicity.

## SACL ACE types

### Audit ACEs

Trigger audit log entries when matching access attempts occur. The AceFlags field carries SUCCESSFUL_ACCESS_ACE_FLAG (0x40) and/or FAILED_ACCESS_ACE_FLAG (0x80).

| Type | Value | Effect |
|---|---|---|
| SYSTEM_AUDIT_ACE | 0x02 | Audit access matching the SID and mask. |
| SYSTEM_AUDIT_OBJECT_ACE | 0x07 | Audit access scoped to a GUID. |
| SYSTEM_AUDIT_CALLBACK_ACE | 0x0D | Conditional audit. |
| SYSTEM_AUDIT_CALLBACK_OBJECT_ACE | 0x0F | Conditional audit, scoped to GUID. |

### Alarm ACEs (continuous auditing)

> [!INFORMATIVE]
> These ACE types are reserved but unimplemented in the reference model. KACS repurposes them for continuous per-operation auditing: unlike standard audit ACEs (which emit a single event at handle creation), alarm ACEs configure per-operation audit masks that persist on the open handle. This creates no interoperability conflict because external sources never contain alarm ACEs.

| Type | Value | Effect |
|---|---|---|
| SYSTEM_ALARM_ACE | 0x03 | Continuous audit for matching SID and mask. |
| SYSTEM_ALARM_OBJECT_ACE | 0x08 | Continuous audit scoped to a GUID. |
| SYSTEM_ALARM_CALLBACK_ACE | 0x0E | Conditional continuous audit. |
| SYSTEM_ALARM_CALLBACK_OBJECT_ACE | 0x10 | Conditional continuous audit, scoped to GUID. |

### Mandatory label ACE

Defines the object's integrity level for MIC. At most one per SACL. The SID encodes the integrity level. The access mask encodes the MIC policy (which operations are blocked for non-dominant callers).

| Type | Value | Effect |
|---|---|---|
| SYSTEM_MANDATORY_LABEL_ACE | 0x11 | Sets the object's integrity level and MIC policy. |

### Resource attribute ACE

Attaches name-value attributes to the object for conditional ACE evaluation. The ACE's SID is always Everyone (`S-1-1-0`).

| Type | Value | Effect |
|---|---|---|
| SYSTEM_RESOURCE_ATTRIBUTE_ACE | 0x12 | Defines a resource attribute on the object. |

### Scoped policy ID ACE

References a central access policy by SID. During AccessCheck, the referenced policy's rules are evaluated in addition to the object's own DACL.

| Type | Value | Effect |
|---|---|---|
| SYSTEM_SCOPED_POLICY_ID_ACE | 0x13 | References a central access policy. |

### Process trust label ACE

Defines the object's PIP trust level. The SID encodes the PIP type and trust level. The access mask specifies the exact rights that non-dominant callers are allowed.

| Type | Value | Effect |
|---|---|---|
| SYSTEM_PROCESS_TRUST_LABEL_ACE | 0x14 | Sets the object's PIP trust level. |

## Reserved ACE type

| Type | Value | Notes |
|---|---|---|
| ACCESS_ALLOWED_COMPOUND_ACE | 0x04 | Never implemented. Reserved. |

## ACL revision

ACLs carry a revision number that constrains which ACE types MAY appear:

- **ACL_REVISION (0x02)** — basic ACE types (0x00, 0x01, 0x02, 0x03), mandatory label (0x11), resource attribute (0x12), scoped policy (0x13), and process trust label (0x14).
- **ACL_REVISION_DS (0x04)** — additionally permits object-type ACEs (0x05--0x08), callback ACEs (0x09--0x0C, 0x0D--0x10). Required for Active Directory access control.

When creating new ACLs, the revision SHOULD be set to the minimum required by the ACE types present.
