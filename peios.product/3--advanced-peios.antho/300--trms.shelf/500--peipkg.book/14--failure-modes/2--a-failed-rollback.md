---
title: A Failed Rollback
description: When the rollback itself fails — what is left on disk, what peipkg does about it, and what it means for the next operation.
---

The rollback itself fails: a write error, a filesystem gone read-only, a
permission change mid-operation.

## What is left

Some originals restored, some still at their backup paths. Some new
files removed, some still at their final paths. The database holding the
pre-transaction state, because the commit never ran.

## What peipkg does

Discards the error, closes the journal's transaction as rolled back, and
returns.

## What that means for the next operation

Recovery looks for a pending transaction and finds none, so it does not
retry. The history shows an authoritative-looking rolled-back record.
Nothing tells the operator the rollback did not complete.

## The signal that is available

`peipkg verify` re-hashes every recorded file against what is on disk.
Files the rollback failed to restore will not match their recorded
hashes, and will be reported as modified.

A directory listing around the affected paths shows the leftovers
directly: siblings carrying the backup and staged markers with the
failed transaction's identifier.

## Getting back to a known state

Identify the affected paths, decide whether the old or the new content
is wanted, remove the leftover siblings, and reinstall the affected
packages so that the database and the filesystem agree again.
