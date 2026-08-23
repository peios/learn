---
title: Mandatory Integrity Control
description: MIC restricts what the DACL is allowed to grant along a vertical trust hierarchy — the labels, the policy bits, and the algorithm.
---

MIC is a mandatory constraint that restricts which rights the DACL is
allowed to grant, along a vertical trust hierarchy. It is evaluated
**before** the DACL walk, in the pre-SACL phase.

Every token carries an integrity level, and every object may carry a
mandatory label — a `SYSTEM_MANDATORY_LABEL_ACE` in its SACL. MIC
compares the two: a caller below the object's level is blocked from
whole categories of access whatever the DACL says.

The default is **no-write-up**. A lower-integrity process can read and
execute a higher-integrity object but cannot write to it, and the
object's label may additionally block reads or execution for callers
beneath it.

An object with no mandatory label ACE in its SACL — or no SACL at all
— is treated as Medium integrity with no-write-up, so Low and
Untrusted processes cannot write to unlabelled objects.

A caller whose level is greater than or equal to the object's label
**dominates** it, and MIC pre-decides nothing: the DACL handles
authorization normally.

## What MIC does and does not touch

MIC constrains what the DACL can grant. It does not revoke what
privileges have already granted, because it mutates only `decided` and
never touches `granted` or `privilege_granted`.

`ACCESS_SYSTEM_SECURITY` is outside its reach for a structural reason:
the bits MIC can decide are bounded by
`MapGenericBits(GENERIC_ALL, mapping)`, which does not include it. The
right is privilege-granted rather than DACL-granted, so MIC never
blocks it. PIP is stricter and does revoke it for non-dominant callers
— explicitly ORing it into the set of bits it can take away — which is
the mechanism by which objects stay protected even from
administrators.

`SeRelabelPrivilege` has one specific interaction: it lets the DACL
grant `WRITE_OWNER` even when an integrity mismatch would otherwise
block it, so a privileged administrator can take ownership of a
higher-integrity object as the first step in modifying it. The bit
granted this way is recorded under its own provenance and is
deliberately **not** part of `privilege_granted`, so it is not
restored after the restricted merge and is not preserved by the CAAP
error escape hatch.

Enforcement is gated on the token's `mandatory_policy`: with
`NO_WRITE_UP` set — the default — the rule applies, and with it clear
MIC is effectively disabled for that token. The field is fixed at
creation (§3.2.2), which is what makes MIC a boundary rather than a
suggestion.

## Labels

An object's SACL may carry more than one mandatory label ACE. Only the
first non-inherit-only one is used; inherit-only labels do not apply
to the object carrying them.

The SID in a mandatory label ACE has the Mandatory Label authority
(`S-1-16`) and exactly one sub-authority, and that sub-authority value
*is* the integrity level, compared as an unsigned integer. Any
`S-1-16-X` is therefore valid.

| SID | Level | Name |
|---|---:|---|
| `S-1-16-0` | 0 | Untrusted |
| `S-1-16-4096` | 4096 | Low |
| `S-1-16-8192` | 8192 | Medium |
| `S-1-16-12288` | 12288 | High |
| `S-1-16-16384` | 16384 | System |

Peios tooling and authd use these five, but intermediate values such
as `S-1-16-2048` or `S-1-16-8448` are valid and compared numerically,
which is what allows Windows-originated descriptors carrying
non-standard levels to be evaluated without translation.

A label ACE whose SID falls outside the `S-1-16` authority — wrong
identifier authority, or the wrong sub-authority count — is
malformed, and so is one that is not a plain single-SID ACE. Either
causes AccessCheck to reject the whole descriptor with an error rather
than ignore the label.

## Policy bits

| Bit | Value | Meaning |
|---|---|---|
| `SYSTEM_MANDATORY_LABEL_NO_READ_UP` | 0x00000001 | Non-dominant callers receive no read-mapped rights from the DACL. |
| `SYSTEM_MANDATORY_LABEL_NO_WRITE_UP` | 0x00000002 | Non-dominant callers receive no write-mapped rights from the DACL. |
| `SYSTEM_MANDATORY_LABEL_NO_EXECUTE_UP` | 0x00000004 | Non-dominant callers receive no execute-mapped rights from the DACL. |

Unknown bits in a label mask are ignored.

## The algorithm

```
EnforceMIC(ace, token, mapping, &decided):

    if not (token.mandatory_policy & NO_WRITE_UP):
        return

    token_dominates = (token.integrity_level >= ace.integrity_level)

    if token_dominates:
        return

    // Non-dominant: start with read + execute, strip per label policy.
    allowed = MapGenericBits(GENERIC_READ, mapping)
            | MapGenericBits(GENERIC_EXECUTE, mapping)

    if ace.mask & SYSTEM_MANDATORY_LABEL_NO_READ_UP:
        allowed &= ~MapGenericBits(GENERIC_READ, mapping)
    if ace.mask & SYSTEM_MANDATORY_LABEL_NO_WRITE_UP:
        allowed &= ~MapGenericBits(GENERIC_WRITE, mapping)
    if ace.mask & SYSTEM_MANDATORY_LABEL_NO_EXECUTE_UP:
        allowed &= ~MapGenericBits(GENERIC_EXECUTE, mapping)

    // READ_CONTROL and SYNCHRONIZE are always allowed regardless of the
    // object type's GenericMapping and the label's up-strip policy — a
    // non-dominant caller can always read the descriptor and synchronize
    // on the object. Applied after the strips because a file GENERIC_READ
    // mapping folds these bits in, so NO_READ_UP would otherwise take them.
    allowed |= READ_CONTROL | SYNCHRONIZE

    // SeRelabelPrivilege: let WRITE_OWNER through MIC.
    if token.privilege_enabled(SeRelabelPrivilege):
        allowed |= WRITE_OWNER

    all_bits = MapGenericBits(GENERIC_ALL, mapping)
    decided |= all_bits & ~allowed
```
