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

The list above is proposed handling, not a supported recovery interface.
Earlier wording here said recovery only rolls back and writes are never
refused after failure. Do not apply those blanket statements to the
[source-verified cross-root path](~peios/peipkg/transactions/crash-recovery#cross-root-the-exception):
rollback errors retain pending work, an ordinary single-root operation
refuses to recover it in isolation, and coordinated recovery can roll
forward after a sibling commits.

That correction does not establish the five proposed facilities or verify
every single-root failure path. Inspect the actual journal, diagnostics and
installed revision, and use the
[operator recovery checks](~peios/package-management/transactions-and-recovery)
rather than assuming a universal recovery direction or write policy.

## What an operator can do today

`peipkg verify` re-hashes every recorded file against what is on disk
and reports the differences. That is the closest available thing to the
forensic report, and it is the tool for establishing what a failed
operation actually left behind.

`peipkg recover` explicitly attempts recovery and emits an audit event
where the automatic path does not. Coordinated cross-root recovery chooses
rollback or roll-forward from participant state; its console message alone
does not establish that direction.

Beyond that, reconciling the database with the filesystem is manual:
identifying files sitting at backup paths, deciding whether the old or
the new content is wanted, and reinstalling the affected packages to
restore agreement.
