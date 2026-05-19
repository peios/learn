---
title: Central access policies
type: concept
description: A central access policy is an additional layer of access restriction defined once and applied to many objects. Objects reference policies by SID in their SACL; the access check evaluates each referenced policy and intersects the result with the object's own DACL. CAAP never widens access — it only narrows.
related:
  - peios/central-access-policies/policies-and-rules
  - peios/central-access-policies/evaluation
  - peios/central-access-policies/staged-policies
  - peios/central-access-policies/distribution-and-recovery
  - peios/access-decisions/overview
  - peios/security-descriptors/the-sacl
---

A **central access policy** — CAAP for short — is access policy defined once, centrally, and applied to many objects without per-object configuration. Where a DACL says "this is the policy for *this* object", a CAAP says "this is the policy for *every* object that references this policy". Objects reference a CAAP by including a `SYSTEM_SCOPED_POLICY_ID_ACE` in their SACL, naming the policy's SID. When the access check evaluates the object, it looks up each referenced policy and runs its rules in addition to the object's own DACL.

The model is conservative by design: **CAAP never widens access — it only narrows**. Whatever the object's DACL would have granted, a CAAP can take away. Nothing a CAAP says can let a caller through that the DACL would have denied. This makes CAAP safe to layer: you can apply a policy to many objects without worrying about it accidentally granting access that the underlying ACLs intended to refuse.

This page covers what CAAP is, when it makes sense to use, and the model at a conceptual level.

## What CAAP solves

The problem CAAP exists for: organisations whose access rules span many objects in a way that does not fit the per-object DACL model. Examples:

- "Files classified Top Secret can only be read by users in the Cleared group, regardless of what the file's individual DACL says."
- "Database records belonging to the EU customer base require GDPR-compliant access rules, applied uniformly."
- "Engineering documents must be readable only on devices with up-to-date security software."

In each case, the rule is defined once at the organisational level. Each object that the rule applies to does not need to know the rule itself; it just needs to reference the policy by SID. The policy's content is stored centrally (in the directory or registry, distributed by authd) and applied at access-check time.

If you tried to express these rules directly in object DACLs, you would have to update every covered object whenever the rule changed. With CAAP, the policy is updated once and the next access check on any referencing object sees the new version.

## How an object references a policy

An object opts into a CAAP by including a `SYSTEM_SCOPED_POLICY_ID_ACE` in its SACL. The ACE has a single SID — the policy's identifier. Multiple `SYSTEM_SCOPED_POLICY_ID_ACE` entries in one SACL apply multiple policies; each is looked up independently and each contributes its own restriction to the access check.

The SACL is where the reference lives because the policy reference is system-level information — not something the object's owner should be able to override unilaterally. Modifying the SACL requires `ACCESS_SYSTEM_SECURITY`, which is privilege-gated (see [The SACL](~peios/security-descriptors/the-sacl)). An object owner can rewrite the DACL freely; they cannot add or remove CAAP references without administrative authority.

Inherit-only `SYSTEM_SCOPED_POLICY_ID_ACE` entries are skipped during evaluation, just like other inherit-only ACEs. Their purpose is to propagate the policy reference to child objects at creation time.

## The model in one paragraph

A CAAP is a named bundle of **rules**. Each rule has:

- An **applies-to expression** (optional) — a conditional expression evaluated against the object's resource attributes. If it evaluates to TRUE, the rule applies to this object; if to FALSE or UNKNOWN, the rule is skipped. If the expression is absent, the rule applies to every object that references the policy.
- An **effective DACL** — a DACL whose rules are run against the calling token via a recursive sub-AccessCheck. The result is intersected with the running grant from the rest of the pipeline. A bit granted by the rule's DACL is preserved; a bit not granted is dropped.
- An **effective SACL** (optional) — audit ACEs merged into the access check's SACL walk, so the policy can contribute its own audit rules.
- A **staged DACL** and **staged SACL** (both optional) — proposed replacements for the effective DACL and SACL, evaluated in parallel without affecting access. Used for policy testing. See [Staged policies](~peios/central-access-policies/staged-policies).

