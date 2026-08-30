---
title: Lookup
description: Resolving one name in one directory — the provider, ancestors, independence from the caller, and staging entries.
---

Resolution is defined for one name in one directory. Every path
operation is a sequence of such resolutions, each independent of the
last.

## The provider

To resolve a name in a stratafs directory, the corresponding directory
of each stratum is examined in precedence order, and the first stratum
holding an entry of that name is its **provider**. [*resolution.provider-is-highest-stratum] If no stratum holds
it, the resolution produces a negative dentry and the VFS reports
`ENOENT`. [*resolution.absent-name-enoent]

Mechanically, each stratum's path string is joined with the relative
path of the name and walked in full, once per stratum. A walk that
succeeds sets that stratum's bit in a presence bitmap; a walk that
fails with `ENOENT` or `ENOTDIR` leaves it clear and the stratum is
skipped. Selecting the provider is then the trailing-zero count of the
bitmap, computed in `stratafs-core`.

Any other error from a stratum's walk — `EACCES`, `EIO`, `ELOOP`,
`ENAMETOOLONG`, `ESTALE` — is not treated as absence. It fails the
whole resolution, so a stratum that is unreadable for a reason other
than not being there masks the name entirely rather than being passed
over. [*resolution.stratum-error-fails-lookup]

A joined stratum path, or a child relative path, that would exceed
`PATH_MAX` fails with `ENAMETOOLONG`. [*resolution.path-max-enametoolong]

## Ancestors

Resolution does not consult a parent's provider to find a child's. A
name's provider is chosen afresh across all strata, so if `/a` is
provided by stratum 2, `/a/b` may still be provided by stratum 1 —
provided stratum 1 also holds `/a` as a directory and the two therefore
merge (§4.3.2). [*resolution.provider-chosen-per-component]

What resolution does consult is whether any ancestor of the path is
masked. Before resolving the final component, every proper prefix of
the relative path is resolved across all strata and its merged provider
computed; a prefix whose provider is not a directory aborts the whole
resolution with `ENOTDIR`. [*resolution.masked-ancestor-enotdir] That is what makes masking total (§4.3.3),
and it is why a lookup costs one full walk per stratum for the name
itself plus one merged resolution per path component above it.

## Independence from the caller

Resolution runs under the credentials captured at mount, against the
root captured at mount, and takes no operation argument. It does not
depend on the calling token, on what the caller is trying to do, or on
whether the operation will ultimately be permitted. [*resolution.independent-of-caller]

A name whose provider the caller may not access therefore resolves
normally and is then refused. It does not fall through to a lower
stratum — which would let a caller's rights change which file they
read, a considerably worse property than a denial. [*resolution.no-fallthrough-on-denial]

## Reaching the object

Once a name resolves to a non-directory provider, the object is the
provider's object and stratafs does not interpose on its contents. The
outer inode takes the provider's mode and, from it, the operations
tables for a regular file, symlink or special file; reads, writes,
mappings, splices, locks and `ioctl`s are forwarded to a backing file
opened on the provider. [*resolution.non-directory-forwarded]

Symbolic links are forwarded rather than followed. The outer inode's
`get_link` calls the provider inode's own and returns the raw target
verbatim; stratafs deliberately does not use `vfs_get_link`, which
would demand a read right the caller need not hold to traverse a link.
The VFS then interprets the target in the caller's own namespace, so an
absolute target resolves from the process's root and may re-enter this
mount, another stratafs mount, or none. [*resolution.symlink-forwarded-verbatim]

Where a mount is established at a path within a stratum, stratafs
follows it: the stratum walk is an ordinary `filename_lookup` with no
flag restricting it to one filesystem, and everything downstream
operates on the inner mount it returns. [*resolution.follows-inner-mounts]

## Staging entries

One class of name is invisible to resolution. While a copy-up is in
flight, its staged object may exist under a name in the create stratum;
that name is dropped from resolution for the mount that owns it, so an
incomplete copy is never reachable through the merged view (§4.5.2). [*resolution.staged-names-hidden]
The suppression applies only to the create stratum, and only within the
owning mount — a second stratafs mount sharing that directory, and any
direct reader of it, sees an ordinary entry. [*resolution.staged-suppression-is-mount-local]

Staged names begin with `.stratafs-stage-`, and a lookup of any name
with that prefix triggers a recovery scan of the create-stratum parent
before resolving. A resolution can therefore have the side effect of
removing orphaned staging entries from the create stratum. [*resolution.stage-prefix-triggers-recovery]

## Recursion

A task that is already resolving inside a superblock and re-enters the
same superblock fails immediately with `ELOOP`. [*resolution.reentrant-superblock-eloop] The guard is a global
list of task-and-superblock pairs, not a depth counter, so a cycle
formed after mount — a stratafs mount established inside one of its own
strata, or bind-mounted into one — terminates the moment resolution
returns to a mount it is already inside.
