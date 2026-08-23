---
title: The Privilege Model
description: Rights that do not fit the subject-object model — the privilege lifecycle, the two enforcement categories, intent gating, assignment and auditing.
---

Some operations do not fit the subject-object model at all. Rebooting
the machine, loading a kernel module, changing the system clock,
creating a token — these affect the system itself rather than a
specific protected resource, so there is nothing to attach a security
descriptor to. They still need authorization.

Privileges fill that gap. A privilege is the right to perform a
particular system operation, carried on the token beside the
principal's identity. Where a descriptor says "this principal may read
this file", a privilege says "this principal may shut down the
system". The descriptor lives on the object; the privilege lives on
the subject.

## Lifecycle

A privilege is **assigned by policy** when authd creates the token,
resolving the principal's assignments from security policy once, at
creation. There are no runtime grants: a privilege absent at creation
can never be added later.

The privilege then sits on the token in whatever enabled state it was
created with. The kernel accepts any enabled set that is a subset of
the present set, and takes the creation-time enabled set as the
enabled-by-default set. authd issues every privilege it grants already
enabled, on the reasoning that a privilege the holder had to enable
before it worked would be a grant in name only — so the
present-but-disabled resting state exists in the model and is
reachable through AdjustPrivileges, but is not where privileges
normally start.

A privilege that has been disabled is re-activated by **explicitly
enabling** it through AdjustPrivileges.

When the privilege is **exercised**, the kernel checks that it is both
present and enabled — a single mask test against both words — permits
the operation, and records it as used.

For a standalone gate, "exercised" means the gate accepted that bit,
and the used bit is meant to be recorded even when a later independent
check — a process descriptor, PIP, or a malformed-input test — denies
the operation afterwards. Where the shared privilege helper performs
the check, it marks the bit immediately, and the impersonation gate
does the same. Three gates mark later and therefore record nothing
when a subsequent check fails: token creation marks after the token
has been constructed and its descriptor allocated, so a malformed
specification leaves the bit unset; primary token installation marks
after the same-user and same-LogonSession gate; and the `CAP_SYS_BOOT`
mapping marks after the remote-shutdown origin gate.

Used-state for the AccessCheck-influencing privileges follows the
provenance rules of §3.8 instead.

Recording the used bit is not merely bookkeeping. Every gate treats a
failure to record it as a failure of the operation itself and returns
`EPERM` or `EACCES`.

Afterwards the privilege may be **disabled**, returning to rest, or
**removed permanently**, which clears it from the present, enabled,
and enabled-by-default states while preserving the `used` bit for
audit.

## Two enforcement categories

**Standalone operation gates** are the majority. They authorize
specific operations that AccessCheck does not mediate — rebooting,
loading modules, debugging processes — and the kernel simply checks
whether the calling thread's token holds the privilege present and
enabled before allowing the operation.

**AccessCheck-influencing privileges** alter the outcome of
AccessCheck itself, causing it to grant rights the object's DACL would
not grant on its own. They are evaluated inside the pipeline alongside
DACL rules, integrity policy, and confinement. There are five:
`SeSecurityPrivilege` grants `ACCESS_SYSTEM_SECURITY` for SACL access
(and doubles as a standalone gate for the audit-related Linux
capabilities); `SeTakeOwnershipPrivilege` grants `WRITE_OWNER` as a
post-DACL fallback; `SeBackupPrivilege` grants all read access;
`SeRestorePrivilege` grants all write access plus `WRITE_DAC`,
`WRITE_OWNER`, `DELETE` and `ACCESS_SYSTEM_SECURITY`; and
`SeRelabelPrivilege` loosens MIC's constraint on `WRITE_OWNER` for
non-dominant callers. §3.8 gives the exact mechanics.

## Intent gating

`SeBackupPrivilege` and `SeRestorePrivilege` are intent-gated. Other
AccessCheck-influencing privileges are self-scoping —
`SeSecurityPrivilege` only matters when `ACCESS_SYSTEM_SECURITY` is
requested — but backup and restore grant such broad categories of
access that evaluating them unconditionally would apply them to every
AccessCheck on the system.

AccessCheck therefore takes a `privilege_intent` parameter. A caller
passes `BACKUP_INTENT` for a backup-context operation and
`RESTORE_INTENT` for a restore-context one, and the corresponding
privilege is evaluated only when its flag is present. Without the
flag, these privileges are invisible to the pipeline.

Intent gating also keeps backup and restore *inside* the pipeline
rather than short-circuiting it, which matters because later stages —
PIP in particular — have to be able to constrain privilege-granted
access.

## Assignment

Privileges are assigned by security policy, not by identity.
Membership of the Administrators group confers no privilege by itself.
Groups and privileges are orthogonal: groups determine which objects
you can reach through DACLs, privileges determine which system
operations you can perform.

An administrator defines policy — that members of Backup Operators
receive `SeBackupPrivilege` and `SeRestorePrivilege`, say. At
authentication authd resolves the principal's group memberships,
evaluates the policy against them, and creates the token carrying the
result. The kernel neither verifies nor evaluates that policy; it
trusts authd as a TCB component. The token then carries those
privileges for its whole lifetime.

## Auditing

Every exercise sets the token's monotonic used state for that
privilege, and every standalone gate emits an ftrace event.

KMES audit events are emitted only for the five AccessCheck-influencing
privileges, and only when the token's `audit_policy` opts in through
`PRIVILEGE_USE_SUCCESS` or `PRIVILEGE_USE_FAILURE`. The event fires
when the privilege's provenance bits intersect both the mapped desired
mask and the final granted mask. For `SeSecurityPrivilege` and
`SeTakeOwnershipPrivilege` that intersection is genuinely
counterfactual — `ACCESS_SYSTEM_SECURITY` is pre-decided by the
privilege, and take-ownership contributes only when `WRITE_OWNER` was
not already granted — so an event means the privilege was load-bearing.
Backup and restore seed their bits unconditionally, without asking
whether the DACL would have granted the same access, so their events
also fire for accesses the DACL alone would have permitted.

A `MAXIMUM_ALLOWED` request short-circuits this accounting entirely,
recording no used bits and emitting no privilege-use events for any
privilege.
