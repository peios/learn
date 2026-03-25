---
title: Understanding Conditional ACEs
type: concept
order: 10
---

A regular ACE applies whenever the SID matches — if the token contains the ACE's SID, the rule takes effect. A **conditional ACE** adds a second requirement: an expression that must evaluate to true for the ACE to apply.

This allows access rules that go beyond group membership. "Allow read access to Domain Users *if* the user's department is Engineering" is something a regular ACE cannot express. A conditional ACE can.

## What a conditional ACE looks like

A conditional ACE has the same components as a regular ACE — type, SID, access mask — plus an **expression**:

```
Allow  Domain Users  FILE_READ_DATA
  IF (@User.department == "Engineering")
```

When AccessCheck encounters this ACE, it first checks whether the SID matches (is the token a member of Domain Users?). If it does, it then evaluates the expression. Only if both match does the ACE take effect.

If the SID matches but the expression evaluates to false, the ACE is skipped — as if it didn't exist. AccessCheck moves on to the next ACE.

## Expressions

Conditional ACE expressions can reference three kinds of data:

| Source | Syntax | Where it comes from |
|---|---|---|
| **User claims** | `@User.department` | Key-value pairs on the token, set from directory attributes at authentication |
| **Device claims** | `@Device.managed` | Key-value pairs from the machine's token (compound identity) |
| **Resource attributes** | `@Resource.classification` | Key-value pairs attached to the object via special ACEs in the SACL |

Expressions support standard operators:

| Operator | Meaning |
|---|---|
| `==`, `!=` | Equality and inequality |
| `<`, `>`, `<=`, `>=` | Ordering comparisons |
| `Contains`, `AnyOf`, `MemberOf` | Set membership tests |
| `Exists`, `Not_Exists` | Whether a claim or attribute is present |
| `&&`, `\|\|`, `!` | Logical AND, OR, NOT |

These can be combined to form complex conditions:

```
Allow  Authenticated Users  FILE_READ_DATA
  IF (@User.department == "Engineering" && @Resource.classification != "restricted")
```

## Three-valued logic

Expressions evaluate to one of three values: **TRUE**, **FALSE**, or **UNKNOWN**.

UNKNOWN occurs when the expression references a claim or attribute that does not exist. If a conditional ACE checks `@User.department` but the token has no `department` claim, the expression evaluates to UNKNOWN — not true, not false.

How UNKNOWN is handled depends on the ACE type:

| ACE type | Expression result: TRUE | Expression result: FALSE | Expression result: UNKNOWN |
|---|---|---|---|
| **Allow** | ACE applies (grants access) | ACE skipped | ACE skipped |
| **Deny** | ACE applies (denies access) | ACE skipped | ACE skipped |

Both allow and deny ACEs skip on UNKNOWN. This is a safety property:

- An allow ACE with UNKNOWN does not grant access — missing data cannot accidentally open a door
- A deny ACE with UNKNOWN does not deny access — missing data cannot accidentally lock someone out

The access decision proceeds as if the conditional ACE were not there. Other ACEs in the DACL still apply normally.

## Why UNKNOWN matters

Consider a rule intended to restrict access to a classified resource:

```
Deny  Everyone  FILE_READ_DATA
  IF (@Resource.classification == "top-secret")
```

If the object has no `classification` resource attribute, the expression evaluates to UNKNOWN and the deny does not apply. This is the correct behavior — the absence of a classification should not trigger a rule designed for classified objects.

But it means the deny rule only works when the resource attribute is actually set. If an administrator forgets to tag an object with its classification, the deny rule is inert. Three-valued logic is safe but demands that claims and attributes are populated correctly.

## Conditional ACEs in the DACL walk

Conditional ACEs participate in the normal DACL walk. They are evaluated in order alongside regular ACEs. The only difference is the expression check — if the expression is false or unknown, the ACE is skipped and the walk continues.

```
DACL:
  Deny   Everyone      FILE_WRITE_DATA  IF (@Resource.classification == "readonly")
  Allow  Domain Users  FILE_READ_DATA | FILE_WRITE_DATA
  Allow  Contractors   FILE_READ_DATA   IF (@User.clearance >= 2)
```

AccessCheck walks this top to bottom as usual. The conditional deny fires only if the resource is classified as readonly. The conditional allow for contractors fires only if the user has sufficient clearance. The unconditional allow for Domain Users always applies when the SID matches.
