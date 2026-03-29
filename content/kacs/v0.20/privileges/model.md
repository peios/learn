---
title: Privilege Model
order: 1
---

Some operations do not fit the subject-object model. Rebooting the system, loading a kernel module, changing the system clock, creating a new token -- these are system-wide operations that affect the machine itself, not a specific protected resource. They need authorization, but there is no object to attach an SD to.

Privileges fill this gap. A privilege is a right to perform a specific system operation, carried on the token alongside the principal's identity. Where an SD says "this principal may read this file," a privilege says "this principal may shut down the system." The SD is on the object; the privilege is on the subject.

## Lifecycle

A privilege has a simple lifecycle on a token:

1. **Assigned by policy.** When authd creates a token, it resolves the principal's privilege assignments from security policy. The assignment is resolved once, at token creation time. There MUST NOT be runtime privilege grants -- if a privilege is not on the token at creation, it MUST NOT be added later.

2. **Present but disabled.** Most privileges start disabled. They exist on the token but are not active.

3. **Explicitly enabled.** Before using a privilege, the holder enables it via AdjustPrivileges. This is a deliberate act.

4. **Exercised.** The privilege is checked by the kernel and, if enabled, the operation is permitted. The privilege is recorded as used and an audit event MAY be emitted.

5. **Disabled or removed.** After the operation, the privilege MAY be disabled (returning to the resting state) or permanently removed (irreversible).

## Two categories

Privileges divide into two categories based on where they are enforced:

**Standalone operation gates.** The majority of privileges. These authorize specific system operations not mediated by AccessCheck -- rebooting, loading kernel modules, debugging processes. The kernel checks whether the calling thread's token holds the required privilege (present and enabled) before permitting the operation.

**AccessCheck-influencing privileges.** A small number of privileges alter the outcome of AccessCheck itself -- they can cause AccessCheck to grant access rights that the object's DACL would not independently grant. These are evaluated inside the pipeline alongside DACL rules, integrity policy, and confinement. Five privileges influence AccessCheck:

- **SeSecurityPrivilege** — grants ACCESS_SYSTEM_SECURITY (SACL read/write).
- **SeTakeOwnershipPrivilege** — grants WRITE_OWNER as a post-DACL fallback.
- **SeBackupPrivilege** — grants all read access (intent-gated).
- **SeRestorePrivilege** — grants all write access plus WRITE_DAC, WRITE_OWNER, DELETE, and ACCESS_SYSTEM_SECURITY (intent-gated).
- **SeRelabelPrivilege** — loosens MIC's constraint on WRITE_OWNER for non-dominant callers.

The precise mechanics of how these interact with the AccessCheck pipeline are specified in the AccessCheck section.

## Intent-gated privileges

SeBackupPrivilege and SeRestorePrivilege are **intent-gated**. Unlike other privileges which are self-scoping (SeSecurityPrivilege only matters when ACCESS_SYSTEM_SECURITY is requested), backup and restore grant broad categories of access that would apply to every AccessCheck call if evaluated unconditionally.

AccessCheck takes a `privilege_intent` parameter. The caller passes BACKUP_INTENT when performing a backup-context operation and RESTORE_INTENT when performing a restore-context operation. Backup and restore privileges MUST only be evaluated when the corresponding flag is present. Without the flag, these privileges are invisible to the pipeline.

Intent-gating also ensures backup and restore are evaluated *inside* the AccessCheck pipeline rather than short-circuiting it. This is necessary because later stages -- specifically PIP -- MUST be able to constrain privilege-granted access.

## Assignment

Privileges are assigned by security policy, not by identity. Being a member of the Administrators group does not automatically confer any privilege. Privileges and group memberships are orthogonal: groups determine what objects you can access (via DACLs), privileges determine what system operations you can perform.

The assignment flow:

1. An administrator defines privilege policy: "members of the Backup Operators group receive SeBackupPrivilege and SeRestorePrivilege."
2. When a principal authenticates, authd resolves group memberships and evaluates privilege policy against those memberships.
3. authd creates the token with those privileges via CreateToken. The kernel MUST NOT verify or evaluate the policy -- it trusts authd as a TCB component.
4. The token carries those privileges for its lifetime. No privilege MAY be added after creation.

## Auditing

Every privilege exercise SHOULD be tracked. When a privilege is exercised, the token's used state for that privilege is set (monotonic). For AccessCheck-influencing privileges, audit events are emitted when the privilege was actually necessary for the access decision -- not merely when the privilege is present, but when the access would have been denied without it.
