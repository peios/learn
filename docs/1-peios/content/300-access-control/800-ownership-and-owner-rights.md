---
title: Understanding Ownership and Owner Rights
type: concept
description: What the owner SID grants by default, how OWNER RIGHTS overrides it, and how ownership is transferred.
---

Every security descriptor has an **owner SID**. Ownership is not just a label — it confers real rights. The owner of an object can always read its security descriptor and modify its DACL, even if no ACE in the DACL explicitly grants them access.

This guarantee exists so that no object becomes permanently inaccessible. If a DACL is misconfigured and locks everyone out, the owner can still fix it.

## What the owner gets by default

When AccessCheck evaluates a request from the object's owner, it implicitly grants two standard rights:

| Right | What it allows |
|---|---|
| **READ_CONTROL** | Read the security descriptor (see who has access) |
| **WRITE_DAC** | Modify the DACL (change who has access) |

These rights are granted regardless of what the DACL says. The owner does not need an ACE to receive them.

The owner does **not** automatically get other rights. Owning a file does not implicitly grant the right to read or write its contents — those rights must come from the DACL or from privileges. Ownership is about control over the security policy, not blanket access to the object.

## Overriding the defaults with OWNER RIGHTS

The default implicit grants can be overridden by placing an **OWNER RIGHTS ACE** (`S-1-3-4`) in the DACL. When AccessCheck finds this ACE, it replaces the default owner grants with whatever the ACE specifies.

This can **restrict** the owner:

```
Allow  S-1-3-4 (OWNER RIGHTS)  READ_CONTROL
```

The owner can read the security descriptor but cannot modify the DACL. This is useful for objects where an administrator wants to prevent the owner from changing the access rules.

It can also **expand** the owner's implicit rights:

```
Allow  S-1-3-4 (OWNER RIGHTS)  READ_CONTROL | WRITE_DAC | DELETE
```

The owner gets the defaults plus the ability to delete the object.

Without an OWNER RIGHTS ACE, the defaults (READ_CONTROL + WRITE_DAC) apply. The OWNER RIGHTS ACE is the mechanism for fine-tuning what ownership means on a specific object.

## How ownership is set

**At creation.** When a new object is created, the owner is set from the creating token — typically the token's user SID.

**By transfer.** A principal with `WRITE_OWNER` access on the object can change the owner SID. This access can come from the DACL or from a privilege.

**By claiming.** A principal with the `SeTakeOwnershipPrivilege` can claim ownership of any object, regardless of the current DACL. This is the administrative escape hatch — when an object's access is misconfigured and no one can reach it, an administrator with this privilege can take ownership and then fix the DACL.

## The recovery path

Ownership and `SeTakeOwnershipPrivilege` together ensure that there is always a way to recover access:

1. The administrator takes ownership of the object (using `SeTakeOwnershipPrivilege`)
2. As the new owner, they receive READ_CONTROL and WRITE_DAC implicitly
3. They modify the DACL to restore correct access rules

This is a deliberate two-step process. `SeTakeOwnershipPrivilege` does not grant the ability to read or modify the object's contents — it only grants ownership. The administrator must then use the owner's implicit WRITE_DAC to fix the DACL, and only then can they (or others) access the object through normal means.
