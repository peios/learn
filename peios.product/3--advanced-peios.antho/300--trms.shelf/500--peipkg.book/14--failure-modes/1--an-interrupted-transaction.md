---
title: An Interrupted Transaction
description: Power loss or a kill partway through — what the journal preserves, what happens next, and how a post-commit crash differs.
---

The system loses power, or the process is killed, partway through an
operation.

## What survives

The transaction's journal is rows in the package database, written
before any file moved, carrying the backup map. The database is a
transactional store, so the journal is either there or it is not — never
half-written.

## What happens next

The next install, upgrade, or uninstall acquires the lock, finds the
pending transaction, and rolls it back: every displaced original renamed
from its backup path back into place, every directory the transaction
created removed, every staged file discarded, and the transaction
cleared.

That happens automatically and silently. No prompt, and no audit event.

## If the crash came after the commit

The transaction is committed and there is nothing to recover. What is
left is cleanup: staged files and backups that were never discarded.

Those are siblings of their destinations under names carrying the
transaction identifier, and they are removed by the cleanup step
whenever it next runs.

## If the transaction spanned several roots

Recovery rolls forward instead. A root found pending after a sibling
committed is completed from the state its journal persisted, because a
committed sibling cannot be undone.

A pending root carrying no persisted state can be neither completed nor
safely reversed, and recovery refuses it — blocking further work in that
root until `peipkg recover` is run.

A pending cross-root transaction found by an ordinary single-root
operation is refused rather than recovered, for the same reason.

## If peipkg was upgraded in between

The journal records the schema version it was written under. A peipkg
that can read it recovers the transaction; one that cannot refuses,
naming the schema version, and leaves it for a version that can.
