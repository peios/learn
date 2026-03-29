---
title: Access Masks
order: 2
---

Every ACE carries an access mask -- a 32-bit integer where each bit represents a specific right. The same 32-bit layout is used in three contexts: the ACE's mask (what the rule grants or denies), the requested access (what the caller asks for), and the granted access (what AccessCheck returns).

## Bit layout

The 32 bits are divided into four regions:

### Object-specific rights (bits 0--15)

Defined by the object type. Different object types assign different meanings to these bits. A file uses bits for read, write, append, execute; a registry key uses bits for query value, set value, create subkey; a token uses bits for query, duplicate, impersonate. Each subsystem defines its own mapping.

### Standard rights (bits 16--20)

Common to all object types:

| Bit | Name | Value | Meaning |
|---|---|---|---|
| 16 | DELETE | 0x00010000 | Delete the object. |
| 17 | READ_CONTROL | 0x00020000 | Read the object's SD (excluding SACL). |
| 18 | WRITE_DAC | 0x00040000 | Modify the object's DACL. |
| 19 | WRITE_OWNER | 0x00080000 | Change the object's owner. |
| 20 | SYNCHRONIZE | 0x00100000 | Wait on the object. |

### Special rights (bits 24--25)

| Bit | Name | Value | Meaning |
|---|---|---|---|
| 24 | ACCESS_SYSTEM_SECURITY | 0x01000000 | Read or write the SACL. Requires SeSecurityPrivilege. |
| 25 | MAXIMUM_ALLOWED | 0x02000000 | Not a real right. Request flag that tells AccessCheck to compute and return the maximum set of rights the caller would be granted. MUST NOT appear in an ACE. |

### Generic rights (bits 28--31)

Abstract rights mapped to object-specific rights before evaluation:

| Bit | Name | Value |
|---|---|---|
| 28 | GENERIC_ALL | 0x10000000 |
| 29 | GENERIC_EXECUTE | 0x20000000 |
| 30 | GENERIC_WRITE | 0x40000000 |
| 31 | GENERIC_READ | 0x80000000 |

### Reserved bits

Bits 21--23 and 26--27 are reserved and MUST NOT be used.

## Generic mapping

Generic rights exist because SDs need to be portable across object types. A central access policy might say "allow GENERIC_READ on all objects" -- and GENERIC_READ means different specific bits for files versus registry keys.

Each object type defines a **GenericMapping** table:

| Field | Description |
|---|---|
| `read` | Specific + standard bits that GENERIC_READ maps to. |
| `write` | Specific + standard bits that GENERIC_WRITE maps to. |
| `execute` | Specific + standard bits that GENERIC_EXECUTE maps to. |
| `all` | Specific + standard bits that GENERIC_ALL maps to. |

Generic mapping happens once, at request time. AccessCheck MUST map any generic bits in the desired mask to object-specific bits using the object type's GenericMapping table, then clear the generic bits. The DACL walk operates exclusively on specific and standard bits.

> [!INFORMATIVE]
> KACS also maps ACE masks via GenericMapping at evaluation time (using a local variable -- the ACE itself is never mutated). This is an intentional divergence: the reference model expects ACE masks to be pre-mapped at SD construction time. Defensive mapping at evaluation time is necessary because central access policy recovery ACEs use GENERIC_ALL, which must be evaluated correctly regardless of object type.
