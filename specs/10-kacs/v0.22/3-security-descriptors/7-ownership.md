---
title: Ownership
---

Every SD has an owner. Ownership confers two implicit rights that AccessCheck grants regardless of what the DACL says:

- **READ_CONTROL** — the owner can always read the object's SD.
- **WRITE_DAC** — the owner can always modify the object's DACL.

These implicit grants are the "you can't lock yourself out" guarantee. Even if the DACL grants the owner nothing, the owner can read and rewrite the DACL to restore access.

Ownership is determined by SID equality against the caller's user SID or token
group SIDs. Deny-only flags affect ACE matching, but they do not change the
ownership relation itself.

## OWNER RIGHTS (S-1-3-4)

The implicit READ_CONTROL and WRITE_DAC grants MAY be suppressed or modified by including an ACE for the OWNER RIGHTS SID (`S-1-3-4`) in the DACL.

When AccessCheck detects any non-inherit-only access-control ACE targeting the OWNER RIGHTS SID in the DACL (via a pre-scan before the DACL walk), the implicit grant is suppressed. The owner's access then comes entirely from the DACL walk -- through ACEs matching their user SID, group SIDs, and any ACEs targeting S-1-3-4.

This enables three patterns:

- **Suppress owner rights** — a deny ACE for S-1-3-4 with READ_CONTROL | WRITE_DAC.
- **Expand owner rights** — an allow ACE for S-1-3-4 with additional rights beyond the default.
- **Restrict owner rights** — an allow ACE for S-1-3-4 with only READ_CONTROL (no WRITE_DAC).

The OWNER RIGHTS pre-scan checks only for the presence of any non-inherit-only access-control ACE targeting the OWNER RIGHTS SID in the DACL, not whether any condition on the ACE evaluates to TRUE. A conditional ACE targeting OWNER RIGHTS suppresses the implicit grant even if the condition later evaluates to FALSE.

During the DACL walk, S-1-3-4 is treated as a normal SID. If the caller is the owner, ACEs targeting S-1-3-4 match the caller. The suppression only removes the automatic implicit grant; it does not isolate the owner from the rest of the DACL.

**SeTakeOwnershipPrivilege interaction.** OWNER_RIGHTS deny ACEs cannot block SeTakeOwnershipPrivilege. If an OWNER_RIGHTS ACE denies WRITE_OWNER, the DACL walk marks WRITE_OWNER as decided-but-not-granted. The post-DACL SeTakeOwnershipPrivilege override (algorithm step 10) fires when WRITE_OWNER is not granted and was not blocked by a mandatory mechanism (MIC or PIP). DACL denials — including OWNER_RIGHTS denials — are not mandatory decisions, so the privilege overrides them. Only MIC no-write-up or PIP non-dominance can prevent SeTakeOwnershipPrivilege from granting WRITE_OWNER.

## Ownership transfer

Changing an object's owner requires WRITE_OWNER on the object. Without SeTakeOwnershipPrivilege, the new owner MUST be the caller's own SID or a group on the caller's token with SE_GROUP_OWNER (defined in the SID format section, flag value 0x00000008). SE_GROUP_ENABLED is NOT required — a deny-only group with SE_GROUP_OWNER can be set as the owner.

SeTakeOwnershipPrivilege grants WRITE_OWNER on any object regardless of the DACL (deny-proof, but subject to MIC/PIP). SeRestorePrivilege bypasses the ownership SID constraint entirely — the `kacs_set_sd` syscall checks for SeRestorePrivilege and, when present, skips the "own SID or SE_GROUP_OWNER group" validation, allowing the caller to set ownership to any arbitrary SID.
