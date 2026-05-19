---
title: Intent-gated privileges
type: concept
description: SeBackupPrivilege and SeRestorePrivilege are exempt from the normal "enabled means in effect" rule. They are evaluated only when the caller passes a specific intent flag — BACKUP_INTENT or RESTORE_INTENT — to AccessCheck. This page covers why intent gating exists and how the flags are passed.
related:
  - peios/privileges/overview
  - peios/privileges/lifecycle
  - peios/access-decisions/overview
---

Most privileges work the same way: if they are enabled on the calling token at the moment of the call, the kernel uses them; if not, it does not. AdjustPrivileges manages enabled state; the access check reads it. There is no other input.

Two privileges are special: **`SeBackupPrivilege`** and **`SeRestorePrivilege`**. Both are present-and-enabled on the tokens of backup-and-restore tools. Both grant access that the DACL alone would not. And both will refuse to do anything unless the calling code passes a specific **intent flag** to AccessCheck — `BACKUP_INTENT` for SeBackup, `RESTORE_INTENT` for SeRestore.

Without the intent flag, the privilege is invisible to the access check. The token has it. The kernel knows it has it. But the privilege does not participate in the access decision. The DACL walk runs as if the privilege were not present.

This page covers why intent gating exists, how the flags are passed, and what each privilege actually does when its intent flag is set.

## Why intent gating exists

The privileges in question grant very broad access. SeBackup grants read on any object regardless of the DACL. SeRestore grants write, ownership change, and SACL access on any object. They are designed for backup-and-restore tools — programs that legitimately need to bypass discretionary access control to do their job.

The problem: if these privileges were always in effect when enabled, every access check on a token holding them would benefit from them. A backup tool that opens a configuration file as part of its initialisation — for entirely ordinary reasons — would silently exercise SeBackup, even though the configuration file's normal DACL would have granted the access anyway. The audit trail would record privilege exercises that were operationally meaningless. Worse, a buggy code path in the tool that did something unintended would silently get backup-level access to the unintended object.

Intent gating solves this by making the privilege opt-in **per call**. The tool's main backup loop sets `BACKUP_INTENT` on every AccessCheck call it makes; everything else does not. The privilege fires only where the tool deliberately asked for it. Audit events for privilege exercise are accurate (they only appear where the tool intentionally invoked the privilege), and bugs in non-backup code paths cannot accidentally exercise SeBackup.

The split is between "enabled" (the token can use the privilege) and "intent" (the caller wants to use the privilege right now). Both must be true.

## The intent flags

The flags are passed to AccessCheck as part of the `privilege_intent` parameter. They are independent bits:

| Flag | Effect |
|---|---|
| `BACKUP_INTENT` (0x01) | Tells AccessCheck that the caller wants `SeBackupPrivilege` to participate, if present and enabled. |
| `RESTORE_INTENT` (0x02) | Tells AccessCheck that the caller wants `SeRestorePrivilege` to participate. |

A caller can set both, one, or neither. The flags are not exclusive — a backup-and-restore tool might do a restore-with-verification operation that wants both privileges to fire.

Without either flag, the corresponding privilege is stripped from the access check's view of the token *for this call*. It is not removed from the token; the token still has it; the next call from the same code can set the flag and use it. The strip happens only for the current AccessCheck.

The flags are at the AccessCheck API surface. Lower-level open and access paths (the file system's open, the registry's read) translate higher-level semantics into AccessCheck calls; whether they pass the flags depends on whether they were told to. Most do not; an opener of a file in the ordinary course of work does not pass BACKUP_INTENT.

## What SeBackupPrivilege does

With `BACKUP_INTENT` set and SeBackup enabled, AccessCheck grants the caller read-category rights on the object regardless of the DACL:

