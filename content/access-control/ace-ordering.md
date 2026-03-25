---
title: How ACE Ordering Affects Access Decisions
type: concept
order: 60
---

AccessCheck walks the DACL from top to bottom. It does not reorder, sort, or prioritize ACEs — it evaluates them in exactly the order they appear. This means the order you place ACEs in the DACL directly determines the outcome of access decisions.

> [!WARNING]
> Getting the order wrong is one of the most common access control mistakes. A deny rule placed after an allow rule may never take effect.

## The canonical ordering

The standard ACE ordering is:

1. **Explicit deny ACEs**
2. **Explicit allow ACEs**
3. **Inherited deny ACEs**
4. **Inherited allow ACEs**

This ordering exists for two reasons:

**Denies before allows** ensures that deny rules are always evaluated first. If a principal is explicitly denied access, that denial takes effect before any allow rule can grant it. This makes deny ACEs reliable — you can always block a specific principal regardless of what allow rules exist later in the DACL.

**Explicit before inherited** ensures that rules set directly on the object take precedence over rules inherited from a parent. If a directory grants Domain Users read access, but a specific file within it denies read access to a particular user, the file's explicit deny should win. Placing explicit ACEs before inherited ACEs guarantees this.

## Order changes the result

Consider three ACEs targeting the same object — a deny for Bob and allows for Domain Users and Administrators. Bob is a member of Domain Users.

**Correct ordering (deny first):**

```
Deny   bob            FILE_WRITE_DATA
Allow  Domain Users   FILE_READ_DATA | FILE_WRITE_DATA
Allow  Administrators FILE_ALL_ACCESS
```

Bob requests `FILE_WRITE_DATA`. AccessCheck hits the deny ACE first — denied. The allow for Domain Users is never reached for that right. Bob cannot write to this file.

**Incorrect ordering (allow first):**

```
Allow  Domain Users   FILE_READ_DATA | FILE_WRITE_DATA
Deny   bob            FILE_WRITE_DATA
Allow  Administrators FILE_ALL_ACCESS
```

Bob requests `FILE_WRITE_DATA`. AccessCheck hits the allow for Domain Users first — Bob is a member, so `FILE_WRITE_DATA` is granted. The deny ACE is never reached because the right was already resolved. Bob can write to the file despite the deny rule.

The same three ACEs, the same principals, the same rights — but a different result because of the order.

## Inherited ACEs come last

When an object inherits ACEs from its parent, those ACEs are placed **after** the object's own explicit ACEs. This ensures that the object's local policy always takes precedence.

Consider a directory with an inheritable allow for Everyone:

```
Directory DACL:
  Allow  Everyone   FILE_READ_DATA   (inheritable)
```

A file in that directory has an explicit deny:

```
File DACL:
  Deny   contractors   FILE_READ_DATA        (explicit)
  Allow  Everyone      FILE_READ_DATA        (inherited from parent)
```

A member of the contractors group requests read access. The explicit deny is evaluated first — denied. The inherited allow never applies.

If the inherited ACE somehow appeared before the explicit deny, the contractor would be granted access — the local policy would be overridden by the parent's. The canonical ordering prevents this.

## Tools enforce the ordering

When you use standard tools to modify a DACL, they place ACEs in canonical order automatically. Explicit deny ACEs go to the top, explicit allow ACEs follow, and inherited ACEs remain at the bottom.

If you construct a DACL manually or programmatically, you are responsible for getting the order right. AccessCheck does not validate or reorder the DACL — it trusts whatever order it finds.
