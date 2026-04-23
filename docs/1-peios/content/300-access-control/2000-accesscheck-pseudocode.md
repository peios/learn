---
title: AccessCheck Pseudocode
type: concept
description: The complete AccessCheck evaluation algorithm — every function, every step, no omissions.
---

The complete pseudocode for the AccessCheck evaluation pipeline. This is the exact process the kernel follows for every access decision on Peios.

> [!NOTE]
> This page is a reference for readers who want to understand the precise evaluation logic. For a conceptual overview, see [How AccessCheck Evaluates Every Access Decision](~peios/access-control/how-accesscheck-works).

## AccessCheck

Single-result access check. If tree present, all nodes must pass.

```
AccessCheck(
    SecurityDescriptor  sd,
    Token               token,
    ACCESS_MASK         desired,
    GenericMapping      mapping,
    OBJECT_TYPE_LIST[]  object_tree,
    SID                 self_sid,
    CLAIM_ATTRIBUTES[]  local_claims,
    AUDIT_CONTEXT       object_audit_context,
    uint32              privilege_intent,
) -> (ACCESS_MASK granted, bool allowed,
      ACCESS_MASK continuous_audit_mask,
      [(GUID, ACCESS_MASK)] continuous_audit_nodes) | error

result = AccessCheckCore(sd, token, desired, mapping,
                         object_tree, self_sid, local_claims,
                         object_audit_context, privilege_intent)
if result is error:
    return result

(decided, granted, privilege_granted, max_allowed_mode,
 mapped_desired, continuous_audit_mask, continuous_audit_nodes) = result

if object_tree is not null:
    granted = object_tree[0].granted

if mapped_desired == 0:
    allowed = true
else:
    allowed = (granted & mapped_desired) == mapped_desired
if not max_allowed_mode:
    if allowed:
        granted = mapped_desired
    else:
        granted = 0
return (granted, allowed, continuous_audit_mask, continuous_audit_nodes)
```

## AccessCheckResultList

Per-node result access check. Requires tree.

```
AccessCheckResultList(
    SecurityDescriptor  sd,
    Token               token,
    ACCESS_MASK         desired,
    GenericMapping      mapping,
    OBJECT_TYPE_LIST[]  object_tree,
    SID                 self_sid,
    CLAIM_ATTRIBUTES[]  local_claims,
    AUDIT_CONTEXT       object_audit_context,
    uint32              privilege_intent,
) -> (ACCESS_MASK[] granted_list, STATUS[] status_list,
      ACCESS_MASK continuous_audit_mask,
      [(GUID, ACCESS_MASK)] continuous_audit_nodes) | error

if object_tree is null:
    return ERROR_INVALID_PARAMETER

result = AccessCheckCore(sd, token, desired, mapping,
                         object_tree, self_sid, local_claims,
                         object_audit_context, privilege_intent)
if result is error:
    return result

(decided, granted, privilege_granted, max_allowed_mode,
 mapped_desired, continuous_audit_mask, continuous_audit_nodes) = result

granted_list = []
status_list = []

for each node in object_tree:
    if mapped_desired == 0:
        node_status = OK
    else if (node.granted & mapped_desired) == mapped_desired:
        node_status = OK
    else:
        node_status = ACCESS_DENIED

    if max_allowed_mode:
        node_granted = node.granted
    else:
        node_granted = mapped_desired if node_status == OK else 0

    granted_list.append(node_granted)
    status_list.append(node_status)

return (granted_list, status_list, continuous_audit_mask,
        continuous_audit_nodes)
```

## AccessCheckCore

Orchestrator. Calls EvaluateSecurityDescriptor, then Central Access Policy, then audit.