The full rule structure is in [Policies and rules](~peios/central-access-policies/policies-and-rules). The evaluation mechanics — how rules compose, where they fire in the access pipeline, the no-recursion rule — are in [Evaluation](~peios/central-access-policies/evaluation).

## The narrowing-only guarantee

Every CAAP rule's effective DACL is **intersected** with the running grant. The intersection is conjunctive: only bits granted by both sides remain. A bit the rule's DACL would not grant is dropped, regardless of how the object's own DACL had decided it.

This makes CAAP safe by construction. You cannot accidentally write a CAAP that grants something. The most permissive CAAP rule possible would be one whose effective DACL grants `GENERIC_ALL` to `Everyone` — and even that does not grant anything to a caller whose underlying DACL did not. The intersection is the floor of safety: CAAP can only ever restrict, never relax.

The implications:

- **Adding a CAAP to an existing object cannot increase access.** Worst case, the new policy contributes nothing additional. Best case, it restricts access in the intended way.
- **A misconfigured CAAP cannot grant. It can only deny too aggressively.** A bug in a policy's effective DACL means objects become harder to reach, not easier.
- **The order of CAAP evaluation does not matter.** Intersection is commutative. Two CAAP rules on one object produce the same final grant whether you evaluate rule A then rule B or B then A.

This is the property that makes CAAP suitable as a deployment-wide policy mechanism. Administrators can layer policies without coordinating because the layers can only narrow.

## Multiple policies, multiple rules

A single SACL can include several `SYSTEM_SCOPED_POLICY_ID_ACE` entries, each referencing a different policy. Each policy can contain several rules. All of them apply. The running grant from the rest of the pipeline is intersected against each rule's effective DACL in turn. The final grant is what survives every applicable rule across every applicable policy.

In practice, a single object is usually covered by zero or one policy. Multiple policies on the same object means the policies cover orthogonal axes — "Classification" plus "Compliance", say — where each axis is a separate policy. The CAAP author keeps each policy's rules focused on one axis and lets layering produce the combined effect.

## Check-at-open semantics

CAAP changes are applied at the **next** access check. Already-open handles do not see CAAP changes. A handle opened ten minutes ago has its granted mask cached on the file descriptor; the access check that granted it was the one that mattered, and a CAAP update afterwards has no effect on that handle.

This is the standard check-at-open model that [File access (FACS)](~peios/file-access/the-handle-model) uses for all of access control. A user wanting to be sure a CAAP change has taken effect must close existing handles and reopen.

The implication for policy rollout: updating a CAAP does not immediately revoke access from sessions that already have open handles. If the policy update is meant to be enforced retroactively, the deployment needs an out-of-band step — typically session-revocation or service-restart — to drop the existing handles.

## The CAAP catalog lives in the kernel

The kernel maintains a **policy cache** keyed by policy SID. The cache is populated by authd at startup, and updated by `kacs_set_caap` calls when policies change. At access-check time, looking up a referenced policy is a constant-time lookup against this cache.

The cache is empty at boot. Until authd populates it, every CAAP reference resolves to "policy not found" and the recovery policy fires (covered in [Distribution and recovery](~peios/central-access-policies/distribution-and-recovery)). This is why authd populates the cache early in boot, before user-facing services start.

## Where to start

If you want the structure of a policy — the rule layout, applies-to expressions, effective and staged DACL/SACL — read [Policies and rules](~peios/central-access-policies/policies-and-rules).

If you want to know how CAAP fires in the access pipeline and the rules for composition, read [Evaluation](~peios/central-access-policies/evaluation).

If you want to understand the testing model — staged policies that evaluate in parallel without affecting access — read [Staged policies](~peios/central-access-policies/staged-policies).

If you want the operational story — how policies get into the kernel, who calls `kacs_set_caap`, what happens when a referenced policy is missing — read [Distribution and recovery](~peios/central-access-policies/distribution-and-recovery).
