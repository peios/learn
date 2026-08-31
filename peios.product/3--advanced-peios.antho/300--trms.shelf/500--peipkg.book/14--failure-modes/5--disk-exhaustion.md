---
title: Disk Exhaustion
description: Free space is checked per filesystem before staging — and what happens if a write still fails, depending on where in the operation it does.
---

peipkg checks free space before it stages anything, so exhaustion
normally arrives as a refusal that costs nothing. A write can still fail
— another process can consume the space in between, and the estimate is
of payload rather than of the metadata the filesystem writes alongside
it — and where in the operation that happens decides how bad it is.

## During staging

The cleanest case. Nothing has been renamed into place, the transaction
rolls back, and the staged files are discarded — recovering the space
they consumed.

## During the apply phase

Some files have been renamed in and some originals are sitting at their
backup paths.

Because backups are renames rather than copies, the apply phase itself
consumes almost no additional space: the space was consumed during
staging. A failure here is more likely to be a different error than
exhaustion.

Rollback restores from the backup map, which is again renames, so it
does not need space either.

## During the commit

The database commit needs space for its own write-ahead log. A failure
there leaves the transaction uncommitted, and rollback proceeds
normally — but a database that cannot write is a database that cannot
record a rollback, which is where §14.2 begins.

## The check

A transaction's requirement is the incoming file content of its added
and replaced entries, aggregated across every operation. Backups cost
nothing, because they are renames rather than copies, and a removal
frees rather than consumes. A replaced file's old bytes are not
subtracted: they are still on disk under the backup name until the
commit succeeds, which is exactly when the space is needed.

The figure is computed **per filesystem**, not as a single total,
because a transaction can span several — installation roots and
destinations within a root can be separate mounts. Destinations are
grouped by the filesystem id their directory reports, so the mount table
never has to be read.

The comparison is against the blocks available to an unprivileged
writer, not the free blocks: the reserved fraction is not peipkg's to
spend. A 32 MiB margin is left on top, covering the inodes, directory
entries, journal blocks and tail padding the filesystem writes that the
payload figure does not include. The check runs before the journal is
opened, so a refusal leaves nothing to recover from.