```
AccessCheckCore(
    SecurityDescriptor  sd,
    Token               token,
    ACCESS_MASK         desired,
    GenericMapping      mapping,
    OBJECT_TYPE_LIST[]  object_tree,
    SID                 self_sid,
    CLAIM_ATTRIBUTES[]  local_claims,
    AUDIT_CONTEXT       object_audit_context,
    uint32              privilege_intent,
) -> (decided, granted, privilege_granted, max_allowed_mode, mapped_desired,
      continuous_audit_mask, continuous_audit_nodes) | error

// Steps 1-8a: per-SD evaluation.
result = EvaluateSecurityDescriptor(sd, token, desired, mapping,
                                    object_tree, self_sid, local_claims,
                                    privilege_intent)
if result is error:
    return result

(decided, granted, privilege_granted, max_allowed_mode, mapped_desired,
 resource_attributes, policy_sids) = result

// Step 9: Central Access Policy evaluation.
enriched_token = EnrichToken(token, sd.owner, self_sid)

if len(policy_sids) > 0:
    cap_effective = granted
    cap_staged = granted

    if object_tree is not null:
        cap_eff_tree = deep_copy(object_tree)
        cap_stg_tree = deep_copy(object_tree)

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

            // --- Effective evaluation ---
            eff_sd = copy(sd)
            eff_sd.dacl = rule.effective_dacl
            eff_sd.control |= SE_DACL_PRESENT

            if object_tree is not null:
                eff_tree = deep_copy_structure(object_tree)
            else:
                eff_tree = null

            eff_result = EvaluateSecurityDescriptor(
                             eff_sd, token, desired, mapping,
                             eff_tree, self_sid, local_claims, 0)
            if eff_result is error:
                cap_effective &= privilege_granted
                cap_staged &= privilege_granted
                if object_tree is not null:
                    for i = 0 to len(object_tree) - 1:
                        cap_eff_tree[i].granted &= privilege_granted
                        cap_stg_tree[i].granted &= privilege_granted
                continue
            (_, eff_granted, _, _, _, _, _) = eff_result

            cap_effective &= eff_granted
            if object_tree is not null:
                for i = 0 to len(object_tree) - 1:
                    cap_eff_tree[i].granted &= eff_tree[i].granted

            // --- Staged evaluation ---
            if rule.staged_dacl is not null:
                stg_sd = copy(sd)
                stg_sd.dacl = rule.staged_dacl
                stg_sd.control |= SE_DACL_PRESENT

                if object_tree is not null:
                    stg_tree = deep_copy_structure(object_tree)
                else:
                    stg_tree = null

                stg_result = EvaluateSecurityDescriptor(
                                 stg_sd, token, desired, mapping,
                                 stg_tree, self_sid, local_claims, 0)
                if stg_result is error:
                    stg_granted = eff_granted
                    cap_staged &= stg_granted
                    if object_tree is not null:
                        for i = 0 to len(object_tree) - 1:
                            cap_stg_tree[i].granted &= eff_tree[i].granted
                else:
                    (_, stg_granted, _, _, _, _, _) = stg_result
                    cap_staged &= stg_granted
                    if object_tree is not null:
                        for i = 0 to len(object_tree) - 1:
                            cap_stg_tree[i].granted &= stg_tree[i].granted
            else:
                cap_staged &= eff_granted
                if object_tree is not null:
                    for i = 0 to len(object_tree) - 1:
                        cap_stg_tree[i].granted &= eff_tree[i].granted

    if cap_effective != cap_staged:
        LogStagingDifference(cap_effective, cap_staged)

    granted = cap_effective

    if object_tree is not null:
        for i = 0 to len(object_tree) - 1:
            object_tree[i].granted = cap_eff_tree[i].granted

// Step 9b: Privilege-use auditing.
if not max_allowed_mode:
    if (mapped_desired & ACCESS_SYSTEM_SECURITY) != 0
       and (granted & ACCESS_SYSTEM_SECURITY) != 0:
        token.privileges_used |= SeSecurityPrivilege
        EmitPrivilegeUseAudit(object_audit_context, token,
                              SeSecurityPrivilege)
    if (mapped_desired & WRITE_OWNER) != 0
       and (privilege_granted & WRITE_OWNER) != 0
       and (granted & WRITE_OWNER) != 0:
        token.privileges_used |= SeTakeOwnershipPrivilege
        EmitPrivilegeUseAudit(object_audit_context, token,
                              SeTakeOwnershipPrivilege)
    if (privilege_intent & BACKUP_INTENT)
       and (privilege_granted & MapGenericBits(GENERIC_READ, mapping)) != 0
       and (granted & privilege_granted) != 0:
        token.privileges_used |= SeBackupPrivilege
        EmitPrivilegeUseAudit(object_audit_context, token,
                              SeBackupPrivilege)
    if (privilege_intent & RESTORE_INTENT)
       and (privilege_granted & MapGenericBits(GENERIC_WRITE, mapping)) != 0
       and (granted & privilege_granted) != 0:
        token.privileges_used |= SeRestorePrivilege
        EmitPrivilegeUseAudit(object_audit_context, token,
                              SeRestorePrivilege)

// Step 10: Audit emission.
continuous_audit_mask = 0
continuous_audit_nodes = []

if mapped_desired == 0:
    access_success = true
else:
    access_success = (granted & mapped_desired) == mapped_desired

if sd.control.SE_SACL_PRESENT is set:
    audit_sid_match = |sid, for_allow| SidMatchesToken(
                          sid, enriched_token, for_allow)

    for ace in sd.sacl.aces:
        if ace.flags & INHERIT_ONLY:
            continue

        // --- Access Auditing (SYSTEM_AUDIT types) ---
        if ace.type in [SYSTEM_AUDIT, SYSTEM_AUDIT_CALLBACK,
                        SYSTEM_AUDIT_OBJECT, SYSTEM_AUDIT_CALLBACK_OBJECT]:

            audit_on_success = (ace.flags & SUCCESSFUL_ACCESS_ACE_FLAG) != 0
            audit_on_failure = (ace.flags & FAILED_ACCESS_ACE_FLAG) != 0
            if not audit_on_success and not audit_on_failure:
                continue

            if access_success and not audit_on_success:
                continue
            if not access_success and not audit_on_failure:
                continue

            if not audit_sid_match(ace.sid, false):
                continue

            if ace.type in [SYSTEM_AUDIT_CALLBACK,
                            SYSTEM_AUDIT_CALLBACK_OBJECT]:
                if ace.condition is not null:
                    cond = EvaluateConditionalExpression(
                               ace.condition, enriched_token,
                               resource_attributes, local_claims,
                               for_allow=false)
                    if cond == FALSE:
                        continue

            if ace.type in [SYSTEM_AUDIT_OBJECT,
                            SYSTEM_AUDIT_CALLBACK_OBJECT]:
                if ace.object_type_present and object_tree is not null:
                    n = FindNode(object_tree, ace.object_type)
                    if n is null:
                        continue
                    ace_mask = MapGenericBits(ace.mask, mapping)
                    if mapped_desired == 0:
                        node_success = true
                    else:
                        node_success = (n.granted & mapped_desired) == mapped_desired

                    if node_success and not audit_on_success:
                        continue
                    if not node_success and not audit_on_failure:
                        continue

                    if node_success:
                        if (n.granted & ace_mask) == 0:
                            continue
                    else:
                        if (ace_mask & mapped_desired & ~n.granted) == 0:
                            continue

                    EmitAccessAudit(object_audit_context, token,
                                    mapped_desired, n.granted,
                                    node_success, ace, n)
                    continue

            ace_mask = MapGenericBits(ace.mask, mapping)
            if access_success:
                if (granted & ace_mask) == 0:
                    continue
            else:
                if (ace_mask & mapped_desired & ~granted) == 0:
                    continue

            EmitAccessAudit(object_audit_context, token,
                            mapped_desired, granted,
                            access_success, ace, null)

        // --- Continuous Auditing (SYSTEM_ALARM types) ---
        else if ace.type in [SYSTEM_ALARM, SYSTEM_ALARM_CALLBACK,
                             SYSTEM_ALARM_OBJECT,
                             SYSTEM_ALARM_CALLBACK_OBJECT]:

            if not access_success:
                continue

            if not audit_sid_match(ace.sid, false):
                continue

            if ace.type in [SYSTEM_ALARM_CALLBACK,
                            SYSTEM_ALARM_CALLBACK_OBJECT]:
                if ace.condition is not null:
                    cond = EvaluateConditionalExpression(
                               ace.condition, enriched_token,
                               resource_attributes, local_claims,
                               for_allow=false)
                    if cond == FALSE:
                        continue

            ace_mask = MapGenericBits(ace.mask, mapping)

            if ace.type in [SYSTEM_ALARM_OBJECT,
                            SYSTEM_ALARM_CALLBACK_OBJECT]:
                if ace.object_type_present and object_tree is not null:
                    n = FindNode(object_tree, ace.object_type)
                    if n is null:
                        continue
                    node_mask = ace_mask & n.granted
                    if node_mask != 0:
                        existing = continuous_audit_nodes.find(ace.object_type)
                        if existing is not null:
                            existing.mask |= node_mask
                        else:
                            continuous_audit_nodes.append(
                                (ace.object_type, node_mask))
                    continue

            continuous_audit_mask |= (ace_mask & granted)

return (decided, granted, privilege_granted, max_allowed_mode,
        mapped_desired, continuous_audit_mask, continuous_audit_nodes)
```

## EvaluateSecurityDescriptor

Per-SD evaluation pipeline. Steps 1-8a: validation, generic mapping, privilege grants, MIC, virtual group injection, DACL walk, restricted token pass, and confinement.

