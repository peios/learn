---
title: Null DACL vs Empty DACL
type: concept
order: 70
---

A DACL can be **null** (absent from the security descriptor) or **empty** (present but containing zero ACEs). These sound similar but have opposite security implications.

## Null DACL — no access control

> [!WARNING]
> A null DACL grants **all access to everyone**. It is not "no permissions set" — it is "no access control at all." This is almost never what you want.

A null DACL means the security descriptor has no discretionary access control list at all. When AccessCheck encounters a null DACL, it **grants all requested rights to everyone**. There are no rules to evaluate, so nothing is denied.

This is not "default permissions." It is not "inherit from parent." It is no access control at all. Every principal — every user, every service, every process on the machine — gets full access to the object.

A null DACL is almost never what you want. It cannot be audited in a meaningful way (there are no rules to match against), it cannot be partially tightened (there is no list to add entries to — you must create a DACL from scratch), and it is invisible in a way that explicit rules are not. A tool listing the object's permissions would show no DACL rather than a permissive rule.

## Empty DACL — deny everyone

An empty DACL is a DACL that exists but contains no ACEs. When AccessCheck walks it, there are no entries to match — no allow ACEs to grant rights and no deny ACEs to explicitly block them. Since rights must be explicitly granted, the result is that **all access is denied**.

The one exception is the owner's implicit rights. If the requesting token's user SID matches the object's owner SID, the owner still receives `READ_CONTROL` and `WRITE_DAC` by default. This means the owner can read the security descriptor and add ACEs to the DACL to restore access.

An empty DACL is a legitimate (if uncommon) configuration. It creates an object that only the owner can interact with — and even then, only to read the SD and modify the DACL.

## What to use instead of a null DACL

If you want broad access to an object, write an explicit allow ACE:

```
Allow  S-1-1-0 (Everyone)   GENERIC_READ | GENERIC_WRITE
```

This achieves what a null DACL might have been intended for, with critical advantages:

- **Visible** — the rule shows up when anyone inspects the security descriptor
- **Auditable** — audit ACEs in the SACL can match against the access
- **Revocable** — the ACE can be removed or narrowed without rebuilding the DACL from scratch
- **Scoped** — you can grant broad read access without granting write or delete

An explicit permissive ACE is a conscious, documented decision. A null DACL is the absence of a decision.
