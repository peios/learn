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

For the reviewed cross-root preparation rollback in
[peipkg `8b588ae8`](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/install/execute.go#L668-L724),
it reports rollback errors and retains the affected pending journal. Use
[coordinated recovery](~peios/package-management/transactions-and-recovery#across-more-than-one-root),
with all participants reachable from the original anchor.

Earlier wording here described errors being discarded and the journal
closed as rolled back. That closed-journal failure remains a diagnostic
case to distinguish; it is not the contract of the pinned cross-root path.
This correction does not verify every single-root path or released image.

## What that means for the next operation

First inspect whether the journal is pending or closed. A pending cross-root
transaction is not safely recovered in isolation by an ordinary single-root
operation. Preserve its participants and recovery files.

In the previously described **closed-journal** case, recovery finds no
pending transaction to retry even though restoration failed. A rolled-back
record can then look authoritative while files still disagree with it.
Neither case makes file verification optional.

## The signal that is available

`peipkg verify` re-hashes every recorded file against what is on disk.
Files the rollback failed to restore will not match their recorded
hashes, and will be reported as modified.

A directory listing around the affected paths shows the leftovers
directly: siblings carrying the backup and staged markers with the
failed transaction's identifier.

## Getting back to a known state

Retain staged and backup siblings while recovery and diagnosis still need
them. Identify the affected paths, inspect transaction state, and verify
what was restored before deciding whether old or new content is wanted.
Follow the [operator recovery checks](~peios/package-management/transactions-and-recovery#when-recovery-does-not-restore-the-files)
for unresolved files and package records; do not delete recovery material
or start another package change merely to make the leftovers disappear.