```
EvaluateSecurityDescriptor(
    SecurityDescriptor  sd,
    Token               token,
    ACCESS_MASK         desired,
    GenericMapping      mapping,
    OBJECT_TYPE_LIST[]  object_tree,
    SID                 self_sid,
    CLAIM_ATTRIBUTES[]  local_claims,
    uint32              privilege_intent,
) -> (decided, granted, privilege_granted, max_allowed_mode, mapped_desired,
      resource_attributes, policy_sids) | error

// Step 1: Input validation.
if sd is null:
    return ERROR_INVALID_PARAMETER
if sd.owner is null or sd.group is null:
    return ERROR_INVALID_SECURITY_DESCR
if object_tree is not null:
    if object_tree is empty:
        return ERROR_INVALID_PARAMETER
    if object_tree[0].Level != 0:
        return ERROR_INVALID_PARAMETER
    level_0_count = 0
    for i = 0 to len(object_tree) - 1:
        if object_tree[i].Level < 0:
            return ERROR_INVALID_PARAMETER
        if object_tree[i].Level == 0:
            level_0_count += 1
        if level_0_count > 1:
            return ERROR_INVALID_PARAMETER
        if i > 0 and object_tree[i].Level > object_tree[i-1].Level + 1:
            return ERROR_INVALID_PARAMETER
    if duplicate GUIDs in object_tree:
        return ERROR_INVALID_PARAMETER

// Step 2: Generic mapping.
desired = MapGenericBits(desired, mapping)

// Step 2a: Strip MAXIMUM_ALLOWED meta-bit.
max_allowed_mode = (desired & MAXIMUM_ALLOWED) != 0
desired = desired & ~MAXIMUM_ALLOWED

// Step 2b: Compute effective privileges.
effective_privileges = token.privileges_enabled
if not (privilege_intent & BACKUP_INTENT):
    effective_privileges &= ~SeBackupPrivilege
if not (privilege_intent & RESTORE_INTENT):
    effective_privileges &= ~SeRestorePrivilege

// Step 3: Privilege-based grants.
decided  = 0
granted  = 0
privilege_granted = 0

// ACCESS_SYSTEM_SECURITY: always decided.
decided |= ACCESS_SYSTEM_SECURITY
if (effective_privileges & SeSecurityPrivilege):
    granted |= ACCESS_SYSTEM_SECURITY
    privilege_granted |= ACCESS_SYSTEM_SECURITY

// Backup privilege: grant all read-mapped bits.
if (effective_privileges & SeBackupPrivilege):
    backup_bits = MapGenericBits(GENERIC_READ, mapping)
    decided |= backup_bits
    granted |= backup_bits
    privilege_granted |= backup_bits

// Restore privilege: grant all write-mapped bits + standard rights.
if (effective_privileges & SeRestorePrivilege):
    restore_bits = MapGenericBits(GENERIC_WRITE, mapping)
                   | WRITE_DAC | WRITE_OWNER | DELETE
                   | ACCESS_SYSTEM_SECURITY
    decided |= restore_bits
    granted |= restore_bits
    privilege_granted |= restore_bits

// WRITE_OWNER: deferred to step 7a (post-DACL privilege override).

// Step 4: Pre-SACL walk.
resource_attributes = {}
policy_sids = []
PreSACLWalk(sd, token, mapping, &decided, &granted,
            &privilege_granted, &resource_attributes, &policy_sids)

// Step 5: Virtual group injection.
token = EnrichToken(token, sd.owner, self_sid)

// Step 6: Initialize tree nodes.
if object_tree is not null:
    for each node in object_tree:
        node.decided = decided
        node.granted = granted

// Step 7: Normal DACL evaluation.
normal_sid_match = |sid, for_allow| SidMatchesToken(sid, token, for_allow)
EvaluateDACL(sd, token, mapping, object_tree,
             normal_sid_match, desired, max_allowed_mode,
             resource_attributes, local_claims,
             skip_owner_implicit=false,
             &decided, &granted)

// Step 7a: Post-DACL privilege override for WRITE_OWNER.
if (desired & WRITE_OWNER) != 0 or max_allowed_mode:
    if (effective_privileges & SeTakeOwnershipPrivilege):
        if not (granted & WRITE_OWNER):
            decided |= WRITE_OWNER
            granted |= WRITE_OWNER
            privilege_granted |= WRITE_OWNER
            if object_tree is not null:
                for each node in object_tree:
                    if not (node.granted & WRITE_OWNER):
                        node.decided |= WRITE_OWNER
                        node.granted |= WRITE_OWNER

// Step 8: Restricted token two-pass.
if token.restricting_sids is not empty:
    r_decided = 0
    r_granted = 0

    restricted_sids = token.restricting_sids
    if SidInRestrictingSids(sd.owner, restricted_sids):
        restricted_sids = restricted_sids.with(SID_OWNER_RIGHTS)
    if self_sid is not null
       and SidInRestrictingSids(self_sid, restricted_sids):
        restricted_sids = restricted_sids.with(SID_PRINCIPAL_SELF)

    if object_tree is not null:
        r_tree = deep_copy(object_tree)
        for each node in r_tree:
            node.decided = 0
            node.granted = 0
    else:
        r_tree = null

    restricted_sid_match = |sid, _| SidInRestrictingSids(sid,
                                        restricted_sids)
    EvaluateDACL(sd, token, mapping, r_tree,
                 restricted_sid_match, desired, max_allowed_mode,
                 resource_attributes, local_claims,
                 skip_owner_implicit=false,
                 &r_decided, &r_granted)

    // Scalar merge.
    if token.write_restricted:
        write_bits = MapGenericBits(GENERIC_WRITE, mapping)
        granted = (granted & ~write_bits)
               | (granted & r_granted & write_bits)
    else:
        granted = granted & r_granted
    granted |= privilege_granted

    // Tree merge.
    if object_tree is not null:
        if token.write_restricted:
            for i = 0 to len(object_tree) - 1:
                object_tree[i].granted =
                    (object_tree[i].granted & ~write_bits)
                  | (object_tree[i].granted & r_tree[i].granted
                     & write_bits)
        else:
            for i = 0 to len(object_tree) - 1:
                object_tree[i].granted =
                    object_tree[i].granted & r_tree[i].granted

        for i = 0 to len(object_tree) - 1:
            object_tree[i].granted |= privilege_granted

// Step 8a: Application Confinement.
if token.confinement_sid is not null and not token.confinement_exempt:
    c_decided = 0
    c_granted = 0

    confinement_sids = [token.confinement_sid]
                     + token.confinement_capabilities

    if SidInList(sd.owner, confinement_sids):
        confinement_sids = confinement_sids.with(SID_OWNER_RIGHTS)
    if self_sid is not null
       and SidInList(self_sid, confinement_sids):
        confinement_sids = confinement_sids.with(SID_PRINCIPAL_SELF)

    confinement_sid_match = |sid, _| SidInList(sid, confinement_sids)

    if object_tree is not null:
        c_tree = deep_copy(object_tree)
        for each node in c_tree:
            node.decided = 0
            node.granted = 0
    else:
        c_tree = null

    EvaluateDACL(sd, token, mapping, c_tree,
                 confinement_sid_match, desired, max_allowed_mode,
                 resource_attributes, local_claims,
                 skip_owner_implicit=true,
                 &c_decided, &c_granted)

    // Scalar merge: absolute, no privilege bypass.
    granted = granted & c_granted

    // Tree merge: absolute per-node, no privilege bypass.
    if object_tree is not null:
        for i = 0 to len(object_tree) - 1:
            object_tree[i].granted =
                object_tree[i].granted & c_tree[i].granted

return (decided, granted, privilege_granted, max_allowed_mode, desired,
        resource_attributes, policy_sids)
```

