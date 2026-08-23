---
title: Object ACEs and Property-Level Access
description: Per-property access control through GUID-scoped ACEs — object type lists, propagation, PRINCIPAL_SELF, and per-node results.
---

An object ACE carries a GUID identifying the property or property set
its rule applies to, which is what enables per-property access control
on objects with internal structure — Active Directory objects, most
obviously. An object ACE with no GUID, meaning
`ACE_OBJECT_TYPE_PRESENT` is unset, behaves exactly like a basic ACE.

## Object type lists

To request property-level access the caller supplies an object type
list: a tree of GUIDs representing the properties being asked for.
Each node carries its own `decided` and `granted` pair and is resolved
independently.

With no list supplied, object ACEs with GUIDs apply globally, as if
they were basic ACEs. With a list supplied, every ACE that behaves
like a basic ACE — ordinary basic ACEs, and object ACEs without an
`ObjectType` GUID — applies to every node in the tree. An object ACE
whose GUID does not appear anywhere in the supplied tree is silently
skipped.

## Propagation

Decisions move through the tree in four ways.

**Downward from grants.** A grant on a property set flows to every
attribute within it, each child node still applying first-writer-wins
for itself.

**Upward from grants.** When every attribute within a property set has
been granted the same right, that right propagates up to the set's
node. The propagation is a per-bit intersection, so a right reaches
the parent only if all siblings share it.

**Upward from denials.** A denial on an attribute propagates to every
ancestor regardless of what its siblings hold, and siblings are
themselves unaffected. Ancestors still apply first-writer-wins to the
propagated bits, so a denial cannot overturn something an ancestor had
already decided.

**Downward from denials.** A denial on a property set flows to every
attribute within it, again subject to first-writer-wins.

## PRINCIPAL_SELF

`PRINCIPAL_SELF` (`S-1-5-10`) is a placeholder for the object's
associated principal. An ACE targeting it matches the caller when the
caller's token represents the same principal as the object, which the
caller establishes by passing the object's principal SID as the
`self_sid` parameter. With a null `self_sid`, `PRINCIPAL_SELF` ACEs
match nothing.

It follows the ordinary deny-only rules: if the caller's matching SID
is deny-only, `PRINCIPAL_SELF` matches deny ACEs but not allow ACEs.

## Scalar and per-node results

`AccessCheck` requires every node to pass, so a denial on any one
property fails the whole request. `AccessCheckResultList` returns a
separate verdict per node.

The scalar result `AccessCheck` returns is the root node's granted
mask. That is equivalent to the intersection across all nodes, but by
construction rather than by computation: upward denial propagation
forces every descendant's denial into all of its ancestors' `decided`
sets, which guarantees the root's granted mask is a subset of every
node's.

## Validation

Object type lists are validated strictly, at parse time. A supplied
list is non-empty; its first node is at level 0; there is exactly one
level-0 node; there are no level gaps, meaning no node at level N+2
following one at level N; and no GUID appears twice.

These checks are stricter than MS-DTYP, which does not specify them.
They exist because a duplicate GUID makes node lookup return the wrong
node, and a level gap makes propagation undefined.
