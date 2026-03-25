---
title: What Are Access Control Lists (DACLs and SACLs)
type: concept
order: 30
description: DACLs control who can access an object, SACLs control auditing and integrity policy.
---

An **Access Control List (ACL)** is an ordered list of rules called **Access Control Entries (ACEs)**. Each ACE is a single statement about what a specific principal can do (or cannot do, or what gets audited) on the object the ACL protects.

Security descriptors contain two ACLs that serve different purposes:

- The **DACL** controls access — who is allowed or denied
- The **SACL** controls system policy — what gets audited and what integrity level is required

## Access Control Entries

Every ACE has three parts:

| Part | What it specifies |
|---|---|
| **Type** | What the ACE does — allow access, deny access, or generate an audit event |
| **SID** | Which principal the rule applies to |
| **Access mask** | Which specific rights are affected |

For example, an allow ACE might say: "Grant `S-1-5-21-...-513` (Domain Users) the right to read data and read attributes on this object."

A deny ACE uses the same structure but blocks access instead of granting it: "Deny `S-1-5-21-...-1028` (bob) the right to write data on this object."

## ACE types

The core ACE types are:

| Type | Where it appears | Purpose |
|---|---|---|
| **Access Allowed** | DACL | Grants specific rights to a principal |
| **Access Denied** | DACL | Blocks specific rights for a principal |
| **System Audit** | SACL | Generates an audit event when a principal accesses (or is denied access to) the object |
| **Mandatory Label** | SACL | Sets the minimum integrity level required to access the object |

There are additional ACE types for more advanced scenarios — conditional ACEs that evaluate expressions, object ACEs that target specific properties, and others — covered in their own documentation.

## DACL: ordering matters

AccessCheck walks the DACL **from top to bottom** and stops evaluating a particular right as soon as it finds a match. This means the order of ACEs directly affects the outcome.

The standard ordering is:

1. **Explicit deny ACEs** — checked first
2. **Explicit allow ACEs** — checked after denies
3. **Inherited deny ACEs** — denies inherited from a parent object
4. **Inherited allow ACEs** — allows inherited from a parent object

Consider a directory where Domain Users are allowed read access, but Bob (a member of Domain Users) should be denied:

```
Deny   S-1-5-21-...-1028 (bob)           FILE_READ_DATA
Allow  S-1-5-21-...-513  (Domain Users)  FILE_READ_DATA
```

AccessCheck encounters the deny first and blocks Bob's read access. The later allow for Domain Users is never reached for Bob.

If the order were reversed — allow first, deny second — Bob would be granted access before the deny was ever evaluated. Ordering is not a suggestion. It determines the result.

## SACL: audit and integrity

The SACL is independent of the DACL. It controls two things:

**Audit ACEs** define what generates audit events. An audit ACE can trigger on successful access, failed access, or both. For example: "Generate an audit event whenever anyone in the Administrators group accesses this object" or "Generate an audit event whenever a write attempt is denied."

**Mandatory labels** set a floor on the integrity level required to modify the object. If an object has a High integrity label, a process running at Medium integrity cannot write to it — regardless of what the DACL says. Integrity enforcement is evaluated before the DACL.

Modifying the SACL requires the `SeSecurityPrivilege`. This separates authority: object owners control who has access (the DACL), but system administrators control what gets audited and what integrity policy applies (the SACL).
