---
title: SD Inheritance
order: 5
---

Security Descriptors propagate structurally. When a file is created in a directory, the directory's inheritable ACEs flow down to the new file's SD. This automatic propagation is inheritance.

Inheritance applies to objects with a container/child relationship: directories contain files and subdirectories, registry keys contain subkeys and values. Objects without a container parent (standalone IPC endpoints, tokens, processes) do not inherit.

## Inheritance flags

Four flags in the ACE header's AceFlags field control propagation:

| Flag | Value | Description |
|---|---|---|
| OBJECT_INHERIT_ACE (OI) | 0x01 | Inherited by non-container children (files). For container children (subdirectories), inherited as inherit-only unless NP is also set. |
| CONTAINER_INHERIT_ACE (CI) | 0x02 | Inherited by container children (subdirectories). The inherited ACE remains inheritable (propagates to grandchildren) unless NP is also set. |
| NO_PROPAGATE_INHERIT_ACE (NP) | 0x04 | When inherited, OI and CI flags are cleared on the copy. One-level inheritance. |
| INHERIT_ONLY_ACE (IO) | 0x08 | Does not apply to the object it is attached to. Exists only to be inherited by children. |

A fifth flag records provenance:

| Flag | Value | Description |
|---|---|---|
| INHERITED_ACE | 0x10 | Set on ACEs created through inheritance (not explicitly placed). Determines ordering in canonical form. |

## Common flag combinations

| Flags | Meaning |
|---|---|
| CI \| OI | Inherit to everything — containers and non-containers, recursively. |
| CI | Inherit to containers only, recursively. |
| OI | Inherit to non-containers only. Containers receive it as inherit-only. |
| CI \| OI \| IO | Inherit to everything, but do not apply to this object. |
| CI \| OI \| NP | Inherit to immediate children only. |
| CI \| NP | Inherit to immediate child containers only. |
| (none) | No inheritance. Applies only to this object. |

## CREATOR OWNER and CREATOR GROUP

Two well-known SIDs receive special treatment during inheritance:

- **CREATOR OWNER (`S-1-3-0`)** — when an ACE with this SID is inherited by a child object, the SID is replaced with the SID of the principal who created the child (the owner of the new object).

- **CREATOR GROUP (`S-1-3-1`)** — replaced with the primary group SID of the creating principal.

Substitution happens at inheritance time. The resulting ACE on the child contains the resolved SID, not the placeholder.

## Inheritance algorithm

When a new object is created, its SD is computed from up to three sources:

1. **Parent SD** — provides inheritable ACEs.
2. **Creator SD** — an explicit SD provided by the caller (if any).
3. **Creator token** — provides the default owner, primary group, and default DACL.

### Owner

If the creator SD specifies an owner, use it. Otherwise, use the token's owner SID.

### Group

If the creator SD specifies a group, use it. Otherwise, use the token's primary group SID.

### DACL

The DACL is computed by merging explicit ACEs from the creator SD with inheritable ACEs from the parent SD:

- If no creator SD is supplied and the parent has inheritable ACEs: the new object's DACL consists entirely of inherited ACEs from the parent.

- If no creator SD is supplied and the parent has no inheritable ACEs: the new object's DACL is the token's default DACL.

- If a creator SD is supplied with a DACL:
  - Explicit ACEs from the creator SD are preserved.
  - If the creator SD's DACL is not protected (SE_DACL_PROTECTED not set) and auto-inheritance is enabled: inheritable ACEs from the parent are appended after the explicit ACEs.
  - If the creator SD's DACL is protected: parent inheritance is blocked. Only the creator's explicit ACEs are used.

In all cases, the resulting DACL is post-processed:

- CREATOR OWNER / CREATOR GROUP SIDs are substituted with the actual owner and group.
- Generic rights in inherited ACEs are mapped to object-specific rights via the object type's GenericMapping.
- The INHERITED_ACE flag is set on all ACEs that came from the parent.

### SACL

Computed identically to the DACL, substituting SACL for DACL throughout. The token has no "default SACL" — if no creator SACL is supplied and the parent has no inheritable SACL ACEs, the new object has no SACL.

## Eager evaluation

Inheritance is eager. The new object's SD is fully computed at creation time. There is no lazy inheritance — the kernel MUST NOT walk up the directory tree at access time to find inheritable ACEs.

A consequence of eager evaluation: modifying an inheritable ACE on a parent object does not automatically update existing children. Existing children retain the SD they were created with. Propagating the change to descendants is an explicit operation outside the scope of this specification. Children with SE_DACL_PROTECTED or SE_SACL_PROTECTED set MUST be skipped during any re-propagation.
