---
title: Ownership and implicit rights
type: concept
description: Understand the owner's limited implicit rights, OWNER RIGHTS suppression, and why changing ownership alone does not guarantee recovery.
related:
  - peios/security-descriptors/overview
  - peios/security-descriptors/dacl-evaluation
  - peios/identity/well-known-principals
  - peios/privileges/overview
  - peios/file-access/managing-file-security
---

Every security descriptor names an owner, a SID associated with the object's access policy. An owner normally receives `READ_CONTROL` to read the descriptor and `WRITE_DAC` to change its DACL. Ownership does **not** automatically grant access to file contents, and it is **not** a guarantee against locking yourself out.

Before relying on ownership to repair access, inspect the DACL for `OWNER RIGHTS` ACEs and check the other access layers. For a shell workflow, use [Managing file security](~peios/file-access/managing-file-security); this page explains when ownership helps and when it does not.

## The implicit rights

At the start of the normal DACL walk, an owner can receive `READ_CONTROL` and `WRITE_DAC`. Those bits are marked granted and decided, so a later DACL ACE cannot reverse them. The grant is limited to valid rights that an earlier policy stage has not already decided; a mandatory denial is not overridden by ownership.

The [descriptor specification](~peios/advanced-peios/pcds/security-descriptor/ownership) determines ownership by equality with the caller's user SID or token group SIDs. This ownership relation is distinct from the `SE_GROUP_OWNER` requirement for assigning a group as a **new** owner. Allow and deny ACE matching also has its own enabled/deny-only group rules.

The implicit grant covers only descriptor reading and DACL editing. It does not include `FILE_READ_DATA`, `FILE_WRITE_DATA`, `WRITE_OWNER` or `ACCESS_SYSTEM_SECURITY`. In particular, being the owner does not confer SACL access or permission to transfer ownership.

