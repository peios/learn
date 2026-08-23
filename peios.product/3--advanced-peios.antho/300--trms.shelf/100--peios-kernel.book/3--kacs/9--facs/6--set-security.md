---
title: The Set-Security Interface
description: The single syscall all descriptor modification flows through — ownership, integrity labels, the SeRestorePrivilege bypass and mandatory attributes.
---

All descriptor modification flows through one syscall. The caller
provides a file descriptor or path, a bitmask naming which components
to modify, and a self-relative descriptor blob carrying the new
values.

| Flag | Component | Required right |
|---|---|---|
| `OWNER_SECURITY_INFORMATION` | Owner SID | `WRITE_OWNER` |
| `GROUP_SECURITY_INFORMATION` | Group SID | `WRITE_OWNER` |
| `DACL_SECURITY_INFORMATION` | Discretionary ACL | `WRITE_DAC` |
| `SACL_SECURITY_INFORMATION` | System ACL | `ACCESS_SYSTEM_SECURITY` |
| `LABEL_SECURITY_INFORMATION` | Mandatory integrity label | `WRITE_OWNER`, plus the integrity constraints below |

The blob is validated structurally — parseable, well-formed ACEs,
valid SIDs, at most 65535 bytes — and then only the indicated
components are merged into the existing descriptor. Unindicated
components are preserved unchanged.

The input is always one self-relative descriptor subset, never a raw
SID or ACL fragment. `SACL_SECURITY_INFORMATION` and
`LABEL_SECURITY_INFORMATION` cannot be combined in one call, because
both target the SACL field with incompatible meanings; the pair fails
with `EINVAL`.

A `SACL_SECURITY_INFORMATION` write replaces the object's **entire**
SACL. A `LABEL_SECURITY_INFORMATION` write interprets the input SACL
as the label subset only: no SACL component removes the explicit
mandatory label and returns the object to the default unlabelled
state; a present SACL contains exactly one non-inherit-only
`SYSTEM_MANDATORY_LABEL_ACE` and nothing else; and the object's
non-label SACL ACEs are preserved.

After merging, the result still has a non-null owner — the group SID
may be null — and a merge that would leave no owner fails.

MIC and PIP apply to these checks. A low-integrity caller cannot
modify a high-integrity file's descriptor even where the DACL grants
`WRITE_OWNER`.

## Ownership

A new owner may be set only to the caller's own SID, or to a group SID
on the token carrying `SE_GROUP_OWNER`. `SeTakeOwnershipPrivilege`
allows setting ownership to the caller's own SID regardless of what
the current descriptor says, and `SeRestorePrivilege` allows any
arbitrary SID.

## Integrity labels

Without `SeRelabelPrivilege` a caller may set a label only at or below
its own integrity level; with it, any level.

The constraint applies through **both** paths — the dedicated label
subset, and a label ACE embedded in a full SACL write. A SACL write
whose ACL contains a mandatory label ACE raising integrity above the
caller's level requires `SeRelabelPrivilege` exactly as the label path
does, even though the SACL component itself is gated only by
`ACCESS_SYSTEM_SECURITY`.

## The SeRestorePrivilege bypass

`SeRestorePrivilege` fires inside the AccessCheck pipeline, so it
bypasses the check only where `kacs_set_sd` runs a **live** one: an
`O_PATH` descriptor with `AT_EMPTY_PATH`, a pidfd, a token descriptor
with `AT_EMPTY_PATH`, or a path. On those paths it grants every
requested right, `WRITE_OWNER`, `WRITE_DAC` and
`ACCESS_SYSTEM_SECURITY` included.

Called on an ordinary file descriptor the required rights are checked
against the cached mask instead, no AccessCheck runs, and the
privilege has no effect at all. A caller needing the bypass has to use
the `O_PATH` route — which is the mechanism behind backup restoration,
administrative repair, and the missing-descriptor repair path
(§3.9.5).

## Mandatory resource attributes

When a caller modifies the SACL, the existing and new SACLs are
compared for changes to `SYSTEM_RESOURCE_ATTRIBUTE_ACE` entries. An
existing attribute carrying `CLAIM_SECURITY_ATTRIBUTE_MANDATORY`
(0x0020) cannot be removed, nor its values modified, without
`SeTcbPrivilege` — and an attempt without it fails the entire call
rather than silently dropping the change.

## Write mechanics

The updated descriptor is serialised to self-relative binary form and
written to the xattr through an internal kernel path bypassing the
denial hook, and the in-memory cache is updated. An audit event is
emitted if the file's SACL carries a matching audit ACE.

The cache update is not atomic with the xattr write; §3.9.5 describes
the lock ordering that forces this and the last-writer-wins window it
produces.
