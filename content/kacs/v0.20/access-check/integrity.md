---
title: Mandatory Integrity Control
order: 3
---

MIC is a mandatory constraint that restricts which rights the DACL is allowed to grant based on a vertical trust hierarchy. It is evaluated before the DACL walk.

Every token carries an integrity level. Every object MAY carry a mandatory label (a SYSTEM_MANDATORY_LABEL_ACE in its SACL). MIC compares the two: if the caller's integrity level is below the object's, certain categories of access are blocked regardless of what the DACL says.

## Default behaviour

The default is **no-write-up**: a lower-integrity process can read and execute a higher-integrity object but MUST NOT write to it. The object's mandatory label MAY additionally block reads (no-read-up) or execution (no-execute-up) for processes below its integrity level.

## Default label

When an object has no mandatory label ACE in its SACL, MIC applies a default: Medium integrity with no-write-up. This ensures Low and Untrusted processes MUST NOT write to unlabeled objects.

## MIC and privileges

Rights granted by privileges (resolved before MIC in the pipeline) are NOT constrained by MIC. MIC constrains what the DACL can grant; it does not revoke what privileges have already granted.

> [!INFORMATIVE]
> PIP fills the role of constraining privilege-granted access for objects that need protection even from administrators.

## SeRelabelPrivilege

SeRelabelPrivilege has a specific interaction with MIC: it allows the DACL to grant WRITE_OWNER even when MIC would otherwise block it due to an integrity level mismatch. This enables a privileged administrator to take ownership of a higher-integrity object as the first step in modifying it.

## Token integrity policy

MIC enforcement is controlled by the token's `mandatory_policy` field. When the NO_WRITE_UP flag is set (the default), MIC's no-write-up rule applies. When cleared, MIC is effectively disabled for that token.

The mandatory policy is fixed -- set at token creation time. A process MUST NOT loosen its own MIC constraints.

## Dominant callers

A caller whose integrity level is greater than or equal to the object's label dominates the object. MIC MUST NOT pre-decide any bits for dominant callers -- the DACL handles authorization normally.

## Multiple labels

If an object's SACL contains multiple mandatory label ACEs, only the first MUST be used.

## MIC enforcement algorithm

```
EnforceMIC(ace, token, mapping, &decided):

    if not (token.mandatory_policy & NO_WRITE_UP):
        return

    token_dominates = (token.integrity_level >= ace.integrity_level)

    if token_dominates:
        return

    // Non-dominant: start with read + execute, strip based on label policy.
    allowed = MapGenericBits(GENERIC_READ, mapping)
            | MapGenericBits(GENERIC_EXECUTE, mapping)

    if ace.mask & SYSTEM_MANDATORY_LABEL_NO_READ_UP:
        allowed &= ~MapGenericBits(GENERIC_READ, mapping)
    if ace.mask & SYSTEM_MANDATORY_LABEL_NO_WRITE_UP:
        allowed &= ~MapGenericBits(GENERIC_WRITE, mapping)
    if ace.mask & SYSTEM_MANDATORY_LABEL_NO_EXECUTE_UP:
        allowed &= ~MapGenericBits(GENERIC_EXECUTE, mapping)

    // SeRelabelPrivilege: allow WRITE_OWNER through MIC.
    if token.privilege_enabled(SeRelabelPrivilege):
        allowed |= WRITE_OWNER

    all_bits = MapGenericBits(GENERIC_ALL, mapping)
    decided |= all_bits & ~allowed
```
