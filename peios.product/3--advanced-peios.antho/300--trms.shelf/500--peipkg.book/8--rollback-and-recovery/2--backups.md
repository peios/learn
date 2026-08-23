---
title: Backups
description: A displaced original is renamed aside within its own directory and never copied — the naming scheme and the retention rules.
---

A backup is made by **renaming the displaced original aside within its
own directory**, never by copying it.

The old file's content is retained in place under a different name, so a
backup costs no additional disk space and is produced by a single atomic
rename. The journal's backup map records, for each displaced file, the
name its original was renamed to.

Restoring a backup on rollback is the inverse rename. Discarding one on
commit is a delete.

## Naming

A backup and a staged file are both siblings of the destination, in the
destination's own directory, under names carrying a marker and the
transaction identifier. Where the destination's basename is long enough
that adding the marker would exceed the filesystem's name limit, the
basename is truncated.

Two long sibling basenames that differ only past the truncation point
therefore produce the same temporary name.

## Retention

Backups are discarded as soon as the transaction commits.

The design permits keeping them beyond commit for a configured window,
to support reverting a committed transaction from local state. That is
not implemented, which is why `peipkg undo` works by re-resolving
against the archive index rather than by restoring backups (§6.5), and
why undo needs a reachable repository.
