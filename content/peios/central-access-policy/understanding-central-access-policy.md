---
title: Understanding Central Access Policy
type: concept
order: 10
description: How Central Access Policy applies organization-wide access rules that intersect with per-object DACLs.
---

The DACL is per-object — the owner sets it. If an organization's access policy changes ("financial data is now restricted to the Finance and Compliance teams"), an administrator must find every affected object and update its DACL individually.

**Central Access Policy (CAP)** solves this by separating the policy definition from the objects it governs. A policy is defined once in a central location — the registry on a standalone machine, or Active Directory for domain-joined machines. Objects reference the policy by ID. When the policy changes, every object that references it is immediately governed by the new rules, without touching a single security descriptor.

## How it works

A Central Access Policy is a named collection of **rules**. Each rule has:

| Component | Purpose |
|---|---|
| **Applies-to condition** (optional) | A conditional expression that determines which objects this rule governs, based on resource attributes. For example: `@Resource.department == "finance"` |
| **Effective DACL** | The mandatory access rules currently enforced by this rule |
| **Staged DACL** (optional) | A proposed replacement for the effective DACL, used for testing before enforcement |

Objects opt in to a policy by placing a **scoped policy ACE** in their SACL. The ACE identifies the policy by SID. When AccessCheck encounters a scoped policy ACE, it looks up the policy in the kernel's cache and evaluates each applicable rule.

## CAP can only restrict, never expand

The result of CAP evaluation is an **intersection** with the normal DACL evaluation. CAP can only further restrict access — it cannot grant access that the object's own DACL denies.

If the DACL grants read and write, but the applicable CAP rule's effective DACL grants only read, the final result is **read only**. The object's DACL is the ceiling. CAP lowers it.

This AND property means composing multiple policies is safe. Adding a policy never grants access that was not already granted. Each additional policy can only further restrict.

Peios allows multiple scoped policy ACEs on a single object, enabling composable policies — "this object is subject to both the Finance Data policy and the Compliance Retention policy." The AND semantics make this safe.

## Policy distribution

Policies are loaded into a kernel cache at boot and updated when policies change. On a standalone machine, policies come from the registry. On a domain-joined machine, they come from Active Directory via Group Policy.

The kernel cache is keyed by policy SID. AccessCheck reads from the cache during evaluation — there are no external lookups during access decisions.

## Recovery when a policy is missing

If a scoped policy ACE references a policy SID that is not in the kernel cache — because the policy was not loaded, was deleted, or the machine is disconnected from the domain — a **recovery policy** is used instead.

The recovery policy grants full access to:
- The object's owner
- The built-in Administrators group
- SYSTEM

Because CAP is applied as an intersection with the normal DACL, the recovery policy does not reopen access that the object's own DACL already denied. It prevents a missing CAP from further restricting access beyond the object's own DACL. In other words: losing CAP is no worse than having no CAP at all.

The alternative — denying all access on missing policy — would cause a single failed policy push to lock out every affected file on the system.

## Staging

Policy changes are high-stakes. A misconfigured rule can lock out thousands of users from thousands of files. **Staging** lets an administrator test a policy change before enforcing it.

Each CAP rule can carry two DACLs: the effective DACL (currently enforced) and a staged DACL (proposed replacement). AccessCheck evaluates both in parallel:

- The **effective DACL** determines the actual access decision
- The **staged DACL** is shadow-evaluated — its result is computed but does not affect access

If the two results differ, the difference is logged. The log tells the administrator exactly which access rights would change: "user X would lose write access to these 47 files" or "the Contractors group would gain read access to the finance directory."

The administrator reviews the impact, adjusts if needed, and promotes the staged DACL to effective when satisfied. This makes policy changes auditable and reversible before they take effect.
