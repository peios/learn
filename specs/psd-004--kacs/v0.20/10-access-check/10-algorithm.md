---
title: The Algorithm
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
12. **CAAP (Central Access and Auditing Policy).** For each scoped policy, evaluate each applicable rule's DACL using the full per-SD pipeline and intersect. Collect applicable rules' SACLs for the audit walk.
13. **Privilege-use auditing.** Emit audit events for privileges that contributed to the final result.
14. **Audit emission.** Walk the object's SACL and any CAAP effective SACLs for audit and alarm ACEs.
15. **Result computation.** Derive the final granted mask and success/failure verdict.

## EvaluateSecurityDescriptor

Per-SD evaluation (steps 0--11). Called once for the normal evaluation and once per CAAP rule with a synthetic SD.

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

    // Note: SeRestorePrivilege above includes WRITE_OWNER in
    // restore_bits. If restore is active, WRITE_OWNER is decided
    // here. Step 9 (SeTakeOwnershipPrivilege) is a fallback for
    // when restore is not active and the DACL did not grant it.

    // Step 5: Pre-SACL walk.
    resource_attributes = {}
    policy_sids = []
    // mandatory_decided tracks bits decided by MIC and PIP
    // (mandatory mechanisms). Used at step 9 to prevent
    // SeTakeOwnershipPrivilege from overriding mandatory
    // decisions. Populated by EnforceMIC and EnforcePIP.
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
        // Build restricted enriched token: inject virtual groups
        // (S-1-3-4 if owner in restricting SIDs, S-1-5-10 if
        // self_sid in restricting SIDs). Swap in restricted
        // device groups for Device_Member_of evaluation.
        // Restricting SIDs are presence-based; attributes ignored.
        r_enriched = EnrichTokenForRestricted(
            token, sd.owner, self_sid,
            token.restricted_sids,
            token.restricted_device_groups)
        // Fresh tree: same structure, zeroed decided/granted.
        r_tree = null
        if object_tree is not null:
            r_tree = copy_tree_structure(object_tree)
            for each node in r_tree:
                node.decided = 0; node.granted = 0
        EvaluateDACL(sd, r_enriched, mapping, r_tree,
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
        // Tree merge: same intersection per node.
        if object_tree is not null:
            for i in 0..len(object_tree):
                if token.write_restricted:
                    object_tree[i].granted =
                        (object_tree[i].granted & ~write_bits)
                        | (object_tree[i].granted
                           & r_tree[i].granted & write_bits)
                else:
                    object_tree[i].granted =
                        object_tree[i].granted & r_tree[i].granted
                object_tree[i].granted |= privilege_granted

    // Step 11: Confinement pass.
    if token.confinement_sid is not null
       and not token.confinement_exempt:
        c_decided = 0; c_granted = 0
        // Build confinement SID set:
        // - confinement_sid
        // - confinement_capabilities (presence-based; attributes ignored)
        // Inject virtual groups:
        // - S-1-3-4 if owner SID is in the confinement SID set
        // - S-1-5-10 if self_sid is in the confinement SID set
        // Fresh tree: same structure, zeroed decided/granted.
        c_tree = null
        if object_tree is not null:
            c_tree = copy_tree_structure(object_tree)
            for each node in c_tree:
                node.decided = 0; node.granted = 0
        EvaluateDACL(sd, token, mapping, c_tree,
                     SidInConfinementSids, desired,
                     max_allowed_mode, resource_attributes,
                     local_claims, skip_owner_implicit=true,
                     &c_decided, &c_granted)
        // Absolute intersection. No privilege bypass.
        granted = granted & c_granted
        // Tree merge: absolute intersection per node.
        if object_tree is not null:
            for i in 0..len(object_tree):
                object_tree[i].granted =
                    object_tree[i].granted & c_tree[i].granted

    return (decided, granted, privilege_granted,
            max_allowed_mode, desired, resource_attributes,
            policy_sids)
```

## AccessCheckCore

Orchestrator. Calls EvaluateSecurityDescriptor, then evaluates CAAPs, emits privilege-use audits, and walks the SACL (plus CAAP SACLs) for audit ACEs.

```
AccessCheckCore(
    sd, token, pip_type, pip_trust, desired, mapping,
    object_tree, self_sid, local_claims,
    object_audit_context, privilege_intent
) -> (decided, granted, privilege_granted,
      max_allowed_mode, mapped_desired,
      continuous_audit_mask, staging_mismatch) | error

    // Steps 0-11: per-SD evaluation.
    (decided, granted, privilege_granted,
     max_allowed_mode, mapped_desired,
     resource_attributes, policy_sids
    ) = EvaluateSecurityDescriptor(
        sd, token, pip_type, pip_trust, desired, mapping,
        object_tree, self_sid, local_claims, privilege_intent)

    // Step 12: CAAP (Central Access and Auditing Policy).
    caap_sacls = []          // Effective SACLs from applicable rules.
    staged_caap_sacls = []   // Staged SACLs (or effective as fallback).
    staged_dacl_total = granted  // Staged DACL running total.
    staged_tree_total = null
    if object_tree is not null:
        staged_tree_total = []
        for each node in object_tree:
            staged_tree_total.append(node.granted)
    staging_mismatch = false
    if len(policy_sids) > 0:
        for caap_sid in policy_sids:
            policy = LookupCAAP(caap_sid)
            if policy is null:
                policy = RECOVERY_POLICY
            for rule in policy.rules:
                if rule.applies_to is not null:
                    cond_result = EvaluateConditionalExpression(
                                     rule.applies_to, token,
                                     resource_attributes,
                                     local_claims, for_allow=false)
                    if cond_result != TRUE:
                        continue
                // DACL component: build synthetic SD, evaluate,
                // intersect with running total.
                rule_sd = synthetic_sd(sd, rule.effective_dacl)
                rule_tree = copy_tree_structure(object_tree)
                rule_result = EvaluateSecurityDescriptor(
                    rule_sd, token, pip_type, pip_trust,
                    desired, mapping, rule_tree, self_sid,
                    local_claims, 0)
                if rule_result is error:
                    // DACL error: deny all except privileges.
                    granted &= privilege_granted
                    if object_tree is not null:
                        for i in 0..len(object_tree):
                            object_tree[i].granted &= privilege_granted
                else:
                    granted &= rule_result.granted
                    if object_tree is not null:
                        for i in 0..len(object_tree):
                            object_tree[i].granted &=
                                rule_tree[i].granted
                // SACL component: collect for audit walk.
                // SACL errors are logged and the rule's audit
                // contribution is skipped (not fail-closed).
                if rule.effective_sacl is not null:
                    caap_sacls.append(rule.effective_sacl)

                // Staged DACL evaluation (parallel, no access effect).
                if rule.staged_dacl is not null:
                    stg_sd = synthetic_sd(sd, rule.staged_dacl)
                    stg_tree = copy_tree_structure(object_tree)
                    stg_result = EvaluateSecurityDescriptor(
                        stg_sd, token, pip_type, pip_trust,
                        desired, mapping, stg_tree, self_sid,
                        local_claims, 0)
                    stg_granted = stg_result.granted
                        if stg_result is not error else 0
                else:
                    stg_granted = rule_result.granted
                        if rule_result is not error
                        else privilege_granted
                staged_dacl_total &= stg_granted
                if object_tree is not null:
                    for i in 0..len(object_tree):
                        if rule.staged_dacl is not null:
                            stg_node_granted =
                                stg_tree[i].granted
                                if stg_result is not error
                                else privilege_granted
                        else:
                            stg_node_granted =
                                rule_tree[i].granted
                                if rule_result is not error
                                else privilege_granted
                        staged_tree_total[i] &=
                            stg_node_granted

                // Staged SACL: collect for staged audit walk.
                if rule.staged_sacl is not null:
                    staged_caap_sacls.append(rule.staged_sacl)
                else if rule.effective_sacl is not null:
                    // No staged SACL: contribute effective to both.
                    staged_caap_sacls.append(rule.effective_sacl)

        // After all policies: compare staged vs effective.
        if staged_dacl_total != granted:
            staging_mismatch = true
            // Log: effective_granted, staged_dacl_total, policy_sids.
        if object_tree is not null:
            for i in 0..len(object_tree):
                if staged_tree_total[i] != object_tree[i].granted:
                    staging_mismatch = true
                    break
            // In result-list mode, any per-node staged/effective
            // grant delta sets staging_mismatch.

    // Step 13: Privilege-use auditing.
    // Only for explicit requests, not MAXIMUM_ALLOWED probing.
    // For each privilege tracked by a provenance mask
    // (security_granted, backup_granted, restore_granted,
    // take_ownership_granted, relabel_granted):
    //
    // success_bits = provenance_var & mapped_desired & granted
    // failure_bits = provenance_var & mapped_desired & ~granted
    //
    // In scalar AccessCheck, compare against scalar final granted.
    // In AccessCheckResultList, compare against the final per-node
    // granted list: a privilege-use success occurs if contributed
    // requested bits survive on any node; a privilege-use failure
    // occurs only if contributed requested bits survive on no node.
    //
    // If success_bits != 0, the privilege was actually necessary
    // for the final result:
    // - call mark_used on the token
    // - emit a PrivilegeUseEvent with success=true if the token's
    //   audit_policy has PRIVILEGE_USE_SUCCESS (0x04)
    //
    // Else if failure_bits != 0, the privilege was exercised but
    // did not survive to the final granted result:
    // - do NOT call mark_used on the token
    // - emit a PrivilegeUseEvent with success=false if the token's
    //   audit_policy has PRIVILEGE_USE_FAILURE (0x08)
    //
    // If both are zero, the privilege did not contribute to the
    // requested access and no privilege-use event is emitted.
    //
    // The object_audit_context is included in emitted events so
    // the audit trail identifies which object the privilege was
    // exercised on.

    // Step 14: Audit emission.
    audit_events = []
    continuous_audit_mask = 0
    // Walk the object's own SACL.
    if sd.sacl is not null:
        EvaluateSACL(sd.sacl, token, sd.owner, self_sid,
                     object_tree, mapped_desired, granted, mapping,
                     resource_attributes, local_claims,
                     &audit_events, &continuous_audit_mask)
    // Walk each CAAP effective SACL collected in step 12.
    // Same evaluation rules as the object's own SACL.
    for caap_sacl in caap_sacls:
        EvaluateSACL(caap_sacl, token, sd.owner, self_sid,
                     object_tree, mapped_desired, granted, mapping,
                     resource_attributes, local_claims,
                     &audit_events, &continuous_audit_mask)
    // continuous_audit_mask is the OR of all matching alarm
    // ACE masks across the object SACL and all CAAP SACLs.
    // audit_events contains all matching audit ACEs.
    // Read-only — does not modify granted.

    // Staged SACL comparison: walk staged SACLs in parallel,
    // compare audit event sets. Does not affect real auditing.
    // Any audit delta sets staging_mismatch in both scalar and
    // result-list modes.
    if len(staged_caap_sacls) > 0:
        staged_audit_events = []
        staged_continuous = 0
        if sd.sacl is not null:
            EvaluateSACL(sd.sacl, token, sd.owner, self_sid,
                         object_tree, mapped_desired, granted, mapping,
                         resource_attributes, local_claims,
                         &staged_audit_events, &staged_continuous)
        for stg_sacl in staged_caap_sacls:
            EvaluateSACL(stg_sacl, token, sd.owner, self_sid,
                         object_tree, mapped_desired, granted, mapping,
                         resource_attributes, local_claims,
                         &staged_audit_events, &staged_continuous)
        if staged_audit_events != audit_events
           or staged_continuous != continuous_audit_mask:
            staging_mismatch = true
            // Log: audit delta between effective and staged SACLs.

    // Step 14b: Token audit_policy forced auditing.
    // If the token's audit_policy has OBJECT_ACCESS_SUCCESS (0x01)
    // and the access succeeded, emit an audit event regardless
    // of whether the SACL matched. Similarly for
    // OBJECT_ACCESS_FAILURE (0x02) on failure. These are additive
    // — they force audit events that the SACL alone would not
    // have generated.
    success = (granted & mapped_desired) == mapped_desired
              or mapped_desired == 0
    if success and (token.audit_policy & 0x01):
        audit_events.append(AuditEvent(
            policy_forced=true, mapped_desired, granted, true))
    if not success and (token.audit_policy & 0x02):
        audit_events.append(AuditEvent(
            policy_forced=true, mapped_desired, granted, false))

    // Step 15: Result computation.
    return (decided, granted, privilege_granted,
            max_allowed_mode, mapped_desired,
            continuous_audit_mask, staging_mismatch)
```

## AccessCheck wrapper

```
AccessCheck(...) -> (granted, allowed,
                     continuous_audit_mask,
                     staging_mismatch) | error

    (decided, granted, privilege_granted,
     max_allowed_mode, mapped_desired,
     continuous_audit_mask,
     staging_mismatch) = AccessCheckCore(...)

    // When a tree is present, root.granted reflects the
    // whole object (ancestor propagation ensures this).
    if object_tree is not null:
        granted = object_tree[0].granted

    // All comparisons use mapped_desired.
    if mapped_desired == 0:
        allowed = true
    else:
        allowed = (granted & mapped_desired) == mapped_desired

    return (granted, allowed, continuous_audit_mask,
            staging_mismatch)
```

## AccessCheckResultList wrapper

```
AccessCheckResultList(...) -> (granted_list, status_list,
                               continuous_audit_mask,
                               staging_mismatch) | error

    // Requires object_tree.
    (decided, granted, privilege_granted,
     max_allowed_mode, mapped_desired,
     continuous_audit_mask,
     staging_mismatch) = AccessCheckCore(...)

    for each node in object_tree:
        if mapped_desired == 0:
            node_status = OK
        else if (node.granted & mapped_desired) == mapped_desired:
            node_status = OK
        else:
            node_status = ACCESS_DENIED
        granted_list.append(node.granted or 0)
        status_list.append(node_status)

    return (granted_list, status_list, continuous_audit_mask,
            staging_mismatch)
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

```
EvaluateSACL(sacl, token, owner, self_sid,
             object_tree, mapped_desired, granted, mapping,
             resource_attributes, local_claims,
             &audit_events, &continuous_audit_mask)

    enriched = EnrichToken(token, owner, self_sid)

    for ace in sacl.aces:
        if ace.flags & INHERIT_ONLY_ACE:
            continue
        ace_mask = MapGenericBits(ace.mask, mapping)

        if ace.type == SYSTEM_AUDIT_ACE
           or ace.type == SYSTEM_AUDIT_OBJECT_ACE:
            if not enriched_sid_matches(ace.sid, enriched,
                                        for_allow=false):
                continue
            // Object ACE GUID scoping: if the ACE has an
            // ObjectType GUID and an object_tree is present,
            // the ACE only fires if the GUID matches a node.
            if ace.has_object_type() and object_tree is not null:
                if FindNode(object_tree, ace.object_type) is null:
                    continue
            if (ace_mask & mapped_desired) == 0:
                continue
            success = (granted & mapped_desired) == mapped_desired
                      or mapped_desired == 0
            if success and (ace.flags & SUCCESSFUL_ACCESS_ACE_FLAG):
                audit_events.append(AuditEvent(
                    ace, mapped_desired, granted, true))
            if not success and (ace.flags & FAILED_ACCESS_ACE_FLAG):
                audit_events.append(AuditEvent(
                    ace, mapped_desired, granted, false))

        if ace.type == SYSTEM_AUDIT_CALLBACK_ACE
           or ace.type == SYSTEM_AUDIT_CALLBACK_OBJECT_ACE:
            if not enriched_sid_matches(ace.sid, enriched,
                                        for_allow=false):
                continue
            // Object ACE GUID scoping (same as above).
            if ace.has_object_type() and object_tree is not null:
                if FindNode(object_tree, ace.object_type) is null:
                    continue
            // Condition must be TRUE or UNKNOWN to fire.
            cond = EvaluateConditionalExpression(
                ace.condition, enriched, resource_attributes,
                local_claims, for_allow=false)
            if cond == FALSE:
                continue
            if (ace_mask & mapped_desired) == 0:
                continue
            success = (granted & mapped_desired) == mapped_desired
                      or mapped_desired == 0
            if success and (ace.flags & SUCCESSFUL_ACCESS_ACE_FLAG):
                audit_events.append(AuditEvent(
                    ace, mapped_desired, granted, true))
            if not success and (ace.flags & FAILED_ACCESS_ACE_FLAG):
                audit_events.append(AuditEvent(
                    ace, mapped_desired, granted, false))

        if ace.type == SYSTEM_ALARM_ACE
           or ace.type == SYSTEM_ALARM_OBJECT_ACE:
            if enriched_sid_matches(ace.sid, enriched,
                                    for_allow=false):
                if ace.has_object_type() and object_tree is not null:
                    if FindNode(object_tree, ace.object_type) is null:
                        continue
                continuous_audit_mask |= ace_mask

        if ace.type == SYSTEM_ALARM_CALLBACK_ACE
           or ace.type == SYSTEM_ALARM_CALLBACK_OBJECT_ACE:
            if enriched_sid_matches(ace.sid, enriched,
                                    for_allow=false):
                if ace.has_object_type() and object_tree is not null:
                    if FindNode(object_tree, ace.object_type) is null:
                        continue
                cond = EvaluateConditionalExpression(
                    ace.condition, enriched, resource_attributes,
                    local_claims, for_allow=false)
                if cond == FALSE:
                    continue
                continuous_audit_mask |= ace_mask
```

## Undefined helper functions

The following functions are called in the pseudocode above but defined in other spec sections:

| Function | Defined in | Purpose |
|----------|-----------|---------|
| `EvaluateDACL` | DACL Walk + Object ACEs sections | Owner implicit rights, DACL walk (first-writer-wins), SID matching, object ACE propagation |
| `EvaluateConditionalExpression` | Conditional ACEs + Bytecode Reference sections | Stack-based bytecode evaluator for callback ACE conditions |
| `PreSACLWalk` | Integrity + PIP sections | Extracts mandatory label, trust label, resource attributes, scoped policy SIDs from SACL. Runs MIC (EnforceMIC) and PIP (EnforcePIP). Outputs: modified decided/granted/privilege_granted, mandatory_decided, resource_attributes, policy_sids |
| `EnrichTokenForRestricted` | Restricted Tokens section | Builds enriched token view for restricted pass: inject S-1-3-4 if owner in restricting SIDs, S-1-5-10 if self_sid in restricting SIDs, swap device groups for restricted device groups |
| `LookupCAAP` | Central Access and Auditing Policy section | Looks up policy by SID in kernel cache. Returns null if not found. |
| `RECOVERY_POLICY` | Central Access and Auditing Policy section | Hardcoded fallback: ALLOW GENERIC_ALL to Administrators, SYSTEM, OWNER_RIGHTS |
| `synthetic_sd` | (inline concept) | Creates an SD using the original SD's owner/group but substituting the rule's DACL. The SACL is copied from the original SD with all SYSTEM_SCOPED_POLICY_ID_ACEs stripped (prevents CAAP recursion). MIC and PIP label ACEs are preserved. |
| `copy_tree_structure` | (inline concept) | Deep-copies object tree node structure (levels, GUIDs, parent/child) with decided=0, granted=0 on each node |
| `SidInRestrictingSids` | Restricted Tokens section | SID matcher callback: returns true if SID is in the token's restricted_sids list (pure SID equality, ignores attributes) |
| `SidInConfinementSids` | Confinement section | SID matcher callback: returns true if SID is in the confinement SID set (confinement_sid + confinement_capabilities). Capability entries are presence-based; attributes are ignored. |
| `enriched_sid_matches` | DACL Walk section | Like SidMatchesToken but also checks virtual groups (S-1-3-4 for owner, S-1-5-10 for PRINCIPAL_SELF). Used for both DACL and SACL SID matching. |

### Privilege provenance tracking

Step 13 references per-privilege provenance masks. These are tracked throughout the pipeline as additional scalar variables:

| Variable | Set when | Used by |
|----------|----------|---------|
| `security_granted` | Step 4: SeSecurityPrivilege grants ACCESS_SYSTEM_SECURITY | Step 13: success if contributed requested bits survive to final granted; failure if they are later stripped |
| `backup_granted` | Step 4: SeBackupPrivilege grants read bits | Step 13 |
| `restore_granted` | Step 4: SeRestorePrivilege grants write+metadata bits | Step 13 |
| `take_ownership_granted` | Step 9: SeTakeOwnershipPrivilege grants WRITE_OWNER | Step 13 |
| `relabel_granted` | Step 5 (MIC): SeRelabelPrivilege adds WRITE_OWNER to MIC allowed set | Step 13 |

Each variable records which bits that privilege contributed. At step 13, for each privilege, compare the provenance mask against the mapped requested mask and the final result. In scalar `AccessCheck`, the comparison uses scalar final `granted`. In `AccessCheckResultList`, the comparison uses the final per-node granted list: if contributed requested bits survive on any node, the privilege was "actually necessary" — call `mark_used` and emit a successful PrivilegeUseEvent if the token's `audit_policy` has `PRIVILEGE_USE_SUCCESS` (0x04). If contributed requested bits were exercised but survive on no node, emit a failure PrivilegeUseEvent if the token's `audit_policy` has `PRIVILEGE_USE_FAILURE` (0x08), but do not call `mark_used`.
