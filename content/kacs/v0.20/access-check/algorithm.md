---
title: The Algorithm
order: 10
---

This section specifies the complete AccessCheck evaluation algorithm. The feature sections describe what each feature does. This section describes how they compose.

## Pipeline overview

The complete evaluation runs in this order:

0. **Impersonation level gate.** If the token is an impersonation token at Identification level, deny immediately. Anonymous tokens proceed through the full pipeline.
1. **Input validation.** Reject null SDs, SDs without owner or group, and malformed object type lists.
2. **Generic mapping.** Map generic bits in the desired mask to object-specific bits. Strip MAXIMUM_ALLOWED.
3. **Effective privileges.** Clear backup/restore bits when the corresponding intent flag is absent.
4. **Privilege grants.** Resolve ACCESS_SYSTEM_SECURITY, backup, and restore. Seed `decided`, `granted`, and `privilege_granted`.
5. **Pre-SACL walk.** Extract the mandatory integrity label, PIP trust label, resource attributes, and scoped policy IDs from the SACL. Enforce MIC and PIP.
6. **Virtual group injection.** Inject S-1-3-4 and S-1-5-10 as virtual groups if the caller is the owner or matches the object's principal.
7. **Tree initialization.** Copy scalar `decided`/`granted` to each tree node.
8. **Normal DACL evaluation.** Owner implicit rights, then the DACL walk with token-based SID matching.
9. **Post-DACL privilege override.** SeTakeOwnershipPrivilege grants WRITE_OWNER if the DACL did not and mandatory policy (MIC/PIP) did not block it.
10. **Restricted token pass.** If the token has restricting SIDs, evaluate the DACL again with the restricted SID list and intersect. Privilege-granted bits are restored after intersection.
11. **Confinement pass.** If the token is confined, evaluate the DACL with confinement SIDs and intersect. No privilege bypass.
12. **Central Access Policy.** For each scoped policy, evaluate each applicable rule's DACL using the full per-SD pipeline and intersect.
13. **Privilege-use auditing.** Emit audit events for privileges that contributed to the final result.
14. **Audit emission.** Walk the SACL for audit and alarm ACEs.
15. **Result computation.** Derive the final granted mask and success/failure verdict.

## EvaluateSecurityDescriptor

Per-SD evaluation (steps 0--11). Called once for the normal evaluation and once per CAP rule with a synthetic SD.

