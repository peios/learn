---
title: Ownership and implicit rights
type: concept
description: Every security descriptor names an owner. The owner has implicit READ_CONTROL and WRITE_DAC rights regardless of what the DACL says — the "you cannot lock yourself out" guarantee. This page covers the implicit rights, how OWNER RIGHTS suppresses them, and the rules for changing ownership.
related:
  - peios/security-descriptors/overview
  - peios/security-descriptors/dacl-evaluation
  - peios/identity/well-known-principals
  - peios/privileges/overview
---

Every security descriptor names an owner — a single SID identifying the principal responsible for the object's access policy. The owner has authority over the object's DACL: they can change it, including granting or revoking access for themselves and others.

That authority is implemented by two implicit rights granted *outside* the DACL walk: `READ_CONTROL` (read the SD) and `WRITE_DAC` (modify the DACL). The owner gets these regardless of what the DACL says. An owner cannot accidentally write a DACL that locks themselves out of their own object — the implicit rights are the floor.

This is the "you cannot lock yourself out" guarantee. It is also why every SD must have an owner: an object with no owner has no fallback authority, and the access check rejects an SD without one.

## The implicit rights

When the access check starts evaluating a DACL, it first checks whether the caller's token represents the SD's owner. If it does, the caller is granted `READ_CONTROL` and `WRITE_DAC` before the DACL walk begins. Both bits go into the `granted` mask and into `decided`, so no later ACE — allow or deny — can change them.

"Represents the owner" means the caller's `user_sid` matches the SD's owner SID **or** the caller's token has the owner SID as a group with the `SE_GROUP_OWNER` flag set. The flag is on the group, not on the token globally; only groups specifically marked as eligible to act as owner count. This lets a token represent multiple potential owners (the user themselves, plus the administrative group they belong to that owns shared objects).

The implicit grant is just `READ_CONTROL` and `WRITE_DAC`. Nothing else. The owner of a file does not automatically get `FILE_READ_DATA` or `FILE_WRITE_DATA` — those rights come from the DACL like any other. An owner who has not written themselves into their own DACL can read and modify the policy but cannot read or write the data without first adding an allow ACE.

This split is what makes the model work. The owner controls *policy*; the DACL controls *data access*. An owner can lose all data-access rights to their own object (perhaps because every ACE was a deny against them) and still recover, because `WRITE_DAC` is implicit and lets them rewrite the DACL.

## OWNER RIGHTS: suppressing the implicit grant

Sometimes you want an object where the owner is *not* allowed to be a backdoor. A sensitive log file owned by a service should not let the service rewrite its own audit policy. A configuration object owned by a user should not let that user override administrator-set restrictions.

The mechanism is the well-known SID **`S-1-3-4`** — `OWNER RIGHTS`. When any ACE in the DACL names `OWNER RIGHTS`, the kernel suppresses the implicit grant of `READ_CONTROL | WRITE_DAC`. The owner gets whatever the ACE says they get, no more.

The rule is more precise than that. Suppression happens when:

- An ACE in the DACL names `S-1-3-4` as its SID, and
- The ACE has `INHERIT_ONLY_ACE` clear (it is a real, evaluated ACE, not an inherit-only placeholder).

If any such ACE is present, the owner's implicit rights are suppressed *regardless of what the ACE grants*. An OWNER RIGHTS allow ACE granting only `FILE_READ_DATA` means the owner can read but not write the DACL — they have lost `WRITE_DAC` entirely.

During the DACL walk, the OWNER RIGHTS SID matches the caller if they are the owner. So an `ACCESS_ALLOWED` ACE on `S-1-3-4` grants those rights to whoever happens to own the object. The ACE composes with the rest of the DACL like any other ACE; first-writer-wins still applies.

The two pieces — suppress implicit, then evaluate normally — let you write DACLs that say:

- "The owner gets exactly read and read-attributes, nothing else, including not WRITE_DAC."
- "The owner has the same rights as any other authenticated user; no special privileges."
- "The owner has no access at all; only specific named principals can touch this object."

These constructions are not always wise. Locking the owner out of `WRITE_DAC` means no one short of an administrator with `SeTakeOwnership` can change the DACL. That can be exactly what you want, but it is also how an object becomes administratively unrecoverable. Use sparingly.

## Changing ownership

Ownership is itself a property the access check protects. To change an SD's owner, the caller must hold `WRITE_OWNER` on the object. By default, that right is in the standard rights section of the access mask (bit 19, value `0x00080000`), and a DACL can grant it like any other right.

Once a caller has `WRITE_OWNER`, they cannot just name any SID as the new owner. The kernel applies one of two rules, depending on the caller's privileges.

**Without `SeRestorePrivilege`**, the new owner SID MUST be either:

- The caller's own `user_sid`, or
- A SID present in the caller's `groups` list with the `SE_GROUP_OWNER` flag set.

This restriction is what stops a user with `WRITE_OWNER` from "transferring" an object to someone else and washing their hands of it. You can take ownership yourself (assuming you have `WRITE_OWNER` or `SeTakeOwnershipPrivilege`), but you cannot hand the object to an arbitrary third party.

**With `SeRestorePrivilege`**, the restriction is bypassed. The new owner can be any well-formed SID. This is what backup and restore tools use to restore an object whose original owner is not present on the current system.

The kernel's `kacs_set_sd` enforces both rules at the time of the change — there is no "set owner to anyone, validate later" path.

## SeTakeOwnership: an unconditional grant

`SeTakeOwnershipPrivilege` is a privilege that grants `WRITE_OWNER` on any object, regardless of the DACL. A caller holding the privilege can take ownership of anything they can reach — a file whose DACL grants them nothing, a registry key with no allow ACE for them at all.

The privilege does **not** bypass:

- The "new owner must be self or a SE_GROUP_OWNER group" rule. The caller still has to name themselves (or one of their owner-eligible groups) as the new owner. To name a different principal as the new owner, the caller additionally needs `SeRestorePrivilege`.
- MIC. A lower-integrity caller cannot take ownership of a higher-integrity object even with the privilege.
- PIP. A non-dominant caller cannot take ownership of an object protected by a higher PIP trust label even with the privilege.

`SeTakeOwnership` is the lever that makes administrative recovery possible. An object whose DACL has accidentally locked everyone out can still be reached by an administrator with the privilege, who can take ownership, then use the implicit `WRITE_DAC` to rewrite the DACL. Without the privilege, such an object would be permanently inaccessible.

The privilege is granted very narrowly — typically only to BUILTIN\Administrators and the SYSTEM account. Most service accounts and ordinary users do not have it.

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

A few patterns for when ownership is the lever you need:

- **Lost access to your own file.** You wrote a DACL that denies you. You are still the owner; implicit `WRITE_DAC` lets you rewrite the DACL and add back what you need.
- **Inherited a mess of objects from a departed user.** Their tokens are gone, but their SIDs are still in the DACLs. An administrator with `SeTakeOwnership` can take ownership of each object (subject to the same-self-or-owner-group rule for the new owner) and then rewrite the DACLs.
- **Restoring backups.** A backup tool with `SeRestorePrivilege` can set arbitrary owners during restore, reproducing the original SDs even when the original principals are not present on the current system.
- **Locking the owner out deliberately.** Use an `OWNER RIGHTS` ACE — explicitly grant the owner what you want them to have (perhaps nothing) and the implicit grant of `READ_CONTROL | WRITE_DAC` will be suppressed. Use with care; this is what makes objects administratively unrecoverable except via `SeTakeOwnership`.