- For files: `FILE_READ_DATA`, `FILE_READ_ATTRIBUTES`, `FILE_READ_EA`, and `READ_CONTROL`.
- For registry keys: the read-category rights on the key (the specific values depend on the registry's GenericMapping).
- For tokens: `TOKEN_QUERY` and `READ_CONTROL`.

The grant happens **after** the DACL walk has run. Specifically, the walk produces a `granted` mask for whatever the DACL alone would grant; the privilege then adds the read-category bits to that mask without consulting the DACL. If the DACL already granted some of them, the privilege grant is redundant; if the DACL granted nothing, the privilege adds them.

The grant is recorded in the access check's audit state. An audit event for this call records "the read rights came from SeBackupPrivilege", distinguishing privilege-granted access from DACL-granted access. Audit consumers that care about privilege use can filter by this marker.

SeBackup does **not** grant write access. A backup tool that needs to write its output also reads but cannot use SeBackup for that — write is SeRestore's territory.

## What SeRestorePrivilege does

With `RESTORE_INTENT` set and SeRestore enabled, AccessCheck grants the caller write-category rights and metadata-modification rights regardless of the DACL:

- Write rights (`FILE_WRITE_DATA`, `FILE_APPEND_DATA`, `FILE_WRITE_ATTRIBUTES`, `FILE_WRITE_EA` for files; corresponding rights on other object types).
- `DELETE`.
- `WRITE_OWNER` and `WRITE_DAC`.
- `ACCESS_SYSTEM_SECURITY` (SACL read/write).

Plus, separately, SeRestore bypasses the "new owner must be self or SE_GROUP_OWNER group" restriction during `kacs_set_sd`. A restore tool can set the owner of a restored object to any well-formed SID, not just the caller's own. This is what lets a backup restore reconstitute an object's original owner even when the original principal is not present on the running system.

Like SeBackup, the grant is recorded in audit state — write rights granted by SeRestore are distinguished from those granted by the DACL.

The reason SeRestore also grants `ACCESS_SYSTEM_SECURITY` (which would normally require SeSecurityPrivilege) is the same: a restore operation needs to set the SACL as part of reconstituting the object's policy. Forcing the tool to also hold SeSecurity would be redundant; SeRestore folds that authority in.

## What the flags do *not* do

Two clarifications:

- **The flags do not grant privileges.** A token that does not have SeBackup gets nothing from setting BACKUP_INTENT. The flag tells the kernel "use this privilege if I have it"; it cannot conjure a privilege the token lacks.
- **The flags do not enable disabled privileges.** A token that has SeBackup present but disabled gets nothing from BACKUP_INTENT, just as it would get nothing without the flag. The privilege must be enabled for AccessCheck to consider using it. Intent is on top of enabled, not in place of it.

The state machine is: **token has the privilege** AND **token has the privilege enabled** AND **caller has set the intent flag** = AccessCheck uses the privilege. Any one of the three missing means it does not.

## Why only these two privileges

The intent-gating model exists specifically for privileges that grant broad, blanket access. SeBackup grants read on everything; SeRestore grants write on everything. The risk of accidental exercise is high enough to be worth a per-call gate.

Other privileges that influence the access check — `SeSecurityPrivilege` (SACL access), `SeTakeOwnershipPrivilege` (WRITE_OWNER), `SeRelabelPrivilege` (raising integrity) — are not intent-gated. They are scoped enough that the "just check if enabled" model is appropriate. SeSecurity only fires when accessing the SACL, which is not done by accident; SeTakeOwnership only fires when changing the owner, ditto; SeRelabel only fires when changing the integrity label, ditto.

The split is between "this privilege only fires when you do something specific anyway" (no intent needed) and "this privilege would fire on every access if we let it" (intent required). SeBackup and SeRestore are the only two privileges in the second class.

## Calling pattern

A typical backup tool's loop:

1. Token at startup has `SeBackupPrivilege` present and enabled. (Granted by authd's privilege policy to backup-role principals.)
2. For each object to back up:
   - Call AccessCheck with `BACKUP_INTENT` set in `privilege_intent`. The kernel grants the read-category rights via SeBackup if the DACL would not.
   - Read the object.
3. Other operations the tool does (reading its own configuration, writing log output, opening its output file) call AccessCheck without `BACKUP_INTENT`. These run through the DACL like any other access. The privilege is not exercised.

A typical restore tool's loop is the mirror:

1. Token at startup has `SeRestorePrivilege` present and enabled.
2. For each object to restore:
   - Call AccessCheck with `RESTORE_INTENT` set. The kernel grants write-category rights via SeRestore.
   - Write the object's contents.
   - Set its SD via `kacs_set_sd`, including owner. The "any well-formed SID can be the owner" rule is in effect because RESTORE_INTENT was set on the AccessCheck that produced the WRITE_OWNER grant.
3. Other operations run normally without the flag.

The pattern is symmetric. Both privileges work the same way; both follow the same intent rule.

## What about privileges in audit events

Audit events for privilege exercise carry enough information to distinguish:

- The privilege that was exercised.
- The bits it contributed to the final granted mask.
- Whether those bits survived to the final access decision (i.e., were not stripped by some later layer like restricted-token intersection or confinement).

A backup tool with `BACKUP_INTENT` set on every AccessCheck call produces clean audit events: one privilege-use event per backup-flavoured access, none for incidental accesses. This is the audit trail intent gating was designed to produce. Without the flag, the privilege would fire on every access from the same token, and the audit would be unable to distinguish "I exercised SeBackup because I'm a backup" from "I exercised SeBackup because the file would have been readable to me anyway".

The full audit model lives in [Auditing](~peios/auditing/overview).
