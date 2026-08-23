---
title: Waiting and Contention
description: The busy timeout is set deliberately shorter than the kernel's request timeout — waiting for the write connection, and abandoned transactions.
---

Every connection is opened with `busy_timeout` set to 25 seconds,
deliberately shorter than the kernel's 30-second request timeout so that
loregd can answer `RSI_TXN_BUSY` before the caller is timed out from
above.

That bound governs one kind of waiting: contention for SQLite's own write
lock on the hive database. Two other kinds arise, and neither is bounded
by it. loregd issues no database operation with a deadline attached.

## Waiting for the write connection

Each hive's write handle owns exactly one connection (§4.1). When a
read-write transaction binds, it holds that connection until it commits or
aborts, so any other write to the same hive waits — and it waits inside
Go's connection pool, before SQLite is ever reached. `busy_timeout` is not
consulted, because there is no SQLite lock in contention; the second
writer simply has no connection to run on.

`RSI_FLUSH` is the one operation that refuses to join this queue. It
checks whether any transaction is bound to the hive and returns
`RSI_TXN_BUSY` immediately if one is, because a checkpoint on a connection
already held by a transaction would deadlock. The check is racy — a
transaction can bind between the check and the checkpoint. Note also that
it does not distinguish a read-only snapshot, which lives on its own
connection, from a write binding, so a flush during a backup returns
`RSI_TXN_BUSY` even though the checkpoint could have proceeded.

`RSI_DELETE_LAYER`, a non-transactional `RSI_DROP_KEY`, and the
conditional-write path of a non-transactional `RSI_SET_VALUE` all take the
write connection without that guard, and queue behind a bound transaction.

## Waiting on the volatile store

The volatile database is in shared-cache mode with journal mode `memory`
(§4.1). It therefore has no multi-version concurrency: readers and writers
contend for table locks rather than passing each other.

> [!IMPORTANT]
> A transaction that has written any `volatile.*` table holds a write-table
> lock on it for the transaction's whole lifetime. A volatile read on any
> other connection waits for that lock, and the wait is not bounded by
> `busy_timeout`.
>
> This reaches **every** read operation, not only ones a caller thinks of
> as volatile. All four read operations query `main` and `volatile` in one
> `UNION ALL` statement (§5.1), and hive resolution probes
> `volatile.keys` as well (§4.2). So while a transaction that has touched
> volatile data is open, ordinary reads against the same hive block in
> their serving goroutine rather than returning a status.
>
> The relationship is symmetric. A read-only snapshot that has read a
> volatile table holds a read-table lock for as long as the snapshot
> lives, and volatile writes wait for it. Read-only snapshots are what
> serve the kernel's `REG_IOC_BACKUP`, which is expected to be
> long-lived.

Contention confined to the persistent side behaves as WAL promises: a
transaction writing only the hive database does not block reads of it, and
a transaction writing only volatile tables does not block reads of the
hive database.

## Abandoned transactions

Nothing reclaims a transaction that is never committed or aborted. There
is no timeout, and no sweep at any point in the daemon's life. Such a
transaction holds its hive's write connection — and, if it wrote volatile
data, its volatile table locks — until the process exits.
