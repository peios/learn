---
title: PIP in AccessCheck
description: How a trust label ACE is evaluated — the label SID, the privileges it revokes, the algorithm, and where the compared values come from.
---

An object opts in to PIP protection by carrying a
`SYSTEM_PROCESS_TRUST_LABEL_ACE` in its SACL. The ACE's SID encodes
the required type and trust, and its access mask names exactly the
rights a non-dominant caller may still have.

A caller that **dominates** — `pip_type` and `pip_trust` both greater
than or equal to the ACE's — is unrestricted by PIP. A caller that
does not dominate is limited to the ACE mask, and everything else is
denied.

Unlike MIC, PIP has **no default**. An object with no trust label is
unrestricted, reachable by any process whatever its PIP identity.

## The label SID

A trust label SID has the form `S-1-19-{type}-{trust}` — the Process
Trust authority, exactly two sub-authorities. Both axes are compared
numerically. The conventional type values are 0 (None), 512
(Protected) and 1024 (Isolated), but they are labels rather than a
closed enum: any other numeric type is valid and compared by the same
dominance rule.

A trust label SID of any other shape — wrong authority, wrong
sub-authority count — makes the descriptor malformed, and AccessCheck
rejects it outright rather than guessing.

Where a SACL carries more than one trust label ACE, only the first
non-inherit-only one is used; inherit-only labels do not apply to the
object carrying them.

## Privilege revocation

This is the critical difference from MIC. PIP does not merely
constrain what the DACL may grant — it **revokes rights privileges
already granted**. A non-dominant caller who used `SeBackupPrivilege`
to obtain read has those bits stripped; `SeTakeOwnershipPrivilege`'s
`WRITE_OWNER` is stripped; `SeSecurityPrivilege`'s
`ACCESS_SYSTEM_SECURITY` is stripped.

The last of those is the point. Without privilege revocation, a
non-dominant administrator holding `SeSecurityPrivilege` could read
the SACL of a PIP-protected object — and remove the trust label from
it. PIP would be self-defeating.

There is no escape hatch. PIP has no `SeRelabelPrivilege` equivalent,
and no privilege compensates for insufficient trust. It is an absolute
boundary, which is why the enforcement step explicitly ORs
`ACCESS_SYSTEM_SECURITY` into the set of bits it can take away —
that right is outside the generic mapping and would otherwise escape.

## The algorithm

```
EnforcePIP(ace, pip_type, pip_trust, mapping, &decided,
           &granted, &privilege_granted):

    // pip_type and pip_trust are the subject's process-trust context,
    // not a token field. See "Where the values come from" below.

    ace_type  = ace.sid.pip_type
    ace_trust = ace.sid.pip_trust

    caller_dominates = (pip_type  >= ace_type
                    and pip_trust >= ace_trust)

    if caller_dominates:
        return

    // Non-dominant: the ACE mask IS the allowed set.
    allowed = MapGenericBits(ace.mask, mapping)

    // Everything not explicitly allowed is denied, including
    // ACCESS_SYSTEM_SECURITY.
    all_bits = MapGenericBits(GENERIC_ALL, mapping)
             | ACCESS_SYSTEM_SECURITY
    pip_denied = all_bits & ~allowed

    decided |= pip_denied

    // Revoke privilege-granted rights.
    granted           &= ~pip_denied
    privilege_granted &= ~pip_denied
```

## Where the values come from

`pip_type` and `pip_trust` are the subject's process trust context and
are never derived from a token field — the token structure has no PIP
field at all. They are passed into AccessCheck as explicit parameters
by whichever layer is enforcing.

During enforcement — FACS file access, process boundaries — the values
are the subject process's PSB, set at exec from the binary's signature
(§3.6, §3.7).

The `kacs_access_check` query may instead supply them through its
arguments, per axis: zero means "use the calling process's PSB value"
and a nonzero value evaluates against the supplied context. This lets
a userspace broker evaluate access under a client's trust level, in
the same way the query's token argument lets it evaluate a token other
than its own. The query is advisory and gates nothing in the kernel;
enforcement always uses the PSB. The same effective values are used
for the verdict and for the event the check emits, so an audit record
never disagrees with the decision it describes.

The enforcement step also computes a record of which bits PIP decided.
Nothing currently consumes it — it is threaded through three
structures and exported, and no caller reads it.