## EvaluateDACL

Unified DACL evaluation. Called for normal, restricted, and confinement passes.

```
EvaluateDACL(sd, token, mapping, object_tree,
             sid_match,
             desired, max_allowed_mode,
             resource_attributes,
             local_claims,
             skip_owner_implicit,
             &decided, &granted)

    // Owner implicit rights.
    if not skip_owner_implicit and sid_match(sd.owner, true):
        owner_rights_present = false
        if sd.control.SE_DACL_PRESENT is set:
            for ace in sd.dacl.aces:
                if ace.flags & INHERIT_ONLY:
                    continue
                if ace.type not in [ACCESS_ALLOWED, ACCESS_DENIED,
                        ACCESS_ALLOWED_CALLBACK, ACCESS_DENIED_CALLBACK,
                        ACCESS_ALLOWED_OBJECT, ACCESS_DENIED_OBJECT,
                        ACCESS_ALLOWED_CALLBACK_OBJECT,
                        ACCESS_DENIED_CALLBACK_OBJECT]:
                    continue
                if ace.sid == SID_OWNER_RIGHTS:
                    owner_rights_present = true
                    break

        if not owner_rights_present:
            new_bits = (READ_CONTROL | WRITE_DAC) & ~decided
            decided |= new_bits
            granted |= new_bits
            if object_tree is not null:
                for each node in object_tree:
                    node_new = (READ_CONTROL | WRITE_DAC) & ~node.decided
                    node.decided |= node_new
                    node.granted |= node_new

    // NULL DACL — grant all valid remaining bits.
    if sd.control.SE_DACL_PRESENT is not set:
        all_bits = MapGenericBits(GENERIC_ALL, mapping)
        new_bits = all_bits & ~decided
        decided |= new_bits
        granted |= new_bits
        if object_tree is not null:
            for each node in object_tree:
                node_new = all_bits & ~node.decided
                node.decided |= node_new
                node.granted |= node_new
        return

    // DACL walk.
    for ace in sd.dacl.aces:
        if ace.flags & INHERIT_ONLY:
            continue

        ace_mask = MapGenericBits(ace.mask, mapping)

        if ace.type in [ACCESS_ALLOWED, ACCESS_ALLOWED_CALLBACK]:
            if sid_match(ace.sid, true):
                if ace.type == ACCESS_ALLOWED_CALLBACK:
                    if ace.condition is null:
                        continue
                    cond = EvaluateConditionalExpression(
                               ace.condition, token,
                               resource_attributes, local_claims,
                               for_allow=true)
                    if cond != TRUE:
                        continue
                else if ace.condition is not null:
                    cond = EvaluateConditionalExpression(
                               ace.condition, token,
                               resource_attributes, local_claims,
                               for_allow=true)
                    if cond != TRUE:
                        continue

                // Scalar: grant.
                new_bits = ace_mask & ~decided
                decided |= new_bits
                granted |= new_bits
                // Tree: grant all nodes.
                if object_tree is not null:
                    for each node in object_tree:
                        node_new = ace_mask & ~node.decided
                        node.decided |= node_new
                        node.granted |= node_new

        else if ace.type in [ACCESS_DENIED, ACCESS_DENIED_CALLBACK]:
            if sid_match(ace.sid, false):
                if ace.condition is not null:
                    cond = EvaluateConditionalExpression(
                               ace.condition, token,
                               resource_attributes, local_claims,
                               for_allow=false)
                    if cond == FALSE:
                        continue

                // Scalar: deny (decided, not granted).
                new_bits = ace_mask & ~decided
                decided |= new_bits
                // Tree: deny all nodes.
                if object_tree is not null:
                    for each node in object_tree:
                        node_new = ace_mask & ~node.decided
                        node.decided |= node_new

        else if ace.type in [ACCESS_ALLOWED_OBJECT,
                             ACCESS_ALLOWED_CALLBACK_OBJECT]:
            if sid_match(ace.sid, true):
                if ace.type == ACCESS_ALLOWED_CALLBACK_OBJECT:
                    if ace.condition is null:
                        continue
                    cond = EvaluateConditionalExpression(
                               ace.condition, token,
                               resource_attributes, local_claims,
                               for_allow=true)
                    if cond != TRUE:
                        continue
                else if ace.condition is not null:
                    cond = EvaluateConditionalExpression(
                               ace.condition, token,
                               resource_attributes, local_claims,
                               for_allow=true)
                    if cond != TRUE:
                        continue

                if not ace.object_type_present or object_tree is null:
                    new_bits = ace_mask & ~decided
                    decided |= new_bits
                    granted |= new_bits
                    if object_tree is not null:
                        for each node in object_tree:
                            node_new = ace_mask & ~node.decided
                            node.decided |= node_new
                            node.granted |= node_new

                else:
                    n = FindNode(object_tree, ace.object_type)
                    if n is not null:
                        // Grant target + descendants.
                        node_new = ace_mask & ~n.decided
                        n.decided |= node_new
                        n.granted |= node_new
                        for each descendant d of n:
                            d_new = ace_mask & ~d.decided
                            d.decided |= d_new
                            d.granted |= d_new

                        // Sibling aggregation upward.
                        v = n
                        while v.Level > 0:
                            common = v.granted
                            for each s in Siblings(v, object_tree):
                                common &= s.granted
                                if common == 0:
                                    break
                            if common == 0:
                                break
                            p = Ancestors(v, object_tree)[0]
                            p_new = common & ~p.decided
                            if p_new == 0:
                                break
                            p.decided |= p_new
                            p.granted |= p_new
                            v = p

        else if ace.type in [ACCESS_DENIED_OBJECT,
                             ACCESS_DENIED_CALLBACK_OBJECT]:
            if sid_match(ace.sid, false):
                if ace.condition is not null:
                    cond = EvaluateConditionalExpression(
                               ace.condition, token,
                               resource_attributes, local_claims,
                               for_allow=false)
                    if cond == FALSE:
                        continue

                if not ace.object_type_present or object_tree is null:
                    new_bits = ace_mask & ~decided
                    decided |= new_bits
                    if object_tree is not null:
                        for each node in object_tree:
                            node_new = ace_mask & ~node.decided
                            node.decided |= node_new

                else:
                    n = FindNode(object_tree, ace.object_type)
                    if n is not null:
                        // Deny target + descendants.
                        node_new = ace_mask & ~n.decided
                        n.decided |= node_new
                        for each descendant d of n:
                            d_new = ace_mask & ~d.decided
                            d.decided |= d_new

                        // Ancestor deny propagation.
                        for each w in Ancestors(n, object_tree):
                            w.decided |= ace_mask

        // Short-circuit: all desired bits decided (non-tree only).
        if object_tree is null and not max_allowed_mode
           and desired != 0 and (decided & desired) == desired:
            break
```

