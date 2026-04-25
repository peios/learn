---
title: Application Confinement
---

Confinement restricts a token's effective access to only what is explicitly granted to its confinement identity. Even if the normal DACL walk grants access via the user SID or group SIDs, the confinement pass intersects those grants with what the confinement SIDs would independently receive. Access that the confinement SIDs cannot independently justify is revoked. The only exception is objects with a NULL DACL (no discretionary restrictions), which grant access in the confinement pass as they do in the normal pass.

## How confinement works

A confined token carries:

- **confinement_sid** — the token's confinement identity. When set, the token is confined.
- **confinement_capabilities** — capability SIDs the application has declared.
- **confinement_exempt** — escape hatch. When set, confinement restrictions are not evaluated.

AccessCheck evaluates confinement as a final mask over the granted rights. The normal evaluation (DACL walk, privileges, integrity, restricted tokens) runs first. The confinement check then independently evaluates the same DACL, matching only against the confinement SID and capability SIDs. The final result is the intersection.

The confinement SID set is:

- `confinement_sid`
- every SID in `confinement_capabilities`

`confinement_capabilities` are presence-based capability identities, not ordinary ACE-matching groups. A capability SID participates in the confinement SID set whenever it is present in `confinement_capabilities`, regardless of `SE_GROUP_ENABLED` or `SE_GROUP_USE_FOR_DENY_ONLY`.

The confinement pass also injects confinement-scoped virtual groups:

- `S-1-5-10` (PRINCIPAL_SELF) is injected only if `self_sid` equals `confinement_sid` or one of the confinement capability SIDs.
- `S-1-3-4` (OWNER RIGHTS) is injected only if the object's owner SID equals `confinement_sid` or one of the confinement capability SIDs.

These confinement-scoped virtual groups apply to both:

- ACE SID matching during the confinement DACL walk
- conditional membership operators (`Member_of`, `Member_of_Any`, and the device/non-device negated variants) evaluated during the confinement pass

The generic allow/deny group-attribute rules do not apply to capability membership inside the confinement SID set. Disabling a capability entry or marking it deny-only does not remove it from the confinement identity.

This is an absolute boundary:

- Privileges MUST NOT bypass confinement.
- Owner implicit rights MUST NOT apply in the confinement evaluation.
- Backup, restore, SeTakeOwnershipPrivilege, SeSecurityPrivilege -- none can grant access that the confinement check denies.

## Strict confinement

A normal confined token carries both ALL_APPLICATION_PACKAGES and ALL_RESTRICTED_APPLICATION_PACKAGES in its capabilities. For additional security, ALL_APPLICATION_PACKAGES MAY be omitted. This is strict confinement -- far fewer system objects grant to ALL_RESTRICTED_APPLICATION_PACKAGES, resulting in a much narrower access surface.

A strictly confined token MUST NOT carry ALL_APPLICATION_PACKAGES in its confinement_capabilities.

## Known consequences

- **SACL access is unreachable.** ACCESS_SYSTEM_SECURITY is privilege-controlled, and privileges do not bypass confinement.
- **Owner implicit rights are skipped** in the confinement evaluation.
- **NULL DACL grants access.** An object with no DACL means "no discretionary restrictions." The confinement pass follows standard evaluation -- NULL DACL grants all valid bits.
- **OWNER RIGHTS is confinement-scoped.** S-1-3-4 matches in the confinement pass only when the owner SID is part of the confinement SID set.
- **PRINCIPAL_SELF is isolated from user identity** in the confinement pass. S-1-5-10 is injected only if `self_sid` matches a confinement SID (the package SID or a capability).
- **Conditional expressions see the full token.** The confinement pass isolates ordinary SID matching to the confinement identity, but conditional expressions inside ACEs still evaluate against the user's real groups and claims. The only exception is the confinement-scoped virtual groups above: `S-1-3-4` and `S-1-5-10` follow the confinement identity rules during conditional membership evaluation.

## Confinement ordering

Confinement runs AFTER the restricted token merge and its privilege restoration. This ordering is critical: privileges bypass the restricted pass but MUST NOT bypass confinement. If confinement ran before the restricted merge, the privilege restoration would resurrect bits that confinement already blocked.
