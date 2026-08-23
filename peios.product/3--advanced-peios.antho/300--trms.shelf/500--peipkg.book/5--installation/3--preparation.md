---
title: Preparation
description: Computing what the install will do — which files and directories are created, which side effects fire, collisions and disk space.
---

With the package validated, peipkg computes what the install will do:
which files are created, which directories are created, which side
effects will be scheduled.

## Collisions

A payload path already owned by another installed package is a
collision, and the database refuses it: the rule that two packages may
not own the same non-directory path is a partial unique index on the
owned-files table.

That constraint is evaluated when the transaction's database changes are
written, which is at commit — after the files have already been renamed
into place. A colliding install therefore fails, but only after paying
the full download, extraction, and on-disk replacement, and recovery
depends on the rollback succeeding.

There is no earlier check. Collisions are not detected at plan time or
at preparation time.

## Disk space

peipkg does not check free space before staging. Exhaustion is
discovered when a write fails — during staging, where rollback is
straightforward, or during the apply phase, where some files have been
renamed into place and some originals are sitting at their backup
paths.

A transaction may span several filesystems, since installation roots and
the destinations within a root can be separate mounts, so a single
global free-space figure would not be the right check even if one were
made.
