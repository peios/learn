---
title: Narrowing layers
type: concept
description: Three layers of the access check can narrow what the DACL plus privileges granted — the restricted-token pass, confinement, and central access policies. Each is a strict intersection. This page covers the three layers in their pipeline order, the rules for what bypasses each one, and how they compose.
related:
  - peios/access-decisions/overview
  - peios/access-decisions/privileges-in-the-pipeline
  - peios/tokens/restricted-tokens
  - peios/confinement/overview
  - peios/central-access-policies/overview
---

The access check has three layers that **narrow** the running granted mask: the restricted-token pass at step 10, the confinement pass at step 11, and the central access policy evaluation at step 12. Each runs after the DACL walk has produced an initial grant. Each is a strict intersection — they can only remove bits from the grant, never add. A right granted by some earlier layer (the DACL or a privilege) may be lost in these passes. A right not granted by an earlier layer cannot be created by them.

This page covers the three layers in pipeline order, the rules for what does and does not bypass each one, and how they compose when more than one is active.

## The order, and why it matters

| Step | Layer | What it intersects against |
|---|---|---|
| 10 | Restricted-token pass | A DACL walk using only the token's `restricted_sids` |
| 11 | Confinement pass | A DACL walk using only the token's confinement SID set |
| 12 | CAAP evaluation | The effective DACLs of each referenced central access policy |

The order is fixed. The restricted pass runs first because it is identity-flavoured — the kernel is asking "would the restricted SIDs alone have been granted this?". Confinement runs next because it is policy applied to the code as a whole, and the inputs to the confinement check are bigger than just the SIDs. CAAP runs last because it can layer multiple policies on top of everything.

A key consequence of the order: a right that survives all three is granted. A right denied by any one is denied. Composition is conjunction — every active narrowing layer must permit the right for it to remain in the final granted mask.

## Restricted-token pass

If the token is not restricted (its `restricted_sids` list is empty), this step is skipped entirely. If it is, the kernel runs the DACL walk a second time, using only `restricted_sids` as the matching set. The `user_sid` does not participate. The `groups` list does not participate. Only entries in `restricted_sids` count.

The result is `granted_restricted` — what the DACL would grant if the token had only its restricted SIDs. This mask is intersected with the running grant from step 8: `granted = granted & granted_restricted`.

**Privileges bypass this pass.** After the intersection, bits that were granted by privileges in steps 4 or 9 are **restored** to the running grant. The reason is that privileges are explicit and authorised independently of identity-based narrowing — a restricted token holder with `SeBackup` enabled and `BACKUP_INTENT` set can still exercise the privilege.

**The write-restricted variant** narrows only write-category bits. Reads and execute come from the step-8 grant alone. The bits in the write category are determined by the object's GenericMapping — for files, that is whatever GENERIC_WRITE maps to. See [Restricted and write-restricted tokens](~peios/tokens/restricted-tokens) for the full mechanics, including the `user_deny_only` flag that write-restricted tokens carry.

The restricted-token pass is **the program's narrowing layer**. It is set up in code: a sandbox launcher FilterTokens its own token down to a restricted version before launching the constrained work. The code is choosing to give itself less authority. Privileges, being explicit, are not subject to this self-imposed narrowing.

## Confinement pass

If `confinement_sid` is null on the token, this step is skipped. If it is set, and `confinement_exempt` is false, the kernel runs the DACL walk a third time, against the confinement identity:

- The user SID is replaced with `confinement_sid`.
- The groups list is replaced with the `confinement_capabilities` list.
- Group attributes are ignored — presence-based matching only.
- Owner implicit rights are **not** applied (the confined application is not the owner).

The result is `granted_confinement` — what the DACL would grant to a "fresh" caller whose entire identity is the confinement SID plus the declared capabilities. This is intersected with whatever the running grant is at this point.

**Privileges do *not* bypass this pass.** Bits granted by privileges in steps 4 or 9 are subject to the confinement intersection like any other bit. A confined token with `SeBackup` enabled and `BACKUP_INTENT` set can have its privilege grant stripped by confinement.

This is the major difference from the restricted-token pass. Restricted tokens trust their own author to use privileges responsibly; confinement does not trust the confined code at all. Confinement is policy applied *to* the application, not by it, so the application cannot escape via privilege exercise. See [Confinement](~peios/confinement/overview).

The `confinement_exempt` flag opts a specific token out of the confinement check. It is set very rarely — only by tools that legitimately need to step outside their own confinement.

## CAAP evaluation

Central access policies are the third narrowing layer. The mechanism: each `SYSTEM_SCOPED_POLICY_ID` ACE in the object's SACL references a policy by SID. The kernel looks up each policy in its policy cache (populated by authd) and evaluates the policy's rules.

A policy contains zero or more rules, each with:

- An optional **applies-to** expression — a conditional expression evaluated against the object's resource attributes. If the expression evaluates UNKNOWN or FALSE, the rule is skipped for this object. If it evaluates TRUE (or is absent), the rule applies.
- An **effective DACL** — a DACL that gets evaluated through a recursive sub-AccessCheck against the calling token. The result is intersected with the running grant.
- An optional **effective SACL** — audit ACEs that are collected for the eventual audit walk.
- Optional **staged DACL / staged SACL** — same content, but evaluated in parallel for testing purposes without affecting the actual grant.

For each applicable rule, AccessCheck recursively evaluates the effective DACL using a synthetic SD (where the DACL is the policy's DACL, the SACL has `SYSTEM_SCOPED_POLICY_ID` ACEs stripped to prevent recursion, and the object's owner/group are preserved). The result is intersected with the running grant.