## PreSACLWalk

```
PreSACLWalk(sd, token, mapping, &decided, &granted,
            &privilege_granted, &resource_attributes, &policy_sids)

    mic_ace = null
    mic_found = false
    pip_ace = null
    pip_found = false

    if sd.control.SE_SACL_PRESENT is set:
        for ace in sd.sacl.aces:
            if ace.type == SYSTEM_MANDATORY_LABEL and not mic_found:
                mic_found = true
                if not (ace.flags & INHERIT_ONLY):
                    mic_ace = ace

            else if ace.type == SYSTEM_RESOURCE_ATTRIBUTE:
                attr = parse_claim_attribute(ace.attribute_data)
                if attr.name not in resource_attributes:
                    resource_attributes[attr.name] = attr

            else if ace.type == SYSTEM_PROCESS_TRUST_LABEL and not pip_found:
                pip_found = true
                if not (ace.flags & INHERIT_ONLY):
                    pip_ace = ace

            else if ace.type == SYSTEM_SCOPED_POLICY_ID:
                if not (ace.flags & INHERIT_ONLY):
                    policy_sids.append(ace.sid)

    // MIC: use found label or default (Medium, NO_WRITE_UP).
    if mic_ace is not null:
        EnforceMIC(mic_ace, token, mapping, &decided)
    else:
        EnforceMIC(default_label_ace(SID_MEDIUM_INTEGRITY,
                   SYSTEM_MANDATORY_LABEL_NO_WRITE_UP),
                   token, mapping, &decided)

    // PIP: only enforced if a trust label ACE is present.
    if pip_ace is not null:
        EnforcePIP(pip_ace, token, mapping, &decided, &granted,
                   &privilege_granted)
```

## EnforceMIC

```
EnforceMIC(ace, token, mapping, &decided)

    if not (token.mandatory_policy & TOKEN_MANDATORY_POLICY_NO_WRITE_UP):
        return

    token_dominates = (token.integrity_level >= ace.sid)

    // Compute allowed set.
    allowed = MapGenericBits(GENERIC_READ, mapping)
           | MapGenericBits(GENERIC_EXECUTE, mapping)

    if token_dominates:
        allowed |= MapGenericBits(GENERIC_WRITE, mapping)

    if not token_dominates:
        if ace.mask & SYSTEM_MANDATORY_LABEL_NO_READ_UP:
            allowed &= ~MapGenericBits(GENERIC_READ, mapping)
        if ace.mask & SYSTEM_MANDATORY_LABEL_NO_WRITE_UP:
            allowed &= ~MapGenericBits(GENERIC_WRITE, mapping)
        if ace.mask & SYSTEM_MANDATORY_LABEL_NO_EXECUTE_UP:
            allowed &= ~MapGenericBits(GENERIC_EXECUTE, mapping)

    if token.privilege_enabled(SeRelabelPrivilege):
        allowed |= WRITE_OWNER

    all_bits = MapGenericBits(GENERIC_ALL, mapping)
    decided |= all_bits & ~allowed
```

## EnforcePIP

```
EnforcePIP(ace, token, mapping, &decided, &granted, &privilege_granted)

    ace_type = ace.sid.pip_type
    ace_trust = ace.sid.pip_trust

    token_dominates = (token.pip_type >= ace_type
                       and token.pip_trust >= ace_trust)

    // Phase 1: seed with R + E. Add W only if token dominates.
    allowed = MapGenericBits(GENERIC_READ, mapping)
           | MapGenericBits(GENERIC_EXECUTE, mapping)

    if token_dominates:
        allowed |= MapGenericBits(GENERIC_WRITE, mapping)

    // Phase 2: ACE mask flags remove categories when not dominant.
    if not token_dominates:
        if ace.mask & SYSTEM_PROCESS_TRUST_LABEL_NO_READ_UP:
            allowed &= ~MapGenericBits(GENERIC_READ, mapping)
        if ace.mask & SYSTEM_PROCESS_TRUST_LABEL_NO_WRITE_UP:
            allowed &= ~MapGenericBits(GENERIC_WRITE, mapping)
        if ace.mask & SYSTEM_PROCESS_TRUST_LABEL_NO_EXECUTE_UP:
            allowed &= ~MapGenericBits(GENERIC_EXECUTE, mapping)

    // PIP includes ACCESS_SYSTEM_SECURITY — privileges cannot bypass.
    all_bits = MapGenericBits(GENERIC_ALL, mapping)
              | ACCESS_SYSTEM_SECURITY
    pip_denied = all_bits & ~allowed

    // Block DACL grants.
    decided |= pip_denied

    // Actively revoke privilege-granted rights that PIP denies.
    granted &= ~pip_denied
    privilege_granted &= ~pip_denied
```

## EvaluateConditionalExpression

