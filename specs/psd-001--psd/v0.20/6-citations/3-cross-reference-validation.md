---
title: Cross-Reference Validation
---

## Validation on version bump

When a new version of any PSD is published, all cross-references within the updated specification and all cross-references from other specifications that resolve to the updated specification SHOULD be validated.

## Validation steps

Cross-reference validation consists of:

1. Parse all `PSD-NNN §x.y.z(n)` references in the updated specifications.
2. Resolve the target version via the version resolution rule (§3.3).
3. Verify the section path exists in the target's document structure.
4. Verify the clause number exists by counting normative statements at the target location.
5. Optionally verify semantic consistency -- does the referenced content still match what the referencing text implies?

Steps 1 through 4 are mechanically automatable. Step 5 requires human or AI review.

> [!INFORMATIVE]
> Trail can implement steps 1-4 as a build-time check. Step 5 is an editorial concern -- a reference to "the AccessCheck algorithm in PSD-004 §10.1(1)" may still resolve to a valid clause, but if that clause was rewritten to describe a different algorithm, the reference is semantically stale even though it is structurally valid.

## Unresolvable references

A reference that cannot be resolved (PSD number does not exist, section path does not exist in the resolved version, clause number exceeds the count of normative statements) SHOULD be treated as an error.

A specification MUST NOT be finalised with unresolvable cross-references.
