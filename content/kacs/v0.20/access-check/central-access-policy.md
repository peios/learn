---
title: Central Access Policy
order: 8
---

Central Access Policy (CAP) separates policy definition from the objects it governs. A policy is defined once, centrally. Objects reference the policy by SID via a SYSTEM_SCOPED_POLICY_ID_ACE in their SACL. When the policy changes, every object that references it is immediately governed by the new rules.

## Policy structure

A Central Access Policy is a named collection of rules. Each rule has:

- **An applies-to condition** (optional) — a conditional expression that determines which objects this rule governs, based on the object's resource attributes. If absent, the rule applies to all objects that reference the policy.

- **An effective DACL** — the mandatory access rules enforced by this rule. A real DACL evaluated using the full pipeline.

- **A staged DACL** (optional) — a proposed replacement for the effective DACL, used for testing.

## Evaluation

The result is an AND with the normal DACL evaluation — CAP can only further restrict access, never expand it. If the DACL grants read and write but the applicable CAP rule's effective DACL grants only read, the final result is read.

Multiple SYSTEM_SCOPED_POLICY_ID_ACEs MAY appear in the same SACL, enabling composable policies. The AND semantics make composition safe — every additional policy can only further restrict.

> [!INFORMATIVE]
> The reference model allows one scoped policy ACE per SACL. KACS allows multiple.

For each scoped policy ACE, AccessCheck:

1. Looks up the policy in the kernel's policy cache.
2. For each rule whose `applies_to` condition matches (or has no condition):
   - Evaluates the rule's effective DACL using the full evaluation pipeline (privilege grants, MIC, PIP, DACL walk, restricted tokens, confinement) with one exception: backup/restore intent is not passed (intent is a caller concern, not a policy concern).
   - Intersects the result with the running total.
3. The final CAP result is intersected with the normal DACL result.

## Policy distribution

Policies are pushed to the kernel by authd. The kernel maintains a policy cache keyed by policy SID. On a standalone machine, authd reads policies from the registry. On a domain-joined machine, authd reads policies from Active Directory.

## Recovery policy

When a scoped policy ACE references a policy SID not in the kernel cache (authd failed to push, policy was deleted, machine is disconnected), a hardcoded recovery policy is used:

- ALLOW GENERIC_ALL to BUILTIN\Administrators (`S-1-5-32-544`)
- ALLOW GENERIC_ALL to SYSTEM (`S-1-5-18`)
- ALLOW GENERIC_ALL to OWNER_RIGHTS (`S-1-3-4`)

Because CAP is applied as an intersection, the recovery policy does not widen access beyond the object's own DACL. It prevents missing CAP from further restricting access -- the object's DACL remains the baseline.

## Error handling

If a CAP rule's evaluation produces an error (e.g., malformed DACL in the policy definition), the rule denies all access except rights granted by privileges. Privilege-granted rights are preserved as an escape hatch: an administrator with SeSecurityPrivilege retains the ability to read and modify the SACL to remove the scoped policy ACE.

## Staging

Each CAP rule MAY carry two DACLs: effective (enforced) and staged (proposed). AccessCheck evaluates both in parallel. The staged result does not affect access. If the effective and staged results differ, the difference is logged.

Rules without a staged DACL contribute their effective result to both the effective and staged running totals.
