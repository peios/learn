---
title: Transactions
description: Transaction ids are allocated by the kernel and bound to connections lazily — beginning, read-write against read-only, committing and aborting.
---

Transaction identifiers are allocated by the kernel and carried on every
request.
[*txn.transaction-ids-are-allocated-by-the-kernel-and-carried-on-every-request]
loregd binds them to connections lazily — `RSI_BEGIN_TRANSACTION`
does no SQLite work at all.

## Beginning

`RSI_BEGIN_TRANSACTION` carries the transaction id and a mode:
`RSI_TXN_READ_WRITE` (0) or `RSI_TXN_READ_ONLY` (1). loregd records the id
as pending in the requested mode and returns `RSI_OK` immediately.
[*txn.begin-records-the-id-as-pending-and-returns-rsi-ok-immediately] No
connection is taken and no SQLite transaction is opened.
[*txn.begin-takes-no-connection-and-opens-no-sqlite-transaction]

loregd supports both modes — its SQLite backing provides atomic
read-write commits and stable read-only snapshots — so it never returns
`RSI_TXN_NOT_SUPPORTED`. [*txn.loregd-never-returns-rsi-txn-not-supported]

Re-using a transaction id that is already active returns `RSI_INVALID`.
[*txn.re-using-an-active-transaction-id-returns-rsi-invalid]
If the mode field is absent from the request, the transaction is treated
as read-write. [*txn.an-absent-mode-field-means-read-write]

## Read-write transactions

The transaction binds to a hive on its **first mutating operation**:
loregd identifies the hive from the operation's GUID, acquires that hive's
write connection, issues `BEGIN IMMEDIATE`, and records the binding.
[*txn.a-read-write-transaction-binds-on-its-first-mutating-operation]
If SQLite reports `SQLITE_BUSY` at that point, the operation returns
`RSI_TXN_BUSY`. [*txn.a-busy-database-at-bind-time-returns-rsi-txn-busy]

Once bound, every subsequent operation with that transaction id — reads
included — runs on the same connection.
[*txn.once-bound-every-operation-on-the-transaction-runs-on-the-same-connection]
That is what provides read-your-own-writes: uncommitted rows are visible
to the transaction because it is the connection that wrote them.
[*txn.a-transaction-sees-its-own-uncommitted-writes] Reads issued
*before* the transaction binds go to the read pool instead, since there
is nothing uncommitted to see.
[*txn.a-read-issued-before-binding-goes-to-the-read-pool]

Because the connection has both the hive database and the volatile
database attached, a single SQLite transaction spans both. Persistent and
volatile mutations made inside one transaction commit together and roll
back together, with no separate mechanism reconciling them.
[*txn.persistent-and-volatile-mutations-commit-and-roll-back-together]

An operation whose GUID belongs to a different hive than the transaction
is bound to is rejected with `RSI_STORAGE_ERROR`.
[*txn.an-operation-on-another-hive-is-rejected-with-rsi-storage-error]
The kernel enforces hive-scoping before requests reach loregd, so this is
a backstop.

## Read-only transactions

A read-only transaction binds on its **first read**.
[*txn.a-read-only-transaction-binds-on-its-first-read] loregd identifies
the hive, opens a **dedicated connection** — deliberately not one from the
read pool, so a long-lived snapshot cannot starve ordinary reads — and
issues `BEGIN DEFERRED`.
[*txn.a-read-only-transaction-gets-a-dedicated-connection-outside-the-read-pool]
WAL fixes the snapshot at that first read, and every later read with the
same transaction id reuses the connection and observes the same point in
time.
[*txn.every-read-in-a-read-only-transaction-observes-the-same-snapshot]

The snapshot is exact for persistent data.
[*txn.the-snapshot-is-exact-for-persistent-data] Volatile data has no
snapshot mechanism: a volatile read inside a read-only transaction
observes the live store.
[*txn.a-volatile-read-inside-a-read-only-transaction-sees-the-live-store]

A mutating operation carrying a read-only transaction id is rejected with
`RSI_INVALID` before any state changes.
[*txn.a-mutation-in-a-read-only-transaction-is-rejected-before-any-state-changes]
The nine operations that route through the write path get this from the
routing itself; `RSI_DELETE_LAYER` and `RSI_FLUSH` cannot route that way
and ask directly, for the same answer (§4.1).

## Committing and aborting

`RSI_COMMIT_TRANSACTION` issues `COMMIT` on the bound connection and
returns `RSI_OK`.
[*txn.commit-issues-commit-on-the-bound-connection-and-returns-rsi-ok]
If the commit fails, the transaction is **left open** so the caller may
retry or abort: a busy or locked failure returns `RSI_TXN_BUSY`, anything
else `RSI_STORAGE_ERROR`.
[*txn.a-failed-commit-leaves-the-transaction-open-for-retry-or-abort]
Committing an unknown transaction id returns `RSI_STORAGE_ERROR`.
[*txn.committing-an-unknown-transaction-id-returns-rsi-storage-error]

Committing a read-only transaction releases the snapshot and returns
`RSI_OK`. [*txn.committing-a-read-only-transaction-releases-the-snapshot]

`RSI_ABORT_TRANSACTION` issues `ROLLBACK`, closes the connection, releases
any snapshot, runs the transaction's abort hooks,
[*txn.abort-rolls-back-closes-the-connection-and-runs-the-abort-hooks] and
always returns `RSI_OK` — including for a transaction id it has never
seen.
[*txn.abort-always-returns-rsi-ok-including-for-an-unknown-transaction-id]
Rollback errors are logged and not reported. This is how the kernel
releases a read-only snapshot after a `REG_IOC_BACKUP` finishes or fails.

A transaction that is neither committed nor aborted is never cleaned up:
there is no timeout and no reaper.
[*txn.an-uncommitted-transaction-is-never-reclaimed] It holds its hive's
write connection until the process exits — see §4.4.