```
EvaluateConditionalExpression(
    condition:           bytes,
    token:               Token,
    resource_attributes: CLAIM_ATTRIBUTES_MAP,
    local_claims:        CLAIM_ATTRIBUTES[],
    for_allow:           bool
) -> TRUE | FALSE | UNKNOWN

    if len(condition) < 4 or condition[0..4] != [0x61, 0x72, 0x74, 0x78]:
        return UNKNOWN

    stack = []
    pos = 4

    while pos < len(condition):
        op = condition[pos]; pos += 1

        if op == 0x00:                              // Padding
            continue

        // --- Literal values ---

        else if op in [0x01, 0x02, 0x03, 0x04]:     // Int8/16/32/64
            magnitude = read_uint64_le(condition, pos)
            sign = condition[pos + 8]
            pos += 10
            if sign == 0x02:
                value = -(magnitude as INT64)
            else:
                value = magnitude as INT64
            stack.push(Value(INT64, value, origin=LITERAL))

        else if op == 0x10:                          // Unicode string
            length = read_uint32_le(condition, pos); pos += 4
            value = decode_utf16le(condition, pos, length); pos += length
            stack.push(Value(STRING, value, origin=LITERAL))

        else if op == 0x18:                          // Octet string
            length = read_uint32_le(condition, pos); pos += 4
            value = condition[pos .. pos+length]; pos += length
            stack.push(Value(OCTET, value, origin=LITERAL))

        else if op == 0x50:                          // Composite (array)
            length = read_uint32_le(condition, pos); pos += 4
            elements = parse_composite(condition, pos, length)
            pos += length
            stack.push(Value(COMPOSITE, elements, origin=LITERAL))

        else if op == 0x51:                          // SID literal
            length = read_uint32_le(condition, pos); pos += 4
            value = parse_sid(condition, pos, length); pos += length
            stack.push(Value(SID, value, origin=LITERAL))

        // --- Attribute references ---

        else if op == 0xf8:                          // @Local.
            name = read_attr_name(condition, &pos)
            v = resolve_claim(local_claims, name, for_allow)
            v.origin = LOCAL_ATTR
            stack.push(v)

        else if op == 0xf9:                          // @User.
            name = read_attr_name(condition, &pos)
            v = resolve_claim(token.user_claims, name, for_allow)
            v.origin = USER_ATTR
            stack.push(v)

        else if op == 0xfa:                          // @Resource.
            name = read_attr_name(condition, &pos)
            v = resolve_resource_attr(resource_attributes, name,
                                      for_allow)
            v.origin = RESOURCE_ATTR
            stack.push(v)

        else if op == 0xfb:                          // @Device.
            name = read_attr_name(condition, &pos)
            v = resolve_claim(token.device_claims, name, for_allow)
            v.origin = DEVICE_ATTR
            stack.push(v)

        // --- Relational operators ---

        else if op == 0x80:                          // ==
            if len(stack) < 2: return UNKNOWN
            rhs = stack.pop(); lhs = stack.pop()
            stack.push(compare_equal(lhs, rhs))

        else if op == 0x81:                          // !=
            if len(stack) < 2: return UNKNOWN
            rhs = stack.pop(); lhs = stack.pop()
            stack.push(negate_tv(compare_equal(lhs, rhs)))

        else if op == 0x82:                          // <
            if len(stack) < 2: return UNKNOWN
            rhs = stack.pop(); lhs = stack.pop()
            stack.push(compare_ordered(lhs, rhs, LT))

        else if op == 0x83:                          // <=
            if len(stack) < 2: return UNKNOWN
            rhs = stack.pop(); lhs = stack.pop()
            stack.push(compare_ordered(lhs, rhs, LE))

        else if op == 0x84:                          // >
            if len(stack) < 2: return UNKNOWN
            rhs = stack.pop(); lhs = stack.pop()
            stack.push(compare_ordered(lhs, rhs, GT))

        else if op == 0x85:                          // >=
            if len(stack) < 2: return UNKNOWN
            rhs = stack.pop(); lhs = stack.pop()
            stack.push(compare_ordered(lhs, rhs, GE))

        else if op == 0x86:                          // Contains
            if len(stack) < 2: return UNKNOWN
            rhs = stack.pop(); lhs = stack.pop()
            stack.push(set_contains(lhs, rhs))

        else if op == 0x88:                          // Any_of
            if len(stack) < 2: return UNKNOWN
            rhs = stack.pop(); lhs = stack.pop()
            stack.push(set_any_of(lhs, rhs))

        else if op == 0x8e:                          // Not_Contains
            if len(stack) < 2: return UNKNOWN
            rhs = stack.pop(); lhs = stack.pop()
            stack.push(negate_tv(set_contains(lhs, rhs)))

        else if op == 0x8f:                          // Not_Any_of
            if len(stack) < 2: return UNKNOWN
            rhs = stack.pop(); lhs = stack.pop()
            stack.push(negate_tv(set_any_of(lhs, rhs)))

        // --- Existence operators ---

        else if op == 0x87:                          // Exists
            if len(stack) < 1: return UNKNOWN
            operand = stack.pop()
            if operand.origin not in [LOCAL_ATTR, RESOURCE_ATTR,
                                      USER_ATTR, DEVICE_ATTR]:
                return UNKNOWN
            stack.push(operand.type != NULL ? TRUE : FALSE)

        else if op == 0x8d:                          // Not_Exists
            if len(stack) < 1: return UNKNOWN
            operand = stack.pop()
            if operand.origin not in [LOCAL_ATTR, RESOURCE_ATTR,
                                      USER_ATTR, DEVICE_ATTR]:
                return UNKNOWN
            stack.push(operand.type == NULL ? TRUE : FALSE)

        // --- Membership operators ---

        else if op == 0x89:                          // Member_of
            if len(stack) < 1: return UNKNOWN
            operand = stack.pop()
            sids = to_sid_list(operand)
            if sids is error: return UNKNOWN
            stack.push(all_sids_match_token(sids, token, for_allow)
                       ? TRUE : FALSE)

        else if op == 0x8b:                          // Member_of_Any
            if len(stack) < 1: return UNKNOWN
            operand = stack.pop()
            sids = to_sid_list(operand)
            if sids is error: return UNKNOWN
            stack.push(any_sid_matches_token(sids, token, for_allow)
                       ? TRUE : FALSE)

        else if op == 0x8a:                          // Device_Member_of
            if len(stack) < 1: return UNKNOWN
            operand = stack.pop()
            sids = to_sid_list(operand)
            if sids is error: return UNKNOWN
            if token.device_sids is null:
                stack.push(UNKNOWN); continue
            stack.push(all_sids_match_token_device(sids, token,
                       for_allow) ? TRUE : FALSE)

        else if op == 0x8c:                          // Device_Member_of_Any
            if len(stack) < 1: return UNKNOWN
            operand = stack.pop()
            sids = to_sid_list(operand)
            if sids is error: return UNKNOWN
            if token.device_sids is null:
                stack.push(UNKNOWN); continue
            stack.push(any_sid_matches_token_device(sids, token,
                       for_allow) ? TRUE : FALSE)

        else if op == 0x90:                          // Not_Member_of
            if len(stack) < 1: return UNKNOWN
            operand = stack.pop()
            sids = to_sid_list(operand)
            if sids is error: return UNKNOWN
            stack.push(all_sids_match_token(sids, token, for_allow)
                       ? FALSE : TRUE)

        else if op == 0x92:                          // Not_Member_of_Any
            if len(stack) < 1: return UNKNOWN
            operand = stack.pop()
            sids = to_sid_list(operand)
            if sids is error: return UNKNOWN
            stack.push(any_sid_matches_token(sids, token, for_allow)
                       ? FALSE : TRUE)

        else if op == 0x91:                          // Not_Device_Member_of
            if len(stack) < 1: return UNKNOWN
            operand = stack.pop()
            sids = to_sid_list(operand)
            if sids is error: return UNKNOWN
            if token.device_sids is null:
                stack.push(UNKNOWN); continue
            stack.push(all_sids_match_token_device(sids, token,
                       for_allow) ? FALSE : TRUE)

        else if op == 0x93:                          // Not_Device_Member_of_Any
            if len(stack) < 1: return UNKNOWN
            operand = stack.pop()
            sids = to_sid_list(operand)
            if sids is error: return UNKNOWN
            if token.device_sids is null:
                stack.push(UNKNOWN); continue
            stack.push(any_sid_matches_token_device(sids, token,
                       for_allow) ? FALSE : TRUE)

        // --- Logical operators (three-value Kleene logic) ---

        else if op == 0xa0:                          // AND
            if len(stack) < 2: return UNKNOWN
            rhs = stack.pop(); lhs = stack.pop()
            if lhs.origin == LITERAL or rhs.origin == LITERAL:
                return UNKNOWN
            lhs_b = to_three_value(lhs)
            rhs_b = to_three_value(rhs)
            if lhs_b == FALSE or rhs_b == FALSE:
                stack.push(FALSE)
            else if lhs_b == TRUE and rhs_b == TRUE:
                stack.push(TRUE)
            else:
                stack.push(UNKNOWN)

        else if op == 0xa1:                          // OR
            if len(stack) < 2: return UNKNOWN
            rhs = stack.pop(); lhs = stack.pop()
            if lhs.origin == LITERAL or rhs.origin == LITERAL:
                return UNKNOWN
            lhs_b = to_three_value(lhs)
            rhs_b = to_three_value(rhs)
            if lhs_b == TRUE or rhs_b == TRUE:
                stack.push(TRUE)
            else if lhs_b == FALSE and rhs_b == FALSE:
                stack.push(FALSE)
            else:
                stack.push(UNKNOWN)

        else if op == 0xa2:                          // NOT
            if len(stack) < 1: return UNKNOWN
            operand = stack.pop()
            if operand.origin == LITERAL:
                return UNKNOWN
            v = to_three_value(operand)
            if v == TRUE:    stack.push(FALSE)
            else if v == FALSE: stack.push(TRUE)
            else:               stack.push(UNKNOWN)

        // --- Unknown opcode ---
        else:
            return UNKNOWN

    // Final result.
    if len(stack) != 1:
        return UNKNOWN
    if stack[0].origin == LITERAL:
        return UNKNOWN
    return to_three_value(stack[0])
```