```
EvaluateSecurityDescriptor(
    sd, token, pip_type, pip_trust, desired, mapping,
    object_tree, self_sid, local_claims, privilege_intent
) -> (decided, granted, privilege_granted, provenance,
      max_allowed_mode, mapped_desired, resource_attributes,
      policy_sids) | error

    // Step 0: Impersonation level gate.
    if token.token_type == Impersonation
       and token.impersonation_level == Identification:
        return ERROR_ACCESS_DENIED

    // Step 1: Input validation.
    if sd is null:
        return ERROR_INVALID_PARAMETER
    if sd.owner is null or sd.group is null:
        return ERROR_INVALID_SECURITY_DESCR
    if object_tree is not null:
        validate: non-empty, first node at level 0,
        exactly one level-0 node, no level gaps,
        no duplicate GUIDs

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

    // ACCESS_SYSTEM_SECURITY: always decided by privilege.
    decided |= ACCESS_SYSTEM_SECURITY
    if (effective_privileges & SeSecurityPrivilege):
        granted |= ACCESS_SYSTEM_SECURITY
        privilege_granted |= ACCESS_SYSTEM_SECURITY

    // Backup: all read-mapped bits.
    if (effective_privileges & SeBackupPrivilege):
        backup_bits = MapGenericBits(GENERIC_READ, mapping)
        decided |= backup_bits
        granted |= backup_bits
        privilege_granted |= backup_bits

    // Restore: all write-mapped bits + metadata rights.
    if (effective_privileges & SeRestorePrivilege):
        restore_bits = MapGenericBits(GENERIC_WRITE, mapping)
                       | WRITE_DAC | WRITE_OWNER | DELETE
                       | ACCESS_SYSTEM_SECURITY
        decided |= restore_bits
        granted |= restore_bits
        privilege_granted |= restore_bits

    // WRITE_OWNER is NOT decided here — deferred to step 9.

    // Step 5: Pre-SACL walk.
    resource_attributes = {}
    policy_sids = []
    mandatory_decided = 0
    PreSACLWalk(sd, token, pip_type, pip_trust, mapping,
                &decided, &granted, &privilege_granted,
                &mandatory_decided, &resource_attributes,
                &policy_sids)

    // Step 6: Virtual group injection.
    token = EnrichToken(token, sd.owner, self_sid)

    // Step 7: Tree initialization.
    if object_tree is not null:
        for each node in object_tree:
            node.decided = decided
            node.granted = granted

    // Step 8: Normal DACL evaluation.
    EvaluateDACL(sd, token, mapping, object_tree,
                 SidMatchesToken, desired, max_allowed_mode,
                 resource_attributes, local_claims,
                 skip_owner_implicit=false,
                 &decided, &granted)

    // Step 9: Post-DACL WRITE_OWNER override.
    // Deny-proof but respects mandatory decisions (MIC/PIP).
    if (desired & WRITE_OWNER) != 0 or max_allowed_mode:
        if (effective_privileges & SeTakeOwnershipPrivilege):
            if not (mandatory_decided & WRITE_OWNER)
               and not (granted & WRITE_OWNER):
                decided |= WRITE_OWNER
                granted |= WRITE_OWNER
                privilege_granted |= WRITE_OWNER
                if object_tree is not null:
                    for each node:
                        if not (node.granted & WRITE_OWNER):
                            node.decided |= WRITE_OWNER
                            node.granted |= WRITE_OWNER

    // Step 10: Restricted token pass.
    if token.restricted_sids is not empty:
        r_decided = 0; r_granted = 0
        // Swap in restricted device groups if present.
        // Build restricted SID set with virtual groups.
        // Fresh tree for restricted pass.
        EvaluateDACL(sd, r_token, mapping, r_tree,
                     SidInRestrictingSids, desired,
                     max_allowed_mode, resource_attributes,
                     local_claims, skip_owner_implicit=false,
                     &r_decided, &r_granted)
        // Scalar merge: intersection.
        if token.write_restricted:
            write_bits = MapGenericBits(GENERIC_WRITE, mapping)
            granted = (granted & ~write_bits)
                    | (granted & r_granted & write_bits)
        else:
            granted = granted & r_granted
        // Privilege-granted bits bypass the restricted pass.
        granted |= privilege_granted
        // Tree merge follows same pattern.

    // Step 11: Confinement pass.
    if token.confinement_sid is not null
       and not token.confinement_exempt:
        c_decided = 0; c_granted = 0
        // Build confinement SID set with virtual groups.
        // Fresh tree for confinement pass.
        EvaluateDACL(sd, token, mapping, c_tree,
                     SidInConfinementSids, desired,
                     max_allowed_mode, resource_attributes,
                     local_claims, skip_owner_implicit=true,
                     &c_decided, &c_granted)
        // Absolute intersection. No privilege bypass.
        granted = granted & c_granted
        // Tree merge follows same pattern.

    return (decided, granted, privilege_granted, provenance,
            max_allowed_mode, desired, resource_attributes,
            policy_sids)
```

## AccessCheckCore

Orchestrator. Calls EvaluateSecurityDescriptor, then evaluates Central Access Policies, emits privilege-use audits, and walks the SACL for audit ACEs.

