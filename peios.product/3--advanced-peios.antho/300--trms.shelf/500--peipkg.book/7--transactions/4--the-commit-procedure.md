---
title: The Commit Procedure
description: The five steps that take a transaction from uncommitted to committed, and what each one guarantees.
---

Commit transitions a transaction from uncommitted to committed, in five
steps.

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

**This database commit is the durability boundary.** It is atomic, so
the transaction is either fully committed or not committed at all.

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

Because step 3 is a single atomic database commit, and because it
carries both the new state and the journal's closure, there is no
intermediate state to discover.
