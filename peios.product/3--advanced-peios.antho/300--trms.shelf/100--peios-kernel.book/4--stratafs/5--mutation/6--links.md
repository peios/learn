---
title: Links
description: Hard links within one mount, linking an unnamed file, and how symbolic links are created.
---

## Hard links

To create a hard link from an existing name to a new name within one
mount, letting `P` be the source's provider:

1. `P` must accept modification. Otherwise `EXDEV`.
2. The destination must not be held by any participating stratum.
   Otherwise `EEXIST`.
3. `P` must hold the directory containing the destination. Otherwise
   `EXDEV`. That directory is not created to satisfy the condition,
   whether or not `P` is the create stratum.
4. The link is created in `P`.

`P` need not be the create stratum: a link is made in whichever stratum
provides the source, since that is the only stratum in which the two
names can share an object. Condition 2 ensures the new link is not
shadowed at its destination, since no stratum — above `P` or below it —
holds that name.

Condition 2 is enforced by the VFS rather than by stratafs for a named
source: the link path looks the destination up with `LOOKUP_EXCL`, and
stratafs's merged lookup makes the dentry positive whenever any stratum
holds the name. stratafs's own test covers only the provider stratum
and is a race backstop. For an unnamed source it does check every
stratum explicitly.

A link request is never satisfied by copying the source up. The result
would be a link to the copy rather than to the object named by the
source, so the two names would not share an object — which is the whole
of what a hard link is for. Refusing is the only correct answer.

`EXDEV` is used rather than `EROFS` because it is the error callers
already handle when a link cannot be made between two locations, and
because it is accurate: the link would have to span two strata, which
through this mount are two filesystems.

Where installing the outer inode fails after the lower link succeeded,
the link is rolled back; a failed rollback is audited.

## Linking an unnamed file

An unnamed file created under §4.5.3 is linked into the mount by the
rules for creation, not by those above: it has no provider, so
conditions 1 and 3 have no subject.

The link is created in the create stratum — a source recorded with any
other index is refused with `EXDEV` — and the operation follows §4.5.3:
the name must not be held by any participating stratum, parent
directories are materialised in the create stratum, and a create
stratum that is absent or does not exist fails with `EROFS`.

Linking an unnamed file into a different mount fails with `EXDEV`,
checked both by superblock and by mount, and by the VFS as well.

## Symbolic links

Creating a symbolic link is an ordinary creation and follows §4.5.3:
the link is created in the create stratum, with a security descriptor
established by inheritance there.

A symbolic link's target is stored and returned verbatim. The target
string is passed through untouched on creation, and on read the outer
inode's `get_link` calls the provider inode's own and returns its
result unmodified. No rewriting exists anywhere: a target naming a path
inside a stratum is not rewritten to name the corresponding path inside
the mount, nor the reverse.

Resolution of a symbolic link found in a stratum follows §4.3.1. The
raw string goes back to the VFS, which interprets it as any filesystem's
target is interpreted, so an absolute target resolves from the process's
root and may re-enter this mount, a different stratafs mount, or none.
A link created directly in a stratum by that stratum's owner is
followed as written; the rule constrains only what stratafs itself
does, which is nothing.