## Helper Functions

```
EnrichToken(token, owner_sid, self_sid) -> Token

    caller_is_owner = SidMatchesToken(owner_sid, token, for_allow=true)
    if caller_is_owner:
        token = token.with_virtual_group(SID_OWNER_RIGHTS)

    if self_sid is not null:
        if SidMatchesToken(self_sid, token, for_allow=true):
            token = token.with_virtual_group(SID_PRINCIPAL_SELF)
        else if SidMatchesToken(self_sid, token, for_allow=false):
            token = token.with_virtual_group(SID_PRINCIPAL_SELF,
                                             deny_only=true)

    return token
```

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
SidInRestrictingSids(sid, restricting_sids) -> bool

    for rs in restricting_sids:
        if sid == rs:
            return true
    return false
```

```
SidInList(sid, sid_list) -> bool

    for s in sid_list:
        if sid == s:
            return true
    return false
```

```
MapGenericBits(mask, mapping) -> ACCESS_MASK

    if mask & GENERIC_READ:
        mask = (mask & ~GENERIC_READ)    | mapping.read
    if mask & GENERIC_WRITE:
        mask = (mask & ~GENERIC_WRITE)   | mapping.write
    if mask & GENERIC_EXECUTE:
        mask = (mask & ~GENERIC_EXECUTE) | mapping.execute
    if mask & GENERIC_ALL:
        mask = (mask & ~GENERIC_ALL)     | mapping.all
    return mask
```

```
FindNode(tree, guid) -> node or null

    for each node in tree:
        if node.GUID == guid:
            return node
    return null
```

```
Descendants(node) -> list of nodes

    result = []
    for each subsequent s after node:
        if s.Level <= node.Level:
            break
        result.append(s)
    return result
```

```
Siblings(node, tree) -> list of nodes

    if node.Level == 0:
        return []

    node_idx = index of node in tree
    parent_idx = -1
    for i = node_idx - 1 downto 0:
        if tree[i].Level < node.Level:
            parent_idx = i
            break

    result = []
    for i = parent_idx + 1 to len(tree) - 1:
        if tree[i].Level <= tree[parent_idx].Level:
            break
        if tree[i].Level == node.Level:
            if i != node_idx:
                result.append(tree[i])
    return result
```

```
Ancestors(node, tree) -> list of nodes

    result = []
    target_level = node.Level - 1
    node_idx = index of node in tree
    for i = node_idx - 1 downto 0:
        if tree[i].Level == target_level:
            result.append(tree[i])
            target_level -= 1
            if target_level < 0:
                break
    return result
```

## Types

```
OBJECT_TYPE_LIST:
    Level:   int
    GUID:    GUID
    decided: ACCESS_MASK
    granted: ACCESS_MASK
```

```
CentralAccessPolicy:
    CAPID:  SID
    rules:  CentralAccessPolicyRule[]

CentralAccessPolicyRule:
    applies_to:     bytes       // conditional expression (artx bytecode), null = applies to all
    effective_dacl: ACL
    staged_dacl:    ACL         // optional
```

```
RECOVERY_POLICY:
    // Hardcoded fallback for unknown CAPIDs.
    // DACL:
    //   ALLOW  GENERIC_ALL  to  BUILTIN_ADMINISTRATORS (S-1-5-32-544)
    //   ALLOW  GENERIC_ALL  to  LOCAL_SYSTEM (S-1-5-18)
    //   ALLOW  GENERIC_ALL  to  OWNER_RIGHTS (S-1-3-4)
    // No AppliesTo condition. No staged DACL.
```

```
CLAIM_ATTRIBUTES:
    Name:   string
    Type:   CLAIM_TYPE      // INT64, UINT64, STRING, SID, BOOLEAN, OCTET_STRING
    Flags:  uint16          // CASE_SENSITIVE (0x0002), USE_FOR_DENY_ONLY (0x0004),
                            // DISABLED (0x0010)
    Values: []
```

```
Value:
    type:   VALUE_TYPE      // INT64, UINT64, BOOLEAN, STRING, OCTET,
                            // SID, COMPOSITE, NULL, or RESULT
    data:   (type-dependent)
    origin: ORIGIN          // LITERAL, USER_ATTR, DEVICE_ATTR,
                            // LOCAL_ATTR, RESOURCE_ATTR, RESULT
    flags:  uint16          // from CLAIM_ATTRIBUTES.Flags when resolved
```

## Expression Helper Functions

```
resolve_claim(claims, name, for_allow) -> Value

    if claims is null:
        return Value(NULL)

    for attr in claims:
        if attr.Name == name:
            if attr.Flags & 0x0010:                    // DISABLED
                return Value(NULL)
            if (attr.Flags & 0x0004) and for_allow:    // USE_FOR_DENY_ONLY
                return Value(NULL)
            if len(attr.Values) == 0:
                return Value(NULL)
            vtype = claim_type_to_value_type(attr.Type)
            is_bool = (attr.Type == CLAIM_TYPE_BOOLEAN)
            if len(attr.Values) == 1:
                val = attr.Values[0]
                if is_bool:
                    val = (val != 0) ? 1 : 0
                return Value(vtype, val, flags=attr.Flags)
            else:
                elements = []
                for v in attr.Values:
                    if is_bool:
                        v = (v != 0) ? 1 : 0
                    elements.append(Value(vtype, v, flags=attr.Flags))
                return Value(COMPOSITE, elements, flags=attr.Flags)
    return Value(NULL)
