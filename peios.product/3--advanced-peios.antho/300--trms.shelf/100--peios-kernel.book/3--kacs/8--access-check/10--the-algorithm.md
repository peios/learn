---
title: The Algorithm
description: How every layer composes — the definitive statement of the evaluation order, from EvaluateSecurityDescriptor down through AccessCheckCore.
---

The preceding sections describe what each layer of AccessCheck does.
This one describes how they compose, and is the definitive statement
of the evaluation order.

## Pipeline overview

Before the pipeline proper, two things are checked and can fail the
call outright. The token's own invariants are validated — a
`write_restricted` token without `user_deny_only` is rejected as
invalid — and, in the orchestrator, a null descriptor is rejected and
`AccessCheckResultList` is required to have been given an object type
list. A null descriptor presented by an Identification-level token
therefore fails as an invalid parameter rather than as access denied,
because the null check runs first.

The pipeline then runs in this order:

0. **Impersonation level gate.** An impersonation token at
   Identification level is denied immediately. Anonymous tokens
   proceed through the full pipeline.
1. **Input validation.** Reject a descriptor with no owner. A null
   group SID is valid and has no direct effect on the decision.
2. **Generic mapping.** Map generic bits in the desired mask to
   object-specific bits; strip `MAXIMUM_ALLOWED`.
3. **Effective privileges.** Clear the backup and restore bits when
   the corresponding intent flag is absent.
4. **Privilege grants.** Resolve `ACCESS_SYSTEM_SECURITY`, backup and
   restore. Seed `decided`, `granted` and `privilege_granted`.
5. **Pre-SACL walk.** Extract the mandatory integrity label, the PIP
   trust label, resource attributes and scoped policy SIDs from the
   SACL, then enforce MIC and PIP.
6. **Virtual group resolution.** `S-1-3-4` and `S-1-5-10` become
   matchable where the caller is the owner or the object's principal.
7. **Tree initialisation.** Seed each node from the scalar state.
8. **Normal DACL evaluation.** Owner implicit rights, then the walk.
9. **Post-DACL WRITE_OWNER override.** `SeTakeOwnershipPrivilege`
   grants `WRITE_OWNER` if the DACL did not and no mandatory
   mechanism blocked it.
10. **Restricted token pass**, with intersection and privilege
    restoration.
11. **Confinement pass**, with absolute intersection.
12. **CAAP.** Evaluate each applicable rule's DACL through the full
    per-descriptor pipeline and intersect; collect SACLs.
13. **Privilege-use auditing.**
14. **Audit emission**, over the object's SACL and any CAAP SACLs.
15. **Result computation.**

Object type lists are validated at parse time rather than at step 1 —
non-empty, one level-0 node first, no level gaps, no duplicate GUIDs —
so a malformed list never reaches the pipeline. Step 1 re-checks only
emptiness.

Reserved access-mask bits (`0x0CE0_0000`) are rejected wherever a mask
is mapped. That applies to the caller's desired mask *and* to every
ACE mask, so a single ACE carrying a reserved bit aborts the entire
check rather than being skipped.

## EvaluateSecurityDescriptor

Steps 0–11, called once for the normal evaluation and once per CAAP
rule with a synthetic descriptor.

