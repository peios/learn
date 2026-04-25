---
title: The DACL Walk
---

The DACL is an ordered list of ACEs. AccessCheck walks the list from first entry to last, comparing each ACE's SID against the calling token's identity.

The fundamental principle is **first-writer-wins**: once a bit in the access mask has been resolved -- granted or denied -- no later ACE can change the outcome for that bit.

## Allow ACEs

When an allow ACE's SID matches the token and the ACE carries rights that have not yet been decided, those rights are granted. Already-decided bits are unaffected.

## Deny ACEs

When a deny ACE's SID matches the token and the ACE carries rights that have not yet been decided, those rights are denied (decided but not granted). Already-decided bits are unaffected.

## SID matching

An ACE's SID matches the token if it equals the token's user SID or a group SID on the token, subject to group attribute filtering:

- **Allow ACEs**: only groups that are enabled (SE_GROUP_ENABLED) and not deny-only match.
- **Deny ACEs**: both enabled groups and deny-only groups (SE_GROUP_USE_FOR_DENY_ONLY) match. A deny-only group always participates in deny matching regardless of its enabled state.
- A group with neither ENABLED nor USE_FOR_DENY_ONLY set does not participate in any matching.

The user SID follows the same deny-only rules: when `user_deny_only` is true, the user SID matches deny ACEs but not allow ACEs.

## Inherit-only ACEs

ACEs with the INHERIT_ONLY flag exist solely to propagate to child objects. The DACL walk MUST skip them.

## ACE mask mapping

At the top of the walk, each ACE's access mask is mapped through MapGenericBits using the same GenericMapping applied to the caller's request. The mapping uses a local copy -- the ACE itself MUST NOT be mutated.

## NULL DACL

If the SD has no DACL (SE_DACL_PRESENT not set), all valid rights that have not already been decided by earlier pipeline stages are granted AND marked as decided. The valid rights are bounded to `MapGenericBits(GENERIC_ALL, mapping)`, not raw 0xFFFFFFFF. Marking these bits as decided ensures the restricted pass and confinement pass see a full grant from the NULL DACL during their intersections.

## Empty DACL

If the DACL is present but contains zero ACEs, no rights are granted by the walk. The only access an owner receives comes from the owner implicit rights mechanism.

## Short-circuit

When all bits in the caller's desired mask have been decided, the walk MAY stop early. This optimization MUST NOT apply in MAXIMUM_ALLOWED mode, where the walk MUST run to completion.

## Owner implicit rights

By default, the owner of an object receives READ_CONTROL and WRITE_DAC regardless of what the DACL says. These implicit rights are granted **before** the DACL walk begins, as the first action inside `EvaluateDACL`. Because first-writer-wins governs the walk, a deny ACE encountered during the walk cannot override owner implicit rights.

The `EvaluateDACL` function accepts a `skip_owner_implicit` parameter. When true (used by the confinement pass), the implicit grant is skipped entirely — confinement is an absolute intersection with no owner bypass.

If any non-inherit-only access-control ACE in the DACL targets the OWNER RIGHTS SID (`S-1-3-4`), the implicit grant is suppressed entirely. This is a pre-scan of the DACL performed at the start of `EvaluateDACL`, before the main walk loop. The pre-scan checks for the ACE's SID presence only — it does not evaluate conditional expressions on the ACE.

During the main walk, S-1-3-4 is treated as a normal SID matching the owner (both allow and deny polarity).

## MAXIMUM_ALLOWED

When the caller includes MAXIMUM_ALLOWED (bit 25) in the desired mask, AccessCheck runs the full evaluation pipeline and returns the complete set of rights that would be granted. MAXIMUM_ALLOWED is stripped from the desired mask before evaluation begins.

Effects:

- The DACL walk runs to completion (no short-circuit).
- The returned mask is whatever the pipeline accumulated, not filtered to requested bits.

MAXIMUM_ALLOWED MAY be combined with specific rights: `MAXIMUM_ALLOWED | READ_CONTROL` asks both "can I read the SD?" (success/fail) and "what else could I get?" (granted mask).

A pure MAXIMUM_ALLOWED request with no specific bits always succeeds.

> [!INFORMATIVE]
> KACS uses first-writer-wins for both targeted and MAXIMUM_ALLOWED requests. This is an intentional divergence that eliminates disagreements between "what can I do?" and "can I do this?" on non-canonically ordered DACLs.
