---
title: PIP in AccessCheck
order: 7
---

Objects MAY opt in to PIP protection by placing a SYSTEM_PROCESS_TRUST_LABEL_ACE in their SACL. The ACE's SID encodes the required `pip_type` and `pip_trust`. The ACE's access mask specifies the exact rights that non-dominant callers are allowed.

When AccessCheck encounters a trust label, it compares the caller's process (which carries `pip_type` and `pip_trust` on the PSB) against the ACE:

- If the caller **dominates** (pip_type >= ACE type AND pip_trust >= ACE trust), PIP imposes no restrictions.
- If the caller **does not dominate**, only the rights in the ACE mask are permitted; everything else is denied.

## Privilege revocation

The critical difference from MIC: PIP actively revokes privilege-granted rights. If a non-dominant process used SeBackupPrivilege to gain read access, PIP strips those bits. If SeTakeOwnershipPrivilege granted WRITE_OWNER, PIP strips it. If SeSecurityPrivilege granted ACCESS_SYSTEM_SECURITY, PIP strips it.

Without privilege revocation, a non-PIP administrator with SeSecurityPrivilege could read the SACL of PIP-protected objects -- including removing the trust label itself.

## No default

Unlike MIC, PIP has no default. Objects without a trust label ACE are unrestricted -- any process can access them regardless of PIP identity.

## No privilege escape

PIP has no SeRelabelPrivilege equivalent. No privilege can compensate for insufficient trust level. This is an absolute boundary.

## Multiple trust labels

If multiple SYSTEM_PROCESS_TRUST_LABEL_ACEs appear in the SACL, only the first MUST be used.

## PIP enforcement algorithm

```
EnforcePIP(ace, pip_type, pip_trust, mapping, &decided,
           &granted, &privilege_granted):

    // pip_type and pip_trust come from the PSB, not the token.

    ace_type = ace.sid.pip_type
    ace_trust = ace.sid.pip_trust

    caller_dominates = (pip_type >= ace_type
                        and pip_trust >= ace_trust)

    if caller_dominates:
        return

    // Non-dominant: the ACE mask IS the allowed set.
    allowed = MapGenericBits(ace.mask, mapping)

    // Compute denied set: everything not explicitly allowed.
    // Includes ACCESS_SYSTEM_SECURITY.
    all_bits = MapGenericBits(GENERIC_ALL, mapping)
              | ACCESS_SYSTEM_SECURITY
    pip_denied = all_bits & ~allowed

    decided |= pip_denied

    // Revoke privilege-granted rights.
    granted &= ~pip_denied
    privilege_granted &= ~pip_denied
```
