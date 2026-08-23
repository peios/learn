---
title: The Model
description: A role is a virtual name several packages contend to own, with at most one holding it — the pieces, and why the links belong to peipkg.
---

A **role** is a virtual name several installed packages may contend to
own on the filesystem, with at most one *holding* it. The holder's file
answers the contended path through a symlink peipkg owns.

Two registry daemons can be installed at once; only one of them is
`/usr/bin/registryd`.

The declarations are specified in PSPU §5.23. What follows is what
peipkg does with them.

## The pieces

A role has one or more **slots**, each materialising one filesystem
name. A slot's **claim paths** are where the links appear; a **target**
is the holder's file each link points at.

The claim-path set for a slot is the union of every installed consumer's
declared path for it, plus the holder's own provider-declared default
path if it has one. The materialised links are the cross-product of that
set with the holder's targets.

## Links are relative

A claim link's body is a **relative** path, computed from the link's
location to the target: a link at `/usr/bin/registryd` pointing at
`/usr/sbin/loregd` is written as `../sbin/loregd`.

Only the database keeps the absolute logical target. Anything reading
the link itself — an auditor, an unrelated tool — sees the relative
form.

The reason is relocatability. A root assembled by the composer, or
installed under an alternate root, or packed into an initramfs archive,
is moved around before it is ever booted. An absolute link body would
point outside it.

## Links belong to peipkg

A claim link is owned by the package manager, not by any package. It
never appears in a package's payload and is never recorded as a
package-owned path.

That is what lets two eligible providers coexist: neither ships the
contended path, so the one-package-per-path rule is never engaged by the
providers themselves.