```
EvaluateSecurityDescriptor(
    sd, token, pip_type, pip_trust, desired, mapping,
    object_tree, self_sid, local_claims, privilege_intent
) -> (decided, granted, privilege_granted,
      max_allowed_mode, mapped_desired, resource_attributes,
      policy_sids) | error

    // Step 0: Impersonation level gate.
    if token.token_type == Impersonation
       and token.impersonation_level == Identification:
        return ERROR_ACCESS_DENIED

    // Step 1: Input validation.
    if sd.owner is null:
        return ERROR_INVALID_SECURITY_DESCR

    // Step 2: Generic mapping.
    desired = MapGenericBits(desired, mapping)
    max_allowed_mode = (desired & MAXIMUM_ALLOWED) != 0
    desired = desired & ~MAXIMUM_ALLOWED

    // Step 3: Effective privileges.
    effective_privileges = token.privileges_enabled
    if not (privilege_intent & BACKUP_INTENT):
        effective_privileges &= ~SeBackupPrivilege
    if not (privilege_intent & RESTORE_INTENT):
        effective_privileges &= ~SeRestorePrivilege

    // Step 4: Privilege-based grants.
    decided = 0; granted = 0; privilege_granted = 0

    // ACCESS_SYSTEM_SECURITY is always decided by privilege.
    decided |= ACCESS_SYSTEM_SECURITY
    if (effective_privileges & SeSecurityPrivilege):
        granted           |= ACCESS_SYSTEM_SECURITY
        privilege_granted |= ACCESS_SYSTEM_SECURITY

    if (effective_privileges & SeBackupPrivilege):
        backup_bits = MapGenericBits(GENERIC_READ, mapping)
        decided |= backup_bits; granted |= backup_bits
        privilege_granted |= backup_bits

    if (effective_privileges & SeRestorePrivilege):
        restore_bits = MapGenericBits(GENERIC_WRITE, mapping)
                     | WRITE_DAC | WRITE_OWNER | DELETE
                     | ACCESS_SYSTEM_SECURITY
        decided |= restore_bits; granted |= restore_bits
        privilege_granted |= restore_bits

    // Restore already includes WRITE_OWNER, so when it is active
    // step 9 has nothing left to do. Step 9 is the fallback for
    // when restore is inactive and the DACL did not grant it.

    // Step 5: Pre-SACL walk. mandatory_decided records bits decided
    // by MIC and PIP, so step 9 cannot override them.
    resource_attributes = {}; policy_sids = []; mandatory_decided = 0
    PreSACLWalk(sd, token, pip_type, pip_trust, mapping,
                &decided, &granted, &privilege_granted,
                &mandatory_decided, &resource_attributes,
                &policy_sids)

    // Steps 6-8: owner implicit rights are granted first, inside
    // EvaluateDACL, and the tree is seeded from the already
    // augmented scalar state. Virtual groups are resolved per
    // lookup rather than by building an enriched token.
    EvaluateDACL(sd, token, mapping, object_tree,
                 SidMatchesToken, desired, max_allowed_mode,
                 resource_attributes, local_claims,
                 skip_owner_implicit=false,
                 &decided, &granted)

    // Step 9: Post-DACL WRITE_OWNER override.
    if (desired & WRITE_OWNER) != 0 or max_allowed_mode:
        if (effective_privileges & SeTakeOwnershipPrivilege):
            if not (mandatory_decided & WRITE_OWNER)
               and not (granted & WRITE_OWNER):
                decided |= WRITE_OWNER
                granted |= WRITE_OWNER
                privilege_granted |= WRITE_OWNER
                for each node with WRITE_OWNER ungranted:
                    node.decided |= WRITE_OWNER
                    node.granted |= WRITE_OWNER

    // Step 10: Restricted token pass.
    if token.restricted_sids or token.restricted_device_groups:
        // Restricted identity view: only restricting SIDs, plus
        // S-1-3-4 if the owner is among them and S-1-5-10 if
        // self_sid is. Restricted device groups swap in.
        // Fresh tree, zeroed state.
        EvaluateDACL(sd, restricted_view, mapping, r_tree,
                     SidInRestrictingSids, desired,
                     max_allowed_mode, resource_attributes,
                     local_claims, skip_owner_implicit=false,
                     &r_decided, &r_granted)
        if token.write_restricted:
            write_bits = MapGenericBits(GENERIC_WRITE, mapping)
            granted = (granted & ~write_bits)
                    | (granted & r_granted & write_bits)
        else:
            granted = granted & r_granted
        granted |= privilege_granted        // privileges bypass
        // Same intersection and restoration per node.

    // Step 11: Confinement pass.
    if token.confinement_sid and not token.confinement_exempt:
        // Confinement SID set: confinement_sid plus every
        // capability, presence-based. S-1-3-4 and S-1-5-10 are
        // injected only if the owner or self_sid is in that set.
        EvaluateDACL(sd, token, mapping, c_tree,
                     SidInConfinementSids, desired,
                     max_allowed_mode, resource_attributes,
                     local_claims, skip_owner_implicit=true,
                     &c_decided, &c_granted)
        granted = granted & c_granted       // no privilege bypass
        // Same absolute intersection per node.

    return (decided, granted & root-consistent state,
            privilege_granted narrowed to what survived,
            max_allowed_mode, desired, resource_attributes,
            policy_sids)
```

The returned `privilege_granted` is **narrowed** by what actually
survived the pass — it is intersected with the root's granted mask on
return, and the orchestrator narrows it again against the CAAP result.
A privilege-granted bit that the write-restricted merge or the
confinement intersection removed is therefore no longer part of it,
which matters in two places: the CAAP error escape hatch (§3.8.8) has
fewer bits to preserve, and the audit provenance masks reflect the
narrowed set.

## AccessCheckCore

The orchestrator runs steps 12 through 15.

**Step 12, CAAP.** For each scoped policy SID, look the policy up —
falling back to the recovery policy when it is absent — and for each
rule whose `applies_to` is TRUE or absent, evaluate the rule's
synthetic descriptor through `EvaluateSecurityDescriptor` and
intersect. A rule that errors denies everything except the (already
narrowed) privilege-granted bits. Staged DACLs are evaluated in
parallel into a separate running total; a rule with no staged DACL
contributes its effective result to both.

After all policies, the staged and effective totals are compared and
any difference sets the staging mismatch flag. In result-list mode a
per-node delta sets it too — and so does a scalar delta, since the
comparison is not mode-branched.

**Step 13, privilege-use auditing.** For each of the five provenance
masks — security, backup, restore, take-ownership and relabel:

```
success_bits = provenance & mapped_desired & granted
failure_bits = provenance & mapped_desired & ~granted
```

Nonzero `success_bits` means the privilege was load-bearing: mark it
used on the token, and emit a success event under
`PRIVILEGE_USE_SUCCESS`. Otherwise nonzero `failure_bits` means it was
exercised but did not survive: do **not** mark it used, and emit a
failure event under `PRIVILEGE_USE_FAILURE`. Both zero means no event.
In result-list mode the comparison folds across nodes — success if the
bits survive on any node, failure only if they survive on none.

