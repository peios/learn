---
title: Privileges in the pipeline
type: concept
description: Several privileges modify what the access check decides. This page covers where each AccessCheck-influencing privilege fires in the pipeline, what bits it grants, what it does not bypass, and how its grant is recorded for audit.
related:
  - peios/access-decisions/overview
  - peios/access-decisions/mandatory-integrity-control
  - peios/access-decisions/narrowing-layers
  - peios/privileges/overview
  - peios/privileges/intent-gated
---

Five privileges in the catalog change what AccessCheck decides. Each one fires at a specific step of the pipeline. Each one grants a specific set of bits. Each one is bypassed by some layers and not by others. Understanding which is which is what lets you reason about access decisions that involve privileges — when a privilege rescued an access, when it could have but did not, when it would have been irrelevant.

This page covers each of the five AccessCheck-influencing privileges in pipeline order: where it fires, what it grants, what bypasses it, and how it shows up in audit.

The intent model itself — why `BACKUP_INTENT` and `RESTORE_INTENT` exist as separate gates — is on [Intent-gated privileges](~peios/privileges/intent-gated). This page assumes that material.

## The five privileges, at a glance

| Privilege | Fires at step | Grants | Intent-gated? |
|---|---|---|---|
| `SeSecurityPrivilege` | 4 | `ACCESS_SYSTEM_SECURITY` | No |
| `SeBackupPrivilege` | 4 | Read-category rights | Yes (`BACKUP_INTENT`) |
| `SeRestorePrivilege` | 4 | Write-category rights, `WRITE_OWNER`, `WRITE_DAC`, `DELETE`, `ACCESS_SYSTEM_SECURITY` | Yes (`RESTORE_INTENT`) |
| `SeTakeOwnershipPrivilege` | 9 | `WRITE_OWNER` | No |
| `SeRelabelPrivilege` | (not AccessCheck — `kacs_set_sd`) | Setting an integrity label above the caller's own | No |

Steps 4 and 9 are both privilege-grant steps in the access check pipeline (see [Access decisions overview](~peios/access-decisions/overview)). The difference is when in the pipeline they run. Step 4 is pre-DACL — privileges that fire there decide bits before the DACL walk happens. Step 9 is post-DACL — `SeTakeOwnershipPrivilege` fires only if the DACL did not already grant `WRITE_OWNER`.

`SeRelabelPrivilege` does not fire inside AccessCheck at all. It is consulted by `kacs_set_sd` when the caller is trying to change an object's integrity label above their own. It is listed here because, like the others, it modifies what would otherwise be a denial decision.

## SeSecurityPrivilege — SACL access

`ACCESS_SYSTEM_SECURITY` (bit 0x01000000) gates reading and writing the SACL. The DACL **never** grants this right — there is no ACE you can write to allow non-privileged users SACL access. The only grant of `ACCESS_SYSTEM_SECURITY` comes from a privilege.

`SeSecurityPrivilege`, when enabled on the calling token, grants `ACCESS_SYSTEM_SECURITY` at step 4 of the pipeline if it appears in the desired mask. The grant is unconditional in the sense that no DACL or MIC bit can deny it. PIP can: a non-dominant PIP caller will lose this bit along with the other privilege-granted bits.

In addition to its access-check role, `SeSecurityPrivilege` is also a kernel-standalone privilege that gates several Linux capability checks (CAP_AUDIT_CONTROL, CAP_MAC_ADMIN, CAP_AUDIT_READ). The same privilege wears two hats.

`SeRestorePrivilege` also grants `ACCESS_SYSTEM_SECURITY` in its specific use cases (restoring an SD via `kacs_set_sd`). The two privileges are not equivalent: a holder of SeSecurity can read or write any SACL freely; a holder of SeRestore can do it as part of a restore operation but the rest of the access-check pipeline treats them differently.

In audit, an `ACCESS_SYSTEM_SECURITY` grant attributable to `SeSecurityPrivilege` is recorded as such. A consumer parsing audit events can distinguish "SACL was modified because the DACL granted it" (cannot happen) from "SACL was modified because the caller held the privilege" (always the cause).