```
AccessCheckCore(
    sd, token, pip_type, pip_trust, desired, mapping,
    object_tree, self_sid, local_claims,
    object_audit_context, privilege_intent
) -> (decided, granted, privilege_granted,
      max_allowed_mode, mapped_desired,
      continuous_audit_mask) | error

    // Steps 0-11: per-SD evaluation.
    result = EvaluateSecurityDescriptor(
        sd, token, pip_type, pip_trust, desired, mapping,
        object_tree, self_sid, local_claims, privilege_intent)

    // Step 12: Central Access Policy.
    if len(policy_sids) > 0:
        for cap_sid in policy_sids:
            policy = LookupCentralAccessPolicy(cap_sid)
            if policy is null:
                policy = RECOVERY_POLICY
            for rule in policy.rules:
                if rule.applies_to is not null:
                    result = EvaluateConditionalExpression(
                                 rule.applies_to, enriched_token,
                                 resource_attributes, local_claims,
                                 for_allow=false)
                    if result != TRUE:
                        continue
                // Evaluate rule's effective DACL using full
                // pipeline (no backup/restore intent).
                eff_result = EvaluateSecurityDescriptor(
                    synthetic_sd(sd, rule.effective_dacl),
                    token, pip_type, pip_trust, desired,
                    mapping, eff_tree, self_sid,
                    local_claims, 0)
                // Intersect with running total.
                granted &= eff_granted
                // Staged evaluation (if present) runs in
                // parallel for logging, does not affect access.

    // Step 13: Privilege-use auditing.
    // Emitted ONCE, not inside EvaluateSecurityDescriptor.
    // Only for explicit requests, not MAXIMUM_ALLOWED probing.
    // Uses per-privilege provenance masks to attribute bits
    // accurately.

    // Step 14: Audit emission.
    // Walk SACL for audit and alarm ACEs. Build continuous
    // audit mask. Read-only — does not modify granted.

    // Step 15: Result computation.
    return (decided, granted, privilege_granted,
            max_allowed_mode, mapped_desired,
            continuous_audit_mask)
```

## AccessCheck wrapper

```
AccessCheck(...) -> (granted, allowed,
                     continuous_audit_mask) | error

    result = AccessCheckCore(...)

    // When a tree is present, root.granted reflects the
    // whole object (ancestor propagation ensures this).
    if object_tree is not null:
        granted = object_tree[0].granted

    // All comparisons use mapped_desired.
    if mapped_desired == 0:
        allowed = true
    else:
        allowed = (granted & mapped_desired) == mapped_desired

    return (granted, allowed, continuous_audit_mask)
```

## AccessCheckResultList wrapper

```
AccessCheckResultList(...) -> (granted_list, status_list,
                               continuous_audit_mask) | error

    // Requires object_tree.
    result = AccessCheckCore(...)

    for each node in object_tree:
        if mapped_desired == 0:
            node_status = OK
        else if (node.granted & mapped_desired) == mapped_desired:
            node_status = OK
        else:
            node_status = ACCESS_DENIED
        granted_list.append(node.granted or 0)
        status_list.append(node_status)

    return (granted_list, status_list, continuous_audit_mask)
```

## Key helper functions

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
EnrichToken(token, owner_sid, self_sid) -> Token
    // Idempotent. Returns a view — original not modified.
    if SidMatchesToken(owner_sid, token, for_allow=true):
        add S-1-3-4 as virtual group
    if self_sid is not null:
        if SidMatchesToken(self_sid, token, for_allow=true):
            add S-1-5-10 as virtual group
        else if SidMatchesToken(self_sid, token, for_allow=false):
            add S-1-5-10 as virtual group (deny-only)
    return token
```

```
MapGenericBits(mask, mapping) -> ACCESS_MASK
    if mask & GENERIC_READ:
        mask = (mask & ~GENERIC_READ) | mapping.read
    if mask & GENERIC_WRITE:
        mask = (mask & ~GENERIC_WRITE) | mapping.write
    if mask & GENERIC_EXECUTE:
        mask = (mask & ~GENERIC_EXECUTE) | mapping.execute
    if mask & GENERIC_ALL:
        mask = (mask & ~GENERIC_ALL) | mapping.all
    return mask
```

> [!INFORMATIVE]
> The full conditional expression evaluator (bytecode parsing, operator semantics, type coercion, claim resolution) and the complete EvaluateDACL function with object ACE propagation are specified in the implementation. The pseudocode here captures the pipeline structure and layer interactions. The complete bytecode operator table is defined in MS-DTYP section 2.4.4.17.4.