```

```
resolve_resource_attr(resource_attributes, name, for_allow) -> Value

    if name in resource_attributes:
        attr = resource_attributes[name]
        if attr.Flags & 0x0010:                    // DISABLED
            return Value(NULL)
        if (attr.Flags & 0x0004) and for_allow:    // USE_FOR_DENY_ONLY
            return Value(NULL)
        if len(attr.Values) == 0:
            return Value(NULL)
        vtype = claim_type_to_value_type(attr.Type)
        is_bool = (attr.Type == CLAIM_TYPE_BOOLEAN)
        if len(attr.Values) == 1:
            val = attr.Values[0]
            if is_bool:
                val = (val != 0) ? 1 : 0
            return Value(vtype, val, flags=attr.Flags)
        else:
            elements = []
            for v in attr.Values:
                if is_bool:
                    v = (v != 0) ? 1 : 0
                elements.append(Value(vtype, v, flags=attr.Flags))
            return Value(COMPOSITE, elements, flags=attr.Flags)
    return Value(NULL)
```

```
to_sid_list(value) -> SID[] | error

    if value.type == SID:
        return [value.data]
    if value.type == COMPOSITE:
        if len(value.data) == 0:
            return error
        result = []
        for elem in value.data:
            if elem.type != SID:
                return error
            result.append(elem.data)
        return result
    return error
```

```
all_sids_match_token(needles, token, for_allow) -> bool

    for sid in needles:
        if not SidMatchesToken(sid, token, for_allow):
            return false
    return true
```

```
any_sid_matches_token(needles, token, for_allow) -> bool

    for sid in needles:
        if SidMatchesToken(sid, token, for_allow):
            return true
    return false
```

```
all_sids_match_token_device(needles, token, for_allow) -> bool

    for sid in needles:
        if not SidMatchesTokenDevice(sid, token, for_allow):
            return false
    return true
```

```
any_sid_matches_token_device(needles, token, for_allow) -> bool

    for sid in needles:
        if SidMatchesTokenDevice(sid, token, for_allow):
            return true
    return false
```

```
compare_equal(lhs, rhs) -> TRUE | FALSE | UNKNOWN

    if lhs.type == NULL or rhs.type == NULL:
        return UNKNOWN
    if (lhs.type == COMPOSITE) != (rhs.type == COMPOSITE):
        return UNKNOWN
    if not types_compatible(lhs, rhs):
        return UNKNOWN

    case_sensitive = (lhs.flags & 0x0002) or (rhs.flags & 0x0002)
    if values_equal(lhs, rhs, case_sensitive):
        return TRUE
    else:
        return FALSE
```

```
compare_ordered(lhs, rhs, ordering) -> TRUE | FALSE | UNKNOWN

    if lhs.type == NULL or rhs.type == NULL:
        return UNKNOWN
    if lhs.type == COMPOSITE or rhs.type == COMPOSITE:
        return UNKNOWN
    if lhs.type == BOOLEAN or rhs.type == BOOLEAN:
        return UNKNOWN
    if not types_compatible(lhs, rhs):
        return UNKNOWN

    case_sensitive = (lhs.flags & 0x0002) or (rhs.flags & 0x0002)
    cmp = compare_values(lhs, rhs, case_sensitive)
    match ordering:
        LT: return cmp < 0  ? TRUE : FALSE
        LE: return cmp <= 0 ? TRUE : FALSE
        GT: return cmp > 0  ? TRUE : FALSE
        GE: return cmp >= 0 ? TRUE : FALSE
```

```
set_contains(lhs, rhs) -> TRUE | FALSE | UNKNOWN

    if lhs.type == NULL or rhs.type == NULL:
        return UNKNOWN
    lhs_set = to_value_set(lhs)
    rhs_set = to_value_set(rhs)
    if len(rhs_set) == 0:
        return UNKNOWN
    for r in rhs_set:
        found = false
        saw_unknown = false
        for l in lhs_set:
            result = compare_equal(l, r)
            if result == TRUE:
                found = true
                break
            else if result == UNKNOWN:
                saw_unknown = true
        if not found:
            if saw_unknown:
                return UNKNOWN
            return FALSE
    return TRUE
```

```
set_any_of(lhs, rhs) -> TRUE | FALSE | UNKNOWN

    if lhs.type == NULL or rhs.type == NULL:
        return UNKNOWN
    lhs_set = to_value_set(lhs)
    rhs_set = to_value_set(rhs)
    if len(lhs_set) == 0 or len(rhs_set) == 0:
        return UNKNOWN
    saw_unknown = false
    for l in lhs_set:
        for r in rhs_set:
            result = compare_equal(l, r)
            if result == TRUE:
                return TRUE
            else if result == UNKNOWN:
                saw_unknown = true
    if saw_unknown:
        return UNKNOWN
    return FALSE
```

```
negate_tv(v) -> TRUE | FALSE | UNKNOWN

    if v == TRUE:    return FALSE
    if v == FALSE:   return TRUE
    return UNKNOWN
```

```
to_three_value(v) -> TRUE | FALSE | UNKNOWN

    if v is a result (TRUE/FALSE/UNKNOWN):
        return v
    if v.type == NULL:
        return UNKNOWN
    if v.type == INT64 or v.type == UINT64 or v.type == BOOLEAN:
        return v.data != 0 ? TRUE : FALSE
    if v.type == STRING:
        return len(v.data) > 0 ? TRUE : FALSE
    return UNKNOWN
```

```
EmitAccessAudit(object_audit_context, token, desired, granted,
                success, ace, node)

    // Emit an Access Audit event. Called from the audit walk (step 10)
    // when a SYSTEM_AUDIT ACE matches. Process context (PID, process
    // name, executable) captured from the kernel's current task struct.
    // Must be non-blocking — AccessCheck is the hot path.
```

```
EmitPrivilegeUseAudit(object_audit_context, token, privilege)

    // Emit a Privilege Use audit event. Called from step 9b when a
    // privilege was exercised and contributed to the final result.
```

```
LogStagingDifference(effective_granted, staged_granted)

    // Log the difference between effective and staged CAP results.
    // Produces an audit event showing which rights would change if
    // the staged policy were made effective.
```

```
claim_type_to_value_type(claim_type) -> VALUE_TYPE

    match claim_type:
        CLAIM_TYPE_INT64   (0x0001): return INT64
        CLAIM_TYPE_UINT64  (0x0002): return UINT64
        CLAIM_TYPE_STRING  (0x0003): return STRING
        CLAIM_TYPE_SID     (0x0005): return SID
        CLAIM_TYPE_BOOLEAN (0x0006): return BOOLEAN
        CLAIM_TYPE_OCTET   (0x0010): return OCTET
```