## SeBackupPrivilege — read-category, intent-gated

`SeBackupPrivilege` is the read-bypass privilege. With `BACKUP_INTENT` set in `privilege_intent` and the privilege enabled on the token, AccessCheck at step 4 grants the **read-category bits** of the desired mask regardless of the DACL.

The "read category" is determined by the object's GenericMapping. For a file: `FILE_READ_DATA | FILE_READ_ATTRIBUTES | FILE_READ_EA | READ_CONTROL`. For a registry key: the corresponding read rights on a key. For a token: `TOKEN_QUERY | READ_CONTROL`.

The grant is pre-decided in step 4. By the time the DACL walk runs in step 8, the read-category bits are already decided as granted, and the walk only processes the remaining (write, execute, ownership) bits. If the DACL would have granted some read bits anyway, the privilege grant is redundant; if the DACL would have granted none, the privilege grant is the source.

The intent flag is what activates the privilege. Without `BACKUP_INTENT`, step 4's SeBackup processing is skipped; the privilege has no effect on this call. The intent must come from the caller — there is no kernel default. See [Intent-gated privileges](~peios/privileges/intent-gated).

## SeRestorePrivilege — write-category, intent-gated

`SeRestorePrivilege` is the write-bypass privilege. With `RESTORE_INTENT` set and the privilege enabled, AccessCheck at step 4 grants the **write-category bits** plus several adjacent rights:

- Write-category bits (`FILE_WRITE_DATA | FILE_APPEND_DATA | FILE_WRITE_ATTRIBUTES | FILE_WRITE_EA` for files; corresponding bits for other types).
- `DELETE`.
- `WRITE_OWNER` and `WRITE_DAC`.
- `ACCESS_SYSTEM_SECURITY` (so a restore can rewrite the SACL).

That last bit is the reason a restore tool does not also need to hold SeSecurityPrivilege — SeRestore folds the SACL-write authority into the restore-flavoured grant.

Beyond the access-check grant, SeRestore has one more effect: it bypasses the "new owner must be self or `SE_GROUP_OWNER` group" restriction in `kacs_set_sd`. A holder of SeRestore can set an object's owner to any well-formed SID, not just their own. This is what lets a restore reconstitute an object's original owner even when the original principal is not present on the running system.

Like SeBackup, the privilege is intent-gated. Without `RESTORE_INTENT`, it is skipped at step 4 and has no effect.

## SeTakeOwnershipPrivilege — WRITE_OWNER, post-DACL

`SeTakeOwnershipPrivilege` is special because of when it fires: step 9, after the DACL walk. The reasoning: the DACL might already grant `WRITE_OWNER` to the caller, in which case the privilege is unnecessary. The pipeline runs the walk first, then checks: did the walk grant `WRITE_OWNER`? If yes, nothing to do. If no, and the caller holds SeTakeOwnership, grant it now.

This timing means SeTakeOwnership produces a different audit signature than the step-4 privileges. The "this right was granted by SeTakeOwnership" event fires only when the DACL would not have granted `WRITE_OWNER` anyway. If you see SeTakeOwnership in an audit log, you know the caller actually needed the privilege for that access; if the DACL had been sufficient, the privilege would not have shown up.

SeTakeOwnership does not bypass MIC. A Medium-integrity caller cannot take ownership of a High-integrity object even with the privilege, because MIC will have pre-decided `WRITE_OWNER` as denied at step 5 (before SeTakeOwnership runs at step 9). The privilege only fires on bits not already decided.

It also does not bypass PIP — same reasoning, PIP fires before step 9 and can pre-decide `WRITE_OWNER` as denied for non-dominant PIP callers.

The "new owner must be self or `SE_GROUP_OWNER` group" rule applies to taking ownership via this privilege. The privilege grants the *right to write the owner field*, not freedom from validation. To set the owner to an arbitrary SID, the caller additionally needs SeRestore.

## SeRelabelPrivilege — raising the integrity label

`SeRelabelPrivilege` is the integrity-label privilege. It does two things:

