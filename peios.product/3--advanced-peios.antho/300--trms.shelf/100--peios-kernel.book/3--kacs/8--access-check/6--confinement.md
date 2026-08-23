---
title: Application Confinement
description: An absolute boundary a confined token cannot cross whatever the DACL says — normal and strict confinement, and where it sits in the order.
---

Confinement restricts a token's effective access to what is explicitly
granted to its confinement identity. Even where the normal DACL walk
grants access through the user SID or a group SID, the confinement
pass intersects that with what the confinement SIDs would receive on
their own, and revokes anything they cannot independently justify.

A confined token carries `confinement_sid`, its confinement identity;
`confinement_capabilities`, the capability SIDs the application
declares; and `confinement_exempt`, an escape hatch that skips
confinement evaluation entirely.

The confinement SID set is `confinement_sid` together with every SID
in `confinement_capabilities`. Capabilities are **presence-based**
identities rather than ordinary ACE-matching groups: a capability SID
participates whenever it is present, and disabling an entry or marking
it deny-only does not remove it from the confinement identity.

The pass also injects two confinement-scoped virtual groups.
`S-1-5-10` (`PRINCIPAL_SELF`) is injected only when `self_sid` equals
the confinement SID or one of the capability SIDs, and `S-1-3-4`
(`OWNER RIGHTS`) only when the object's owner SID does. Both apply to
ACE SID matching during the confinement walk *and* to the conditional
membership operators — `Member_of`, `Member_of_Any`, and their device
and negated variants — evaluated during that pass.

## An absolute boundary

Confinement is not overridable. Privileges do not bypass it: the
confinement merge takes no privilege-granted input at all, so backup,
restore, `SeTakeOwnershipPrivilege` and `SeSecurityPrivilege` are
alike unable to grant access the confinement check denies. Owner
implicit rights are skipped entirely, because the pass runs with
`skip_owner_implicit` set.

One thing does pass through: an object with a **null DACL** grants in
the confinement pass exactly as it does in the normal pass. A null
DACL means "no discretionary restrictions", and the confinement pass
follows standard evaluation, granting all valid bits.

## Strict confinement

A normal confined token carries both `ALL_APPLICATION_PACKAGES` and
`ALL_RESTRICTED_APPLICATION_PACKAGES` among its capabilities. Omitting
`ALL_APPLICATION_PACKAGES` gives strict confinement: far fewer system
objects grant to `ALL_RESTRICTED_APPLICATION_PACKAGES`, so the access
surface is much narrower.

Strict confinement is not a separate kernel mode bit. It is derived
purely from the SID set supplied at token creation — if
`ALL_APPLICATION_PACKAGES` is absent, AccessCheck simply evaluates the
remaining confinement SIDs. The kernel never synthesises it, and never
rejects an otherwise valid confined token for carrying it. Deciding
which capabilities a package token receives belongs to authd and
policy tooling.

## Consequences worth stating

**SACL access is unreachable.** `ACCESS_SYSTEM_SECURITY` is only ever
privilege-granted, and privileges do not bypass confinement, so a
confined token cannot reach a SACL unless a confinement ACE grants the
right outright.

**`OWNER RIGHTS` is confinement-scoped.** `S-1-3-4` matches in the
confinement pass only when the owner SID is part of the confinement
SID set.

**`PRINCIPAL_SELF` is isolated from user identity.** `S-1-5-10` is
injected only when `self_sid` matches a confinement SID — the package
SID or one of its capabilities — not when it matches the user.

**Conditional expressions still see the full token.** The confinement
pass isolates ordinary SID matching to the confinement identity, but
conditional expressions inside ACEs continue to evaluate against the
user's real groups and claims. The two confinement-scoped virtual
groups are the only exception, and they follow the confinement rules
during conditional membership evaluation.

## Ordering

Confinement runs **after** the restricted token merge and after its
privilege restoration. The order is load-bearing: privileges bypass
the restricted pass but must not bypass confinement, and if
confinement ran first the privilege restoration would resurrect bits
that confinement had already blocked.
