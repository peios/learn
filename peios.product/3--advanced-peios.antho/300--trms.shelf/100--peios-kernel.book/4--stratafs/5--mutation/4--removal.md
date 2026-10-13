---
title: Removal
description: stratafs has no whiteouts, so removal can only remove an entry that is really there — and what removal therefore never does.
---

stratafs has no whiteouts and cannot record that a name should be
absent. Removal can therefore only remove an entry that is actually
there, in a stratum it may write to.

## Unlinking [*remove.unlink-in-provider]

To remove a non-directory name from a merged directory: if the provider
accepts modification (§4.5.1), the entry is removed from the provider;
otherwise the operation fails with `EROFS`. The parent is resolved in
the provider's stratum, and the unlink is performed there.

The provider need not be the create stratum. Any stratum that accepts
modification may have an entry removed from it, by the same rule that
allows an object it provides to be modified in place.

Where a lower-precedence stratum also holds the name, that entry
becomes the provider once the higher one is removed, and the name
remains visible, now resolving to the lower stratum's object. That is
not an error and is not reported as one: the removal succeeded, and the
entry it removed is gone. The dentry is dropped on success, so the next
lookup finds the lower entry.

Removing an object that a lower stratum also provides is how a
modification is undone. Where a file was copied up in order to be
edited, removing it through the mount discards the edit and restores
the original, which remained untouched in its own stratum throughout.
Callers expecting POSIX removal will find the name still present
afterwards; §4.8 records this as an intended divergence.

Refusal because the provider does not accept modification is `EROFS`,
with one exception: where the provider's inode is immutable it is
`EPERM`. The outer inode carries the provider's inode flags, so the VFS
refuses the removal before stratafs's own `EROFS` test is reached — and
`EPERM` is what every filesystem returns for an immutable file, so the
distinction is the useful one rather than an accident worth papering
over. The `ro` flag and a read-only provider mount both still produce
`EROFS`.

## Removing directories [*remove.rmdir-merged-emptiness]

The same rule applies, with one additional condition: the **merged**
directory must be empty. A directory is empty for this purpose only if
no participating stratum holds any entry within it, so a directory that
is empty in the provider but not in another participant fails with
`ENOTEMPTY`.

### Access checks precede the emptiness scan [*remove.access-before-emptiness]

Because determining this reads the contents of every participating
stratum, the caller must hold traverse and list rights on each of them.
That check completes over all participants before any of them is
enumerated, so a refusal yields `EACCES` without disclosing whether the
directory was empty. Without that ordering the emptiness test would be
a disclosure channel: a caller who may not enumerate a protected
participant could learn whether it contains anything by attempting
`rmdir` and distinguishing `ENOTEMPTY` from success.

The emptiness scan filters this mount's in-flight staging entries, as
enumeration does. That does not authorise removing a live stage: the
provider can still refuse the physical removal with `ENOTEMPTY`.

### Orphan recovery before inspection [*remove.rmdir-staging-recovery]

After the traverse/list checks complete, the emptiness test runs orphan
recovery on the create stratum's participating directory **before**
enumerating its contents (§4.5.2). A dead mount's entries are not in the
current mount's in-flight list, so waiting until that list has filtered
them would reject the directory before recovery could run. A directory
containing only recoverable orphan files or empty orphan directories can
therefore be removed without first opening or listing it.

Recovery requires the staging prefix, a valid marker, and an owner that
is no longer live. Missing or malformed markers, ordinary published
names, and stages belonging to a live mount remain untouched; they can
still make removal fail with `ENOTEMPTY`. The scan is local to the
participating create directory, not a recursive walk of the stratum.

Where the directory is removed and lower strata hold the same name as a
directory, the name remains visible as a merged directory of the
remaining strata — which, by the emptiness condition, is empty.

## What removal never does [*remove.touches-only-the-provider]

Removal touches exactly one stratum, the provider's. The other strata
are opened read-only for the emptiness scan and nothing else. No entry,
marker, or object is created in any stratum to suppress a lower entry;
no whiteout machinery exists anywhere in the filesystem.

Success is never reported for a name whose provider entry was not
removed. The one place zero is returned without a removal is the
deferred path of §4.5.3, where the entry the descriptor named is
already gone and the deletion is genuinely complete.