- During `kacs_set_sd` with `LABEL_SECURITY_INFORMATION` (or `SACL_SECURITY_INFORMATION`), it allows the caller to set the integrity label to a level **above their own**. Without the privilege, an object's label can be lowered (to at or below the caller's level) but not raised.
- It bypasses the standard MIC check on `WRITE_OWNER` when the caller is operating on an object with a higher integrity label — specifically, the privilege "punches `WRITE_OWNER` through MIC" for non-dominant callers, so a relabelling tool can adjust ownership as part of a relabel even if the object is currently at a higher integrity than the tool.

`SeRelabelPrivilege` is one of the rarest privileges. It is held only by tools that legitimately need to set system-level integrity labels — typically TCB labelling utilities. Almost no general-purpose code holds it.

## What privileges do not bypass

A handful of layers ignore the privilege-grant step entirely.

**Confinement.** Confinement pass (step 11) intersects the running grant with what the confinement SID set would grant. Privilege-granted bits are **not** preserved through this intersection. A confined token with SeBackup enabled can still be confined out of read access; the privilege is gone.

This is the major difference between confinement and the restricted-token pass. Restricted-token intersection (step 10) preserves privilege-granted bits — they are restored after the intersection. Confinement does not. The reason: confinement is policy applied to the code from outside, and a confined application should not be able to escape its sandbox by exercising a privilege. See [Confinement](~peios/confinement/overview).

**CAAP.** Central access policies, evaluated at step 12, can narrow what privileges have already granted. A CAAP rule whose DACL does not grant the right will strip it from the running grant. Privilege-granted bits are not immune.

**PIP.** Non-dominant PIP callers have their privilege-granted bits stripped in step 5 (PIP processing). This is unique to PIP — MIC is content to leave privilege-granted bits alone, but PIP actively revokes them. The reason is the same as the confinement reason: PIP is about isolating untrusted binaries from trusted ones, and a privilege that bypassed PIP would defeat the model.

A useful mnemonic: privileges survive restricted-token narrowing; they do not survive confinement, CAAP, or PIP. The first is the privilege-friendly narrowing layer; the others are privilege-blind.

## Privilege-use audit

Step 13 of the pipeline is the privilege-use audit emission. For each privilege that contributed bits in steps 4 or 9, the kernel checks the token's `audit_policy` and emits an audit event accordingly.

The events fall into two flavours:

- **Successful privilege use.** The privilege contributed bits *and* those bits survived to the final granted mask. Emitted when `PRIVILEGE_USE_SUCCESS` (0x04) is set in `audit_policy`.
- **Failed privilege use.** The privilege contributed bits *but* they did not survive — stripped by some later layer (confinement, CAAP, PIP). Emitted when `PRIVILEGE_USE_FAILURE` (0x08) is set.

The failed-use case is what tells you "a privilege was exercised but was unable to actually grant access". This is auditable separately from a plain "access denied" — the privilege got far enough to fire and then got stripped.

The events themselves are documented in [Auditing](~peios/auditing/overview).

## Reading a granted mask back

A practical concern: when an access check returns a granted mask that includes a right, how do you know whether the right came from the DACL or from a privilege?

You cannot tell from the granted mask alone. The bit is the same regardless of source. The way to tell is the audit log: privilege-use audit events identify which privilege contributed which bits. If you see in the audit log that SeBackup granted `FILE_READ_DATA` on a specific access, you know the DACL did not.

In code, the way to verify is to issue the access check twice: once with the privilege intent flag (or with the privilege enabled), and once without. The difference in granted mask is what the privilege contributed.

For most code paths, this introspection is unnecessary — the granted mask is whatever it is, and the caller acts on it. But for auditing, debugging, or testing pipelines that exercise privileged paths, the distinction matters.

## What goes in audit

The privilege-use audit event for each fire records:

- The name of the privilege (e.g. `SeBackupPrivilege`).
- The bits the privilege contributed pre-narrowing.
- The bits that survived to the final granted mask.
- Whether the use was successful (bits survived) or failed (bits were stripped).

This is enough for an audit consumer to reconstruct what happened. A success event with non-empty surviving bits shows what the privilege ended up granting; a failure event with empty surviving bits shows what the privilege tried to grant and lost. Together they tell the story of where the access landed.
