---
title: Disk Exhaustion
description: peipkg does not check free space first — where in the operation the write fails decides how bad it is.
---

peipkg does not check free space before it starts. Exhaustion is
discovered when a write fails, and where in the operation that happens
decides how bad it is.

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

## Planning ahead

A transaction's additional requirement is the staged new and changed
content, aggregated across every operation. Backups cost nothing.

Because a transaction can span several filesystems — installation roots
and destinations within a root can be separate mounts — the useful
figure is per filesystem rather than a single total.

Nothing computes either figure. The manifest's declared installed size
is available and is used to bound decompression, not to plan space.
