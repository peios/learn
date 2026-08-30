---
title: Locking
description: Advisory locks across a stack of independently writable directories — the rule, a changing provider, the retired provider, and leases.
---

Advisory file locks — whole-file and record locks alike — exist so that
several writers of one file can coordinate. A stratafs mount is
established over directories that have their own writers, so a lock
taken through the mount and a lock taken directly on the same object
must be the same lock.

## The rule [*lock.taken-on-the-provider-object]

A lock taken through a stratafs mount is held on the provider's object,
in the same lock space as a lock taken on that object by any other
path. Both the POSIX and the `flock` paths retarget the request onto
the descriptor's provider file, so the lock lands on the provider
inode's own lock context.

stratafs maintains no lock space of its own. There is no lock list, no
fallback onto the outer inode, and no per-inode lock state. Two callers
that lock the same provider object — one through the mount, one through
the stratum directly, or two through different stratafs mounts sharing
that stratum — contend with each other. Open-file-description locks are
re-owned onto the provider file so that their per-description semantics
are preserved.

Taking a lock does not modify an object, so it does not route (§4.5.1)
and cannot itself cause a copy-up. Locking requires no write access
either, so a read-only descriptor can carry an exclusive lock.

## Locks and a changing provider [*lock.not-transferred-on-provider-change]

A lock is held on the object a descriptor resolved to. That object may
cease to be the provider afterwards — because a higher-precedence
stratum gains the name, because the object is removed from its stratum,
or because a copy-up produced a new object.

In every such case the lock remains held on the object it was taken on.
It is not transferred, and it does not begin to guard the new provider.

**Two callers may therefore hold exclusive locks on one merged path
without contending**, whenever they opened it either side of a change of
provider. Neither is wrong about the object it locked; they locked
different objects, and each lock is honoured by everything else holding
that object. The merged path is what stopped naming one thing. §4.8
records it.

A caller that must be sure it holds a lock on the current provider has
to reopen and re-take it, which is the same discipline required of
anything that locks a path another process may replace by rename. The
exposure here is that a copy-up is a replacement the caller did not
perform and cannot see.

## The retired provider

Copy-up does not close the file it copied from. The pre-copy-up
provider file is moved aside into the descriptor's private state
specifically to keep locks and leases taken before the copy-up alive,
and the fan-out that follows is invisible to the specification but
visible in behaviour:

- A POSIX or `flock` **unlock** is applied to both the retired file and
  the copy; a non-unlock request goes only to the copy. [*lock.unlock-reaches-the-retired-file]
- A lease release is applied to both. A lease *acquisition* is
  redirected to the retired file when that file already holds a lease
  of the same flavour. [*lock.lease-acquisition-redirected]
- Querying a lease returns the stronger of the two files' lease types,
  ordering write above read above none. [*lock.lease-query-returns-the-stronger]
- Closing the descriptor runs the underlying flush and removes POSIX
  locks on both files, and releasing it breaks leases on both, using
  the outer file as the owner identity. [*lock.close-clears-both-files]

All of it is serialised by the descriptor's mutation lock.

## Leases and mandatory locking [*lock.leases-are-the-providers]

Leases are established on the provider's object, in that object's own
lock space, and every result is the provider's own, returned unchanged.
stratafs neither adds to nor removes from whatever semantics the
provider's filesystem gives them, and never reports a lock as
established where the provider's filesystem refused it.

Mandatory locking has no subject here: the platform does not offer it,
and stratafs contains nothing that would obstruct it. The outer inode
copies the provider's inode flags wholesale.

## Internal locks

The specification names no internal lock and fixes no acquisition
order. The implementation's hierarchy, outermost first:

1. The per-open-file **mutation lock**, taken by every operation that
   may copy up.
2. The per-outer-inode **rebind lock**, taken inside it whenever an
   inode's provider is swapped.
3. The dentry lock or the inode lock, taken inside the rebind lock and
   never overlapping each other.

The superblock's identity lock and staging lock are each taken alone.
`copy_file_range` and `remap_file_range` deliberately do not nest the
two files' mutation locks: the input file's is taken, a reference
grabbed, and released before the output file's is taken.

For mutations the ordering is: the KACS decision, then parent
materialisation, then write access on the target mount, then the
parent's directory lock through the VFS's create, remove or rename
helpers. Refusal auditing takes the dentry lock with an atomic
allocation first and falls back to the rebind lock only if that fails,
so the two are never nested.
