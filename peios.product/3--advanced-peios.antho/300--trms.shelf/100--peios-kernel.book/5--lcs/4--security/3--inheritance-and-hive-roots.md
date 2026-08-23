---
title: Inheritance and Hive Roots
description: A new key's descriptor is computed from its parent by the KACS inheritance algorithm — plus hive roots and reading or writing a descriptor.
---

## Inheritance at creation

When `reg_create_key` creates a key, its initial Security Descriptor is
computed from the parent's by the KACS inheritance algorithm. LCS
supplies the parent descriptor, the creating token, the registry
generic mapping and the valid-mask bound, and hands the result to the
source to persist. It implements no inheritance logic of its own.

Three things about registry inheritance are worth stating.

**It is static.** The computation happens once, at creation. A later
change to the parent's descriptor does not propagate to children that
already exist. Re-propagating is an explicit administrative action — a
client-side tree walk — not a kernel operation, and there is no code
anywhere in LCS that walks a tree to re-propagate.

**Only `CONTAINER_INHERIT_ACE` matters.** Every registry object is a
container: keys hold subkeys and values. Values are not independent
security objects and have no descriptors of their own; they inherit
their key's access control. `OBJECT_INHERIT_ACE` is never used to
select an ACE for inheritance. It is only cleared on the child copy
when `NO_PROPAGATE_INHERIT_ACE` applies.

**A parent with no inheritable ACEs falls back to the creating token's
default DACL.** That fallback covers the DACL only; there is no default
SACL.

## Hive roots

A hive root has no parent, so it is the top of every inheritance chain
below it and cannot inherit anything itself. Its descriptor is created
by the **source**, on first boot, and LCS enforces whatever the source
stored.

LCS holds no template. There are no hardcoded SIDs, no default hive
root descriptors, and no code that would construct one — searching for
them finds nothing. The defaults that follow are what loregd writes;
they are conventions of the source, not properties of the kernel.

**`Machine\`:**

| Principal | Rights | Inheritance |
|---|---|---|
| SYSTEM | `KEY_ALL_ACCESS` | Container-inherit |
| Administrators | `KEY_ALL_ACCESS` | Container-inherit |
| Authenticated Users | `KEY_READ` | Container-inherit |

**`Users\<SID>\`:**

| Principal | Rights | Inheritance |
|---|---|---|
| the user's SID | `KEY_ALL_ACCESS` | Container-inherit |
| SYSTEM | `KEY_ALL_ACCESS` | Container-inherit |
| Administrators | `KEY_ALL_ACCESS` | Container-inherit |

These mirror Windows HKLM and HKU. A subsystem needing something
tighter — `Machine\Security\`, say — sets an explicit descriptor on its
own subtree root at creation, overriding what it inherited.

Because there is no traverse checking (§5.4.1), a restrictive
descriptor high in the tree protects only the key it is on. Protection
of a subtree comes from the descriptors its keys inherited at creation,
which is exactly why an administrator changing a parent's descriptor
and expecting the subtree to follow will be disappointed.

## Reading and writing descriptors

`REG_IOC_GET_SECURITY` and `REG_IOC_SET_SECURITY` take a
`security_info` bitmask naming which components to act on: owner,
group, DACL, SACL. Zero is `EINVAL`, and so is any unknown flag; both
are rejected before the source is contacted, before transaction
enlistment and before any mutation.

The rights required are computed from every component named. Reading
owner, group or the DACL needs `READ_CONTROL`; reading the SACL needs
`ACCESS_SYSTEM_SECURITY`. Setting owner **or group** needs
`WRITE_OWNER`; setting the DACL needs `WRITE_DAC`; setting the SACL
needs `ACCESS_SYSTEM_SECURITY`. A request naming several components
must hold all the corresponding rights.

A set is a merge, not a replacement. LCS reads only the components
`security_info` names from the supplied self-relative descriptor and
preserves the existing ones. The result must still have an owner; a
merge that would leave the descriptor ownerless is `EINVAL`. A null
group SID stays valid.

Enlisting a descriptor change in a transaction gives it atomicity with
the rest of the transaction's operations. It does not make it
layer-qualified: the change is still a direct mutation on the key, is
still not reverted by deleting a layer, and is simply not applied at
all if the transaction aborts.