An owner may be able to repair a DACL that excludes them from data access, but only if `WRITE_DAC` remains available. The [Kernel TRM](~peios/advanced-peios/peios-kernel/kacs/access-check/dacl-walk#owner-implicit-rights) documents two important limits:

- A qualifying `OWNER RIGHTS` ACE suppresses the implicit grant.
- The grant cannot override rights already decided by mandatory policy. Confinement also performs its secondary walk without an owner-implicit bypass.

## OWNER RIGHTS: suppressing the implicit grant

`S-1-3-4`, **OWNER RIGHTS**, lets a policy control the owner's rights through ordinary DACL rules rather than an automatic grant. This can be useful when a service that owns a file should not also be free to rewrite its access policy.

Suppression happens if the DACL contains a **non-inherit-only access-control ACE** targeting `S-1-3-4`. The pre-scan tests the ACE's presence, not whether its condition evaluates true. Even a conditional OWNER RIGHTS ACE whose condition later fails suppresses implicit `READ_CONTROL | WRITE_DAC`.

The owner then receives whatever access the full DACL walk and remaining policy allow, including matching user, group and OWNER RIGHTS ACEs. It is not limited to the OWNER RIGHTS ACE alone. An OWNER RIGHTS allow ACE granting only read-data therefore removes the *implicit* `WRITE_DAC`, but another applicable ACE could still grant `WRITE_DAC`.

OWNER RIGHTS ACEs obey the same first-writer-wins order and allow/deny matching rules as other access-control ACEs. An inherit-only OWNER RIGHTS ACE does not suppress implicit rights on the object it is attached to.

> [!WARNING]
> Changing the owner alone preserves the DACL. If it contains an OWNER RIGHTS ACE that suppresses `WRITE_DAC`, that suppression applies to the new owner too. Taking ownership is therefore not a reliable way around it. Keep a separately verified, authorized repair path before restricting owner policy access.

## Changing ownership

Changing an owner requires `WRITE_OWNER` (standard-right bit 19, `0x00080000`) on the object. The DACL can grant it, or an applicable privilege can contribute it through the access-check pipeline. Passing that gate and being allowed to name the new owner are separate requirements.

**Without `SeRestorePrivilege`**, the new owner must be either:

- The caller's own user SID, or
- A group SID on the caller's token carrying `SE_GROUP_OWNER`.

`SeTakeOwnershipPrivilege` does not relax this new-owner restriction. **With `SeRestorePrivilege`**, the SID constraint is bypassed and any well-formed SID can be assigned; the operation still needs the applicable set-security access path and checks. The kernel validates the change before applying it.

For example, the documented shell form for making the current caller the owner of one file is:

```sh
sd owner ./report.txt @self
```

Use it only when that is the intended ownership policy and the required authority is established. It leaves the DACL in place and does not itself restore file-data or DACL-edit access. Inspect and verify as described in [Managing file security](~peios/file-access/managing-file-security).

## SeTakeOwnership and recovery limits

The kernel access-check contract lets `SeTakeOwnershipPrivilege` supply `WRITE_OWNER` after the DACL walk when the DACL did not grant it and mandatory policy did not block it. This is a DACL override for one right, not an unconditional grant of access to the object.

It does **not** bypass:

- The new-owner SID rule. Use of an arbitrary SID instead requires `SeRestorePrivilege`.
- MIC or PIP restrictions. A caller that does not dominate the object's required integrity or trust does not gain an override merely by holding take-ownership.
- Other narrowing layers, including confinement.
- OWNER RIGHTS suppression after the owner changes. The unchanged DACL can still withhold `WRITE_DAC`.

> [!IMPORTANT]
> Confirm privilege availability on the deployed build before planning recovery. Older privilege prose says take-ownership and relabel are absent from the published ABI, but the current [generated ABI](~peios/advanced-peios/peios-kernel/kacs/kacs-abi) defines their constants. A constant alone does not establish which names `authd` or a service's privilege configuration accepts, or what the caller's token actually holds. [Assigning privileges](~peios/privileges/assigning-privileges#what-this-cannot-express-yet) explains that unresolved distinction; do not assume either universal availability or universal unavailability.

`SeRestorePrivilege` is also not a generic promise that an arbitrary file handle can repair a descriptor. The [set-security contract](~peios/advanced-peios/peios-kernel/kacs/facs/set-security#the-serestoreprivilege-bypass) distinguishes live checks through a path or `O_PATH` handle from cached rights on an ordinary fd. Verify the supported repair mechanism rather than improvising one from privilege names.

## The primary group

The SD's primary group field is a relic. It exists because the SD format reserves a slot for it and because some legacy code paths consult it, but in Peios its role is almost entirely passive.

The one place the primary group matters is **inheritance**. When the kernel synthesises a new child SD and an inheritable ACE names `CREATOR_GROUP` (the well-known SID `S-1-3-1`), the substitution uses the new child's primary group SID. The primary group is set to the creator's token's primary group at the time of creation.

After inheritance has run, the primary group on the child SD is just a stored value. The access check does not consult it. ACEs do not match it. It exists so the `CREATOR_GROUP` substitution has a target.

You will rarely need to think about the primary group. The few times it matters are:

- Programs that read SDs and expect to display the primary group alongside the owner.
- Legacy POSIX-style applications that map the primary group to a Linux GID for compatibility purposes.
- Inheritable ACEs that use `CREATOR_GROUP` to grant access to "the group of whoever created this".

Most of the time, the primary group is set to whatever the creating token had and is then ignored.


## Recovery patterns

| Situation | What to establish before changing policy |
|---|---|
| You own the file but cannot read its data | Whether you still have `READ_CONTROL` and `WRITE_DAC`; inspect OWNER RIGHTS, the DACL and mandatory policy before adding the intended data access. |
| Files still name a departed user's SID | Which authorized principal already has policy-edit rights. An ownership change alone does not remove stale ACEs or establish repair authority. |
| A restore must reproduce original owners | Use an established restore workflow with the required `SeRestorePrivilege`, live-check access path and descriptor checks; arbitrary owner SIDs are not available to ordinary owner changes. |
| Policy intentionally limits the owner | Preserve and verify a separate authorized repair route. Neither take-ownership nor a saved SDDL record guarantees rollback. |

If no authorized repair route is established, stop and resolve that with the system's policy administrator or documented recovery process. Do not try broad grants, label lowering or raw xattr writes as a substitute for diagnosis.

## Where to go next

- [Managing file security](~peios/file-access/managing-file-security) — inspect, choose a bounded change and verify it.
- [The sd command](~peios/files-and-directories/sd) — exact shell syntax.
- [Inheritance](~peios/security-descriptors/inheritance) — creator placeholders and child descriptors.
- [Privileges](~peios/privileges/overview) — how privilege-held rights differ from ownership.
