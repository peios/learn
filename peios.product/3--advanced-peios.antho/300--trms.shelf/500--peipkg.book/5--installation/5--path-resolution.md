---
title: Path Resolution
description: How an install path is resolved against a pinned directory descriptor, why no symbolic link is ever traversed, and what the pin closes.
---

An install path is resolved **component by component, against a
directory descriptor**, never as a string handed to the kernel to walk.
Each component is opened relative to the descriptor of its parent, and a
component that is not a real directory — a symbolic link above all —
ends the resolution with an error.

The descriptor of the destination's parent is then held from the moment
the operation is planned until the commit that acts on it. Staging,
displacement and installation are all performed against that one
descriptor.

## No symbolic link is ever traversed

This holds for a link peipkg created moments earlier in the same
transaction as much as for one that was already there. A well-formed
package never has a payload entry whose ancestor is a symbolic link, so
the refusal fires only on a malformed or hostile package, where aborting
is what you want.

Symbolic links as **leaf** payload entries are ordinary and are created
normally. What is forbidden is walking *through* one.

Two things follow, and only one of them is about a race.

**A symbolic-link ancestor cannot redirect a write.** The format's rules
permit a package to ship a link whose target resolves into a permitted
destination, and permit a *different* package to ship a file whose path
descends through that link's location — each entry validates in
isolation, and both are individually valid. Resolving the second
package's path now stops at the link instead of following it. Without
that, the file landed where the link pointed, the database recorded the
archive's path, and the collision constraint of §5.3 compared the wrong
name and never fired.

**The check and the commit act on the same directory.** The window
between them is the whole transaction — a pre-existing entry is detected
while the intent is journalled, and the rename that acts on it runs
after every package has been downloaded, decompressed and staged. The
pinned descriptor is what makes that window harmless: the commit renames
within the directory it examined, not within whatever the path string
resolves to by then.

## The final component

Exclusive-create semantics still apply to a staged file, so it cannot
land on an existing name. A pre-existing entry at a destination is
detected without following it and is displaced by a rename, which does
not follow a link at either end — so a link sitting at an install path
is renamed aside rather than written through.

## Recovery

Recovery has only the journal's strings; there is no descriptor to carry
across a crash. It re-resolves them with the same refusing walk, so an
undo lands on the paths the journal named and nowhere else. There is no
in-flight window to race at that point, only a resolution to get right.

## Implementation

The walk is one `openat` per component with `O_PATH|O_NOFOLLOW|
O_DIRECTORY`, and the commit is `renameat` against the pinned
descriptor. `O_PATH|O_NOFOLLOW` alone would open the link itself;
`O_DIRECTORY` is what turns that into the `ENOTDIR` the refusal rests
on.

`openat2` with `RESOLVE_NO_SYMLINKS` would fold the walk into a single
syscall and add `RESOLVE_BENEATH`, `RESOLVE_NO_XDEV` and
`RESOLVE_NO_MAGICLINKS`. It is worth having and is not needed for the
guarantee: a walk that never follows a link and never accepts a `..`
component cannot leave the root by name.

Descriptors are cached per directory, so the count a transaction holds
is the number of distinct directories it writes into, not the number of
files.

> [!NOTE]
> The format's symlink-target rules are the first layer of the defence
> PSPU §5.26 describes, and component-wise resolution against a pinned
> parent descriptor is the second. Both are in place.
