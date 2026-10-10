---
title: The Commit Procedure
description: The five steps that take a transaction from uncommitted to committed, and what each one guarantees.
---

The sequence below explains **one root's** package-database durability
boundary. It is not the whole cross-root execution sequence. In the
[reviewed coordinated executor](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/install/execute.go#L230-L348),
all participants are prepared before the per-root commit loop. Files can
already be visible, and another root can already be committed when one
root's commit fails. See [Scope](~peios/peipkg/transactions/scope#cross-root-transactions)
and [Atomicity](~peios/peipkg/transactions/atomicity) for the pinned boundaries.

## 1. Record intent

Before any file moves, the transaction's intent is written to the
journal: the set of file operations, and for each one the staged file's
path and the path its displaced original will be backed up to — the
**backup map**. Directories the transaction will create are recorded
too.

The journal is rows in the package database, so recording intent is an
ordinary database write.

## 2. Apply file operations

For each operation: rename any displaced original aside as a backup,
then rename the staged file into place.

Throughout this phase every change is individually reversible from the
backup map. Nothing has been deleted; a replaced file is sitting beside
its own destination under a different name.

## 3. Commit

In a single database transaction, write the new installed state — the
package rows, the owned-file rows, the claim holder and link rows — and
mark the journal's pending transaction committed.

**This database commit is that root's durability boundary.** Its package
metadata and journal closure are committed together; this does not make
filesystem visibility or other roots' commits atomic with it.

## 4. Invoke side effects

Deduplicated across the whole transaction, after the durability
boundary. A side-effect failure therefore cannot roll the transaction
back: the transaction is already committed, side effects are idempotent,
and a failed one is reported and corrected by re-invocation.

## 5. Clean up

Discard staged files, and delete the backups.

## What the ordering buys

A crash before step 3 leaves the journal's transaction pending, and
recovery rolls it back from the backup map. A crash after step 3 leaves
it committed, and recovery has only step 5 to finish.

That describes a single-root recovery boundary, not coordinated recovery.
A pending cross-root participant can instead need roll-forward after a
sibling committed; rollback can also fail and remain pending. Follow the
[source-scoped recovery path](~peios/peipkg/transactions/crash-recovery#cross-root-the-exception).
The atomic database commit does not establish that there is no observable
intermediate filesystem or multi-root state.
