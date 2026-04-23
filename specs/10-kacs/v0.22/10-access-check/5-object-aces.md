---
title: Object ACEs and Property-Level Access
---

Object ACEs add a GUID to the ACE that identifies which property or property set the rule applies to. They enable per-property access control on objects with internal structure, such as Active Directory objects.

An object ACE without a GUID (ACE_OBJECT_TYPE_PRESENT not set) behaves identically to a basic ACE.

## Object type lists

To request property-level access, the caller provides an object type list -- a tree of GUIDs representing the properties being requested. Each node tracks its own access state independently.

When no object type list is provided, object ACEs with GUIDs apply globally, as if they were basic ACEs.

When an object type list is provided, any ACE that behaves like a basic ACE applies globally to every node in the tree. This includes ordinary basic ACEs and object ACEs without an `ObjectType` GUID.

## Propagation

Access decisions propagate through the tree in two directions:

**Downward from grants.** When an object ACE grants access to a property set, that grant flows down to all attributes within the set. Each child node independently respects first-writer-wins.

**Upward from grants.** When every attribute within a property set has been granted the same right, that right propagates up to the property set node. Uses per-bit intersection -- a right propagates to the parent only if all siblings share it.

**Upward from denials.** When an object ACE denies access to an attribute, the
denial propagates upward to each ancestor regardless of sibling state. Sibling
nodes are unaffected. Upward denial propagation does not override bits already
decided at an ancestor; each ancestor still applies normal first-writer-wins
for the propagated bits.

**Downward from denials.** When an object ACE denies access to a property set, the denial flows to all attributes within the set, subject to first-writer-wins.

## PRINCIPAL_SELF (S-1-5-10)

PRINCIPAL_SELF is a well-known SID that acts as a placeholder for the object's associated principal. An ACE targeting S-1-5-10 matches the caller if the caller's token represents the same principal as the object.

The caller provides the object's principal SID as the `self_sid` parameter to AccessCheck. If `self_sid` is null, PRINCIPAL_SELF ACEs match nothing.

PRINCIPAL_SELF follows the same deny-only rules as other SIDs: if the caller's matching SID is deny-only, PRINCIPAL_SELF matches for deny ACEs but not allow ACEs.

## AccessCheck vs AccessCheckResultList

AccessCheck requires every node to pass -- if any property is denied, the whole request fails. AccessCheckResultList returns a separate verdict per node.

## Object type list validation

KACS validates object type lists strictly:

- The list MUST NOT be empty (when provided).
- The first node MUST be at level 0.
- There MUST be exactly one level-0 node.
- Level gaps (a node at level N+2 following a node at level N) MUST be rejected.
- Duplicate GUIDs MUST be rejected.

> [!INFORMATIVE]
> These validations are stricter than the reference model, which does not specify them. They prevent FindNode from returning the wrong node and prevent level gaps from causing undefined propagation behaviour.
