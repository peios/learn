---
title: SD Inheritance
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

- **CREATOR OWNER (`S-1-3-0`)** — when an ACE with this SID is inherited by a child object, the SID is replaced with the owner SID of the new object (as determined by the owner computation above).

- **CREATOR GROUP (`S-1-3-1`)** — replaced with the primary group SID of the creating principal.

Substitution happens at inheritance time. The resulting ACE on the child contains the resolved SID, not the placeholder.

## InheritedObjectType filtering

Object ACEs (`ACCESS_ALLOWED_OBJECT_ACE`, `ACCESS_DENIED_OBJECT_ACE`, etc.) MAY carry an InheritedObjectType GUID. This GUID scopes inheritance to children of a specific class.

The inheritance algorithm accepts an optional `child_class_guid` parameter — the class GUID of the object being created. When processing each inheritable ACE from the parent:

- If the ACE is an object ACE with an InheritedObjectType GUID set, AND `child_class_guid` is provided, AND the two GUIDs do not match: skip the ACE (do not inherit it).
- If the ACE has no InheritedObjectType GUID, or `child_class_guid` is null: inherit normally.

When `child_class_guid` is null (the common case for files and registry keys), InheritedObjectType filtering does not engage — all inheritable ACEs propagate as if the GUID were absent.

> [!INFORMATIVE]
> This mechanism enables class-scoped delegation. A parent container can carry an ACE like "Allow Help Desk to reset passwords, InheritedObjectType = {User class GUID}." Only child objects created with the User class GUID receive the ACE. Other child types (groups, computers) do not. The primary consumer is lpsd and any future subsystem with typed child objects.

## Inheritance algorithm

When a new object is created, its SD is computed from up to four sources:

1. **Parent SD** — provides inheritable ACEs.
2. **Creator SD** — an explicit SD provided by the caller (if any).
3. **Creator token** — provides the default owner, primary group, and default DACL.
4. **Child class GUID** — optional. Filters inheritable object ACEs by InheritedObjectType. Null for files and unclassed registry keys.

### Owner

If the creator SD specifies an owner, use it. Otherwise, use the token's owner SID.

### Group

If the creator SD specifies a group, use it. Otherwise, use the token's primary group SID.

### DACL

The DACL is computed by merging explicit ACEs from the creator SD with inheritable ACEs from the parent SD:

- If no creator SD is supplied and the parent has inheritable ACEs: the new object's DACL consists entirely of inherited ACEs from the parent.

- If no creator SD is supplied and the parent has no inheritable ACEs: the new object's DACL is the token's default DACL.

- If a creator SD is supplied but has no DACL (SE_DACL_PRESENT not set): the new object's DACL is computed as if no creator SD was supplied (inherit from parent, or fall back to the token's default DACL).

- If a creator SD is supplied with a DACL (SE_DACL_PRESENT set):
  - Explicit ACEs from the creator SD are preserved.
  - If the creator SD's DACL is not protected (SE_DACL_PROTECTED not set) and SE_DACL_AUTO_INHERIT_REQ is set on the creator SD: inheritable ACEs from the parent are appended after the explicit ACEs. If SE_DACL_AUTO_INHERIT_REQ is not set, only the creator's explicit ACEs are used (no parent inheritance).
  - If the creator SD's DACL is protected: parent inheritance is blocked. Only the creator's explicit ACEs are used.

In all cases, the resulting DACL is post-processed:

- If the DACL contains any inherited ACEs, set SE_DACL_AUTO_INHERITED on the new SD's control flags. If the DACL contains only explicit ACEs (no parent inheritance occurred), do not set this flag. The same applies to SE_SACL_AUTO_INHERITED for the SACL. These flags allow tools to distinguish auto-inherited DACLs from manually constructed ones.
- CREATOR OWNER / CREATOR GROUP SIDs are substituted with the actual owner and group. This substitution applies only to the ACE's primary SID field — NOT to SID literals inside ApplicationData (conditional expression bytecode). ApplicationData is preserved verbatim during inheritance. No transformation of any kind (SID substitution, generic mapping, offset adjustment) is applied to the bytecode. An implementation MUST NOT scan ApplicationData for CREATOR OWNER SIDs.
- Generic rights in all ACEs (both explicit and inherited) are mapped to object-specific rights via the object type's GenericMapping in the ACE's access mask. Generic rights inside ApplicationData bytecode are NOT mapped. This ensures no unresolved generic bits persist on stored ACE masks.
- The INHERITED_ACE flag is set on all ACEs that came from the parent.

### SE_SERVER_SECURITY — server ACE injection

When the creator SD has SE_SERVER_SECURITY set, the inheritance algorithm appends additional ACEs to ensure the server's own identity retains access to objects it creates on behalf of impersonating clients.

After computing the normal DACL (explicit + inherited ACEs), the algorithm:

1. Reads the caller's **primary token** (`real_cred`, not the impersonation token). This is the server's real identity — it is unaffected by impersonation.
2. Reads the primary token's `default_dacl`.
3. Appends each ACE from the server's default DACL to the new object's DACL. These server ACEs are placed after inherited ACEs. They do NOT have the INHERITED_ACE flag set (they are explicit grants from the server).
4. Generic rights in the server ACEs are mapped via the object type's GenericMapping.

If the caller is not impersonating, the primary token and effective token are the same. SE_SERVER_SECURITY still functions — the server ACEs are appended from the caller's own default DACL. This is harmless (the owner already has implicit rights) but not useful.

The intended use case: a file server (Samba) impersonates a client to create a file. The file's DACL is built from the client's perspective (parent inheritance, client as owner). SE_SERVER_SECURITY ensures the Samba service identity also appears in the DACL, so the service can access the file for future operations without relying on Administrator membership or carefully configured share directory ACLs.

### SACL

Computed identically to the DACL, substituting SACL for DACL throughout. The token has no "default SACL" — if no creator SACL is supplied and the parent has no inheritable SACL ACEs, the new object has no SACL. SE_SERVER_SECURITY does not apply to the SACL.

**Resource attribute inheritance filtering.** When a `SYSTEM_RESOURCE_ATTRIBUTE_ACE` from the parent is being inherited, the algorithm MUST check the `CLAIM_SECURITY_ATTRIBUTE_NON_INHERITABLE` flag (0x0001) on the resource attribute inside the ACE. If the flag is set, the ACE is skipped — it does not propagate to the child. All other inheritable SACL ACEs (audit, mandatory label, scoped policy, resource attributes without NON_INHERITABLE) inherit normally.

## Size limit

If the computed SD (after merging explicit, inherited, and server ACEs) exceeds 64 KB when serialized to self-relative format, the creation MUST fail. The 64 KB limit is the maximum SD size — inheritance does not get an exception. A deeply nested directory tree with many inheritable ACEs can approach this limit.

## Eager evaluation

Inheritance is eager. The new object's SD is fully computed at creation time. There is no lazy inheritance — the kernel MUST NOT walk up the directory tree at access time to find inheritable ACEs.

A consequence of eager evaluation: modifying an inheritable ACE on a parent object does not automatically update existing children. Existing children retain the SD they were created with. Propagating the change to descendants is an explicit operation outside the scope of this specification. Children with SE_DACL_PROTECTED or SE_SACL_PROTECTED set MUST be skipped during any re-propagation.
