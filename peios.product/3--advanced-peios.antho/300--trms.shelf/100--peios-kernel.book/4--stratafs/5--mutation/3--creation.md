---
title: Creation
description: Creating a name no stratum holds — where it lands, its security descriptor, deleting dispositions, and exclusive against non-exclusive creation.
---

Creating a name held by no participating stratum places it in the
create stratum. [*create.lands-in-create-stratum]

1. If there is no create stratum, or it is absent, the operation fails
   with `EROFS`. [*create.erofs-without-create-stratum]
2. Any directories of the create stratum containing the name's path
   that do not exist are materialised as §4.5.2 requires for copy-up
   parents. Where the create stratum holds one of those components as
   something other than a directory, the operation fails with
   `ENOTDIR`; the blocking entry is not removed or replaced. [*create.parent-conflict-enotdir]
3. The name is created there.

All six kinds of creation — regular file, directory, symbolic link,
device node, FIFO, socket — go through one helper and one path.

The `ENOTDIR` case arises because creation routes positionally, into
the create stratum's subdirectory at the same path whether or not it
exists (§4.3.2). Where the create stratum holds that path as a file,
and a higher-precedence stratum provides it as a directory, the merged
directory exists and is reachable while its create-stratum counterpart
is blocked.

## The security descriptor [*create.descriptor-inherited-from-parent]

A created object has no provider to inherit from, so its descriptor is
established by the ordinary creation semantics of the create stratum's
filesystem — by inheritance from the directory it is created in,
exactly as if it had been created there directly. The create is an
ordinary `vfs_create`, `vfs_mkdir`, `vfs_symlink` or `vfs_mknod`
against the real create-stratum parent, with the KACS creation decision
bound to that same parent.

This is cleanly separated from copy-up inside KACS: the copy-up branch
of the inode security initialisation is taken first and short-circuits
the inheritance builder entirely. Ordinary creation in a create stratum
inherits; copy-up preserves.

Where the creating interface lets the caller supply a descriptor — the
native open path does — it is honoured rather than replaced by an
inherited one. That is entirely KACS's doing; stratafs has no
descriptor parameter and cannot express it. All stratafs contributes is
re-anchoring the pending native create request onto the create-stratum
parent.

## Dispositions that delete [*create.supersede-is-removal-then-creation]

A creating interface may offer a disposition that replaces an existing
object rather than opening it. In Peios that is the supersede
disposition of the native open path: KACS creates a temporary file
through the mount, opens it, and renames it onto the target, at which
point stratafs diverts the rename into a dedicated supersede path.

Such a disposition is a removal followed by a creation, and both halves
apply. Before anything is created, the removal is validated: the
target's provider must accept modification, or the operation fails with
`EROFS`. Before anything is removed, the replacement is checked for
reachability: if any stratum strictly above the create stratum, other
than the provider being removed, holds the name, the operation fails
with `EROFS`.

Without that guard the disposition could report success while leaving
the caller's new object invisible. The removal takes the name out of
the stratum that provided it; the creation puts the replacement in the
create stratum; and if some stratum between the two also holds the
name, it now outranks the replacement.

The creation half is treated as a creation throughout. It is never
reclassified as a modification of a newly-surfaced provider and never
copies one up: the caller asked for a new object, and its descriptor is
derived as above.

Three restrictions are implementation choices rather than consequences
of the model. Supersede applies to regular files only, and anything
else is refused with `EOPNOTSUPP`. The source must be in the create
stratum, and source and destination must share a parent. And the two
halves are **not** atomic: the lower entry is unlinked first and the
staged file renamed into place afterwards, so a failure in between
leaves the name having lost its old provider. The caller receives the
error; the window itself is recorded only in the audit trail.

## Deferred deletion [*create.deferred-delete-targets-resolved-object]

A request to delete an object when the last descriptor to it is closed
applies to the object the descriptor resolved to, not to whatever
provides that name at close time. Because removal (§4.5.4) is defined
over the current provider of a name, the deferred case has its own
path.

When the deletion is attempted, stratafs locates the entry at the path
the descriptor was opened against, in the stratum that provided it at
that time — the descriptor's private dentry carries both — and resolves
the parent in that same stratum. Four conditions end the attempt
quietly, reporting success because the deletion is already complete:
the parent is gone, the name is gone, the name now identifies a
different inode, or the unlink raced.

That stratum must accept modification, or the deletion fails with
`EROFS`. Then the entry is removed, and no other. In particular, where
another caller's copy-up has published a new object at that name in a
higher stratum, that object is not the one being deleted and is left
alone.

Because the attempt has no caller to report to, any failure is audited
— and for a deferred deletion, *every* non-zero result is audited, not
only the arrangement errors §4.6.5 covers for ordinary refusals. The
object is left in place.

One part of the model is not implemented as specified. The right to
delete an entry is checked when the delete-on-close request is armed,
against the requesting token, which is correct. But it is checked
against the **merged** parent directory rather than against the
directory of the stratum where the entry actually lives, and no check
is made at deletion time. The specification requires the check to name
that stratum's directory specifically. This is tracked as a defect.

Deferred deletion is restricted to non-directories, and at arm time to
regular files on a managed mount.

## Exclusive creation [*create.exclusive-eexist-from-any-stratum]

Where creation is requested exclusively, the name must not exist in
**any** participating stratum, and a name provided by a lower stratum
causes `EEXIST` even though the create stratum does not hold it.

Nothing in stratafs implements this, and nothing needs to. The merged
lookup instantiates a positive dentry whenever any stratum holds the
name, and the VFS refuses `O_EXCL` on a dentry it did not create. The
`excl` argument stratafs receives is ignored. There is a race backstop
in the create path — a positive dentry appearing in the create stratum
yields `EEXIST` — but it sees only that one stratum.

Exclusive creation asks whether the name is free, and through this
mount it is not: a caller that created it anyway would find their
object shadowing a file they did not know was there, or masking a whole
subtree.

## Non-exclusive creation over a shadowed name [*create.shadowed-non-exclusive-is-open]

Where creation is not exclusive and a lower stratum provides the name,
the merged dentry is positive, so the VFS never calls the create path
at all. The operation is an open, and §4.5.1 routes it.

Where the provider is a regular file that does not accept modification
and the create stratum has higher precedence, the result is a copy-up
followed by the requested modification, including truncation where
`O_TRUNC` was requested. `O_TRUNC` is stripped from the backing open on
a non-in-place route precisely so that the copy-up source is not
destroyed before it is read.

Where the provider is a FIFO, socket, or device node, no copy-up occurs
and the open is forwarded to the provider. Such an open succeeds
whether or not the provider accepts modification: opening a special
file does not modify it.

## Unnamed files [*create.unnamed-file-in-create-stratum]

A file may be created without a name, for later linking into place. In
a merged directory this is supported, and the file is created on the
create stratum's filesystem, recorded with the create stratum's index
and marked unnamed.

Where the mount has no create stratum, or it is absent, the operation
fails with `EROFS`. Parent materialisation applies as for a named
creation: the create stratum's counterpart of the directory the
operation named is materialised, and the new file's descriptor is
derived by inheritance from it, because that directory is what the
descriptor must come from. Linking such a file into the mount is
governed by §4.5.6.