The whole step is skipped in `MAXIMUM_ALLOWED` mode, so such a request
marks nothing used and emits nothing.

Note that `relabel_granted` is tracked as provenance but is
deliberately excluded from `privilege_granted` itself, so a
relabel-loosened `WRITE_OWNER` is neither restored after the
restricted merge nor preserved by the CAAP error hatch.

**Step 14, audit emission.** Walk the object's SACL, then each CAAP
effective SACL, accumulating audit events and ORing alarm masks into
the continuous audit mask. This is read-only with respect to
`granted`.

The staged comparison then walks the object's SACL again followed by
the staged SACLs. That second walk is driven by the **staged** granted
total rather than the effective one, so the success and failure
classification of staged audit events reflects the staged access
result — which is what makes the flag sensitive to descriptors whose
staged and effective grants differ.

**Step 14b, forced auditing.** With
`success = (granted & mapped_desired) == mapped_desired or
mapped_desired == 0`, the token's `audit_policy` forces a success or
failure event additively, regardless of what the SACL matched.

**Step 15** returns the accumulated state.

## The wrappers

`AccessCheck` takes the **root node's** granted mask when a tree is
present, then computes `allowed` as `mapped_desired == 0` or every
requested bit granted. The root's mask equals the intersection across
all nodes by construction rather than by computation: upward denial
propagation (§3.8.5) forces every descendant's denial into all of its
ancestors, so the root can never grant what a descendant denies.

`AccessCheckResultList` requires a tree and returns a per-node granted
mask and status, each node judged against `mapped_desired`
independently.

Neither wrapper filters the returned `granted` to the requested mask.
Privilege seeding at step 4 ORs bits in regardless of what was asked
for, so a caller that requested only `READ_CONTROL` while holding
backup can see read bits it never requested. The file enforcement path
does filter its result; the generic query path does not.

## Helpers

```
SidMatchesToken(sid, token, for_allow) -> bool
    if sid == token.user_sid:
        if for_allow and token.user_deny_only:
            return false
        return true
    for group in token.groups:
        if not group.enabled and not group.deny_only:
            continue
        if for_allow and group.deny_only:
            continue
        if sid == group.sid:
            return true
    return false
```

```
MapGenericBits(mask, mapping) -> ACCESS_MASK
    if mask & RESERVED_BITS: reject
    mapped = mask & ~(GENERIC_READ | GENERIC_WRITE
                    | GENERIC_EXECUTE | GENERIC_ALL)
    if mask & GENERIC_READ:    mapped |= mapping.read
    if mask & GENERIC_WRITE:   mapped |= mapping.write
    if mask & GENERIC_EXECUTE: mapped |= mapping.execute
    if mask & GENERIC_ALL:     mapped |= mapping.all
    return mapped
```

All four generic bits are cleared before any is expanded, so a mask
naming several generics maps every one of them.

**Virtual group resolution.** There is no enrichment step producing a
modified token. `S-1-3-4` and `S-1-5-10` are resolved at each lookup
instead, in the DACL walk, the SACL walk and conditional membership
alike. `S-1-5-10` resolves through the ordinary polarity rules against
`self_sid`. `S-1-3-4` resolves by testing whether the owner SID equals
the token's user SID or any group SID — a **presence** test that does
not consult `SE_GROUP_ENABLED`, `SE_GROUP_USE_FOR_DENY_ONLY`, or
`user_deny_only`, and that returns the same answer for allow and deny
polarity.

**`EvaluateSACL`** walks in a fixed order per ACE: SID match with deny
polarity, then object-type scoping against the tree, then the
condition, then the mask overlap against `mapped_desired`. Audit ACEs
need all four; alarm ACEs deliberately skip the overlap test and
contribute their mask on a SID match alone. Inherit-only ACEs are
skipped throughout.

**`synthetic_sd`** builds a CAAP rule's descriptor from the original's
owner and optional group with the rule's DACL substituted, and the
SACL copied with every scoped policy ACE stripped — which is what
prevents recursion. The MIC and PIP labels are preserved, so a rule is
evaluated under the same mandatory constraints as the object. The
control bits and the stripped SACL's revision are recomputed rather
than copied.

## Provenance masks

| Variable | Set at | Meaning |
|---|---|---|
| `security_granted` | Step 4 | `SeSecurityPrivilege` granted `ACCESS_SYSTEM_SECURITY`. |
| `backup_granted` | Step 4 | `SeBackupPrivilege` granted read bits. |
| `restore_granted` | Step 4 | `SeRestorePrivilege` granted write and metadata bits. |
| `take_ownership_granted` | Step 9 | `SeTakeOwnershipPrivilege` granted `WRITE_OWNER`. |
| `relabel_granted` | Step 5 | `SeRelabelPrivilege` added `WRITE_OWNER` to the MIC allowed set. |

Each records which bits that privilege contributed, and step 13
compares each against the requested mask and the final result.
