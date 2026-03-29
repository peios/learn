---
title: Application Confinement
order: 6
---

Confinement inverts the normal access model. A confined token starts from nothing. Access is denied by default, regardless of what the DACL grants to the token's user SID or group SIDs. The only way a confined process can access an object is if the object's DACL explicitly grants access to the token's confinement SID, one of its declared capability SIDs, or the well-known ALL_APPLICATION_PACKAGES SID.

## How confinement works

A confined token carries:

- **confinement_sid** — the token's confinement identity. When set, the token is confined.
- **confinement_capabilities** — capability SIDs the application has declared.
- **confinement_exempt** — escape hatch. When set, confinement restrictions are not evaluated.

AccessCheck evaluates confinement as a final mask over the granted rights. The normal evaluation (DACL walk, privileges, integrity, restricted tokens) runs first. The confinement check then independently evaluates the same DACL, matching only against the confinement SID and capability SIDs. The final result is the intersection.

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
- **PRINCIPAL_SELF is isolated from user identity** in the confinement pass. S-1-5-10 is injected only if `self_sid` matches a confinement SID (the package SID or a capability).
- **Conditional expressions see the full token.** The confinement pass isolates identity for SID matching, but conditional expressions inside ACEs evaluate against the user's real groups and claims.

## Confinement ordering

Confinement runs AFTER the restricted token merge and its privilege restoration. This ordering is critical: privileges bypass the restricted pass but MUST NOT bypass confinement. If confinement ran before the restricted merge, the privilege restoration would resurrect bits that confinement already blocked.