**Privileges do not bypass CAAP** — bits granted by privileges are subject to CAAP narrowing like every other bit. The reason: CAAP is administrator-imposed policy, layered on top of object-level DACLs, and a privilege that bypassed it would defeat the model.

**Staging mismatches are surfaced separately.** If the staged DACL would have produced a different result, the access check sets the `staging_mismatch` flag in its output. The actual granted mask uses the effective DACL only — the staged DACL never affects what the caller gets. The flag is informational, for policy testing and rollout.

**The recovery policy** is the kernel's fallback when a referenced policy SID is not in the cache. Rather than fail-open (grant everything as if the policy were absent) or fail-closed (deny everything), the kernel applies a hardcoded recovery policy that grants `GENERIC_ALL` to `BUILTIN\Administrators`, `SYSTEM`, and `OWNER_RIGHTS`. This way, administrative access survives a missing-policy condition; ordinary access does not.

The full mechanism — applies-to expressions, staged vs effective semantics, distribution from authd — lives in [Central access policies](~peios/central-access-policies/overview). For this page, what matters is that CAAP is the last narrowing layer, that it is privilege-blind, and that it produces the staging-mismatch signal.

## Composition

When more than one narrowing layer is active, they compose in pipeline order:

```mermaid
flowchart LR
    A["Step 8 grant (DACL + step-4 privileges)"] -->|step 9| B["+ SeTakeOwnership if needed"]
    B -->|step 10| C["intersect with restricted pass (if restricted)"]
    C -->|step 4/9 privileges restored| D["intermediate grant"]
    D -->|step 11| E["intersect with confinement pass (if confined)"]
    E -->|step 12| F["intersect with each CAAP rule"]
    F --> G["final granted mask"]
```

A token can be all three at once: restricted, confined, and accessing an object with CAAP references. Each layer fires; the running grant is intersected three times; the final grant is what survives all of them. Each is conservative — they can only remove. A right that survives is one that all three layers permitted, on top of whatever the DACL and privileges produced.

A token can be one and not the others. A non-restricted, non-confined token accessing a CAAP-bound object faces only step 12. A restricted but not confined token accessing a non-CAAP object faces only step 10. The skipped steps are no-ops.

## Practical examples

**Restricted token, no confinement, no CAAP.** A sandbox launcher created a restricted version of its own token and ran the workload as that. The workload's accesses go through the DACL walk normally, then through the restricted pass (intersection against `restricted_sids`), then through confinement (no-op, token is not confined), then CAAP (no-op, object has no policy). Privilege-granted bits from steps 4/9 are restored after the restricted pass — the workload can still exercise its privileges.

**Confined application, no restricted SIDs, no CAAP.** A service was launched with confinement policy attached by the service manager. The accesses go through the DACL walk normally, then skip the restricted pass (no `restricted_sids`), then through confinement (intersection against the confinement identity). Privilege-granted bits are subject to the intersection — if the confinement DACL would not have granted them, they are lost.

**Plain DACL'd object with CAAP, ordinary token.** A file with a `SYSTEM_SCOPED_POLICY_ID` ACE in its SACL. The DACL walk produces an initial grant. Restricted and confinement passes are no-ops. CAAP looks up the referenced policy, evaluates each applicable rule, intersects each rule's effective DACL with the running grant. The final grant is the DACL-walk result narrowed by every applicable CAAP rule.

**All three.** A restricted, confined token accessing a CAAP-bound object. Every narrowing layer is active. The final grant has to survive all of them. This is rare in practice — restricted and confined are both belts-and-braces approaches — but it is what the model permits.

## What the narrowing layers do *not* do

A few clarifications that come up:

- **They do not run on objects that have no SACL.** Restricted tokens and confinement narrowing depend on the **token**, not on the SACL. The DACL walk happens; the restricted/confinement pass runs based on token state. Only CAAP requires SACL ACEs to fire.
- **They do not change the DACL itself.** The narrowing layers compute a *result*, not a rewritten DACL. The same DACL on the same object produces different results for a normal token vs a restricted one vs a confined one — and the DACL itself is unchanged.
- **They do not affect audit.** Audit ACEs in the SACL fire based on the *final* granted mask, not on what was granted by the DACL walk alone. An audit ACE that fires on success will fire only if the right survives all narrowing layers and ends up granted. A failure ACE fires only if the right would have been granted by some earlier layer but was stripped by a later one.
- **They do not affect outputs other than the granted mask.** Restricted-token and confinement passes do not produce their own audit events. CAAP produces the staging-mismatch flag and contributes effective SACL ACEs to the audit walk; it does not produce a separate "CAAP narrowed this" event.

## Why three different layers?

A reasonable question: if all three are intersections, why not just one? The reason is that they are intersections against different things, set by different audiences, with different bypass rules.

| Layer | Set by | Intersects against | Privileges bypass? |
|---|---|---|---|
| Restricted token | The application (in code) | The application's own restricted SID list | **Yes** |
| Confinement | The system administrator (policy) | The confinement SID + declared capabilities | No |
| CAAP | The directory administrator (policy) | Centrally-defined access rules | No |

The three sources of narrowing — the application, the local administrator, the directory — produce different layers because they answer different questions. "Does this code restrict its own authority?" is a programming concern; "is this service running in a sandbox?" is a deployment concern; "is this resource under enterprise data-protection policy?" is an organisational concern. Each layer handles its question.

The privilege-bypass split is the most consequential difference. Restricted tokens are application-internal and the application is trusted to use privileges responsibly. Confinement and CAAP are external policy and the bypassed code is not trusted; privileges must not be an escape route.
