---
title: Transactions
description: Transaction ids are allocated by the kernel and bound to connections lazily — beginning, read-write against read-only, committing and aborting.
---

Transaction identifiers are allocated by the kernel and carried on every
request. loregd binds them to connections lazily — `RSI_BEGIN_TRANSACTION`
does no SQLite work at all.

## Beginning

`RSI_BEGIN_TRANSACTION` carries the transaction id and a mode:
`RSI_TXN_READ_WRITE` (0) or `RSI_TXN_READ_ONLY` (1). loregd records the id
as pending in the requested mode and returns `RSI_OK` immediately. No
connection is taken and no SQLite transaction is opened.

loregd supports both modes — its SQLite backing provides atomic
read-write commits and stable read-only snapshots — so it never returns
`RSI_TXN_NOT_SUPPORTED`.

Re-using a transaction id that is already active returns `RSI_INVALID`.
If the mode field is absent from the request, the transaction is treated
as read-write.

## Read-write transactions

The transaction binds to a hive on its **first mutating operation**:
loregd identifies the hive from the operation's GUID, acquires that hive's
write connection, issues `BEGIN IMMEDIATE`, and records the binding. If
SQLite reports `SQLITE_BUSY` at that point, the operation returns
`RSI_TXN_BUSY`.

Once bound, every subsequent operation with that transaction id — reads
included — runs on the same connection. That is what provides
read-your-own-writes: uncommitted rows are visible to the transaction
because it is the connection that wrote them. Reads issued *before* the
transaction binds go to the read pool instead, since there is nothing
uncommitted to see.

Because the connection has both the hive database and the volatile
database attached, a single SQLite transaction spans both. Persistent and
volatile mutations made inside one transaction commit together and roll
back together, with no separate mechanism reconciling them.

An operation whose GUID belongs to a different hive than the transaction
is bound to is rejected with `RSI_STORAGE_ERROR`. The kernel enforces
hive-scoping before requests reach loregd, so this is a backstop.

## Read-only transactions

A read-only transaction binds on its **first read**. loregd identifies the
hive, opens a **dedicated connection** — deliberately not one from the
read pool, so a long-lived snapshot cannot starve ordinary reads — and
issues `BEGIN DEFERRED`. WAL fixes the snapshot at that first read, and
every later read with the same transaction id reuses the connection and
observes the same point in time.

The snapshot is exact for persistent data. Volatile data has no snapshot
mechanism: a volatile read inside a read-only transaction observes the
live store.

A mutating operation carrying a read-only transaction id is rejected with
`RSI_INVALID` before any state changes — for the nine operations that
route through the write path. `RSI_DELETE_LAYER` and `RSI_FLUSH` do not
check (§4.1).

## Committing and aborting

`RSI_COMMIT_TRANSACTION` issues `COMMIT` on the bound connection and
returns `RSI_OK`. If the commit fails, the transaction is **left open** so
the caller may retry or abort: a busy or locked failure returns
`RSI_TXN_BUSY`, anything else `RSI_STORAGE_ERROR`. Committing an unknown
transaction id returns `RSI_STORAGE_ERROR`.

Committing a read-only transaction releases the snapshot and returns
`RSI_OK`.

`RSI_ABORT_TRANSACTION` issues `ROLLBACK`, closes the connection, releases
any snapshot, runs the transaction's abort hooks, and always returns
`RSI_OK` — including for a transaction id it has never seen. Rollback
errors are logged and not reported. This is how the kernel releases a
read-only snapshot after a `REG_IOC_BACKUP` finishes or fails.

A transaction that is neither committed nor aborted is never cleaned up:
there is no timeout and no reaper. It holds its hive's write connection
until the process exits — see §4.4.
