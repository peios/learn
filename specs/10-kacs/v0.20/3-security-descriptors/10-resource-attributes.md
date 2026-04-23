---
title: Resource Attributes
---

A Security Descriptor MAY carry metadata about the object it protects -- descriptive properties rather than access rules. These are resource attributes: name-value pairs stored as SYSTEM_RESOURCE_ATTRIBUTE_ACEs in the SACL.

Resource attributes do not grant or deny access. They exist so that conditional ACEs in the DACL can reference properties of the object during evaluation. A conditional allow ACE might say "grant read access if `@User.clearance >= @Resource.confidentiality`."

Each resource attribute ACE encodes a single named, typed, multi-valued
attribute. The name is a string. Values MAY be integers, strings, booleans,
SIDs, or byte arrays. The attribute data uses the claim entry format defined in
the Claim Attribute Format section.

Multiple resource attribute ACEs MAY appear in the same SACL, each carrying a different attribute. If two ACEs carry the same attribute name, the first one wins -- duplicates are silently ignored.

An inherit-only `SYSTEM_RESOURCE_ATTRIBUTE_ACE` does not apply to the object it
is attached to and MUST be ignored during resource-attribute extraction.

Resource attributes are extracted from the SACL before the DACL walk begins, so they are available when conditional expressions need them.

## Claim types

| Type | Value | Description |
|---|---|---|
| INT64 | 0x0001 | Signed 64-bit integer. |
| UINT64 | 0x0002 | Unsigned 64-bit integer. |
| STRING | 0x0003 | Unicode string. |
| FQBN | 0x0004 | Fully Qualified Binary Name. Reserved — not supported in KACS v0.20. |
| SID | 0x0005 | Security identifier. |
| BOOLEAN | 0x0006 | Boolean value. |
| OCTET | 0x0010 | Byte array. |

Boolean values MUST be normalized to 1 (true) or 0 (false) at resolution time (when the conditional expression evaluator reads the attribute value), regardless of the wire encoding.
