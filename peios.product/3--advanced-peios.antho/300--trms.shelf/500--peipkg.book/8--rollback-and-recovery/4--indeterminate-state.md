---
title: Indeterminate State
description: A failed rollback or corrupt journal leaves a state peipkg cannot reason about — what exists today, and what an operator can do.
---

A failed rollback, a corrupt journal, or an unrecoverable backup
mismatch leaves the system in a state peipkg cannot reason about.

## The intended handling

A recovery mode with five properties:

1. Every write operation — install, upgrade, uninstall — is refused
   until recovery completes.
2. Read operations proceed but carry the indeterminate-state warning in
   their output.
3. A forensic report is available on demand, identifying the pending
   transaction's operations, files whose on-disk content does not match
   the recorded hash, database records inconsistent with the journal,
   and any orphaned staged files or backups.
4. An explicit resolution command accepts an operator decision: roll the
   pending transaction back, **or** accept the current on-disk state and
   discard the journal and backups.
5. Resolution is a deliberate operator action and is never performed
   automatically.

## What exists

None of the five.

There is no indeterminate state as a concept: a transaction is pending
or it is not. Writes are not refused after a failure; reads carry no
warning; there is no forensic report; `peipkg recover` offers only
rollback, with no way to accept the current state and discard the
journal; and recovery runs automatically at the head of every operation,
with no prompt.

The last point is the sharpest. Automatic rollback of a *pending*
transaction is correct and is what §7.8 describes. But because nothing
distinguishes a cleanly pending transaction from an indeterminate one,
automatic resolution is the only behaviour available for both.

## What an operator can do today

`peipkg verify` re-hashes every recorded file against what is on disk
and reports the differences. That is the closest available thing to the
forensic report, and it is the tool for establishing what a failed
operation actually left behind.

`peipkg recover` rolls back a pending transaction explicitly, and emits
an audit event where the automatic path does not.

Beyond that, reconciling the database with the filesystem is manual:
identifying files sitting at backup paths, deciding whether the old or
the new content is wanted, and reinstalling the affected packages to
restore agreement.
