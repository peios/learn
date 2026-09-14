---
title: Waiting and Contention
description: The busy timeout is set deliberately shorter than the kernel's request timeout — waiting for the write connection, and abandoned transactions.
---

Every connection is opened with `busy_timeout` set to 25 seconds,
deliberately shorter than the kernel's 30-second request timeout so that
loregd can answer `RSI_TXN_BUSY` before the caller is timed out from
above. [*contend.the-busy-timeout-is-shorter-than-the-kernels-request-timeout]

That bound governs one kind of waiting: contention for SQLite's own write
lock on the hive database. Two other kinds arise, and neither is bounded
by it. [*contend.the-busy-timeout-bounds-only-sqlite-write-lock-contention]
loregd issues no database operation with a deadline attached.
[*contend.no-database-operation-carries-a-deadline]

## Waiting for the write connection

Each hive's write handle owns exactly one connection (§4.1). When a
read-write transaction binds, it holds that connection until it commits or
aborts, so any other write to the same hive waits — and it waits inside
Go's connection pool, before SQLite is ever reached.
[*contend.a-bound-transaction-holds-the-write-connection-until-it-commits-or-aborts]
`busy_timeout` is not consulted, because there is no SQLite lock in
contention; the second writer simply has no connection to run on.
[*contend.a-second-writer-waits-in-the-connection-pool-unbounded-by-busy-timeout]

`RSI_FLUSH` is the one operation that refuses to join this queue. It
checks whether any transaction is bound to the hive and returns
`RSI_TXN_BUSY` immediately if one is, because a checkpoint on a connection
already held by a transaction would deadlock.
[*contend.flush-returns-rsi-txn-busy-rather-than-queueing-behind-a-transaction]
The check is racy — a transaction can bind between the check and the
checkpoint. [*contend.the-flush-bound-transaction-check-is-racy] Note also
that it does not distinguish a read-only snapshot, which lives on its own
connection, from a write binding, so a flush during a backup returns
`RSI_TXN_BUSY` even though the checkpoint could have proceeded.
[*contend.flush-does-not-distinguish-a-read-only-snapshot-from-a-write-binding]

`RSI_DELETE_LAYER`, a non-transactional `RSI_DROP_KEY`, and the
conditional-write path of a non-transactional `RSI_SET_VALUE` all take the
write connection without that guard, and queue behind a bound transaction.
[*contend.delete-layer-drop-key-and-conditional-set-value-queue-behind-a-bound-transaction]

## Waiting on the volatile store

The volatile database is in shared-cache mode with journal mode `memory`
(§4.1). It therefore has no multi-version concurrency: readers and writers
contend for table locks rather than passing each other.
[*contend.the-volatile-store-has-no-multi-version-concurrency]

> [!IMPORTANT]
> A transaction that has written any `volatile.*` table holds a write-table
> lock on it for the transaction's whole lifetime.
> [*contend.a-volatile-write-holds-a-table-lock-for-the-transactions-lifetime]
> A volatile read on any other connection waits for that lock, and the wait
> is not bounded by `busy_timeout`.
> [*contend.a-volatile-read-waits-unbounded-for-a-volatile-write-lock]
>
> This reaches **every** read operation, not only ones a caller thinks of
> as volatile. All four read operations query `main` and `volatile` in one
> `UNION ALL` statement (§5.1), and hive resolution probes
> `volatile.keys` as well (§4.2). So while a transaction that has touched
> volatile data is open, ordinary reads against the same hive block in
> their serving goroutine rather than returning a status.
> [*contend.an-open-volatile-writing-transaction-blocks-ordinary-reads-in-their-goroutine]
>
> The relationship is symmetric. A read-only snapshot that has read a
> volatile table holds a read-table lock for as long as the snapshot
> lives, and volatile writes wait for it.
> [*contend.a-read-only-snapshot-holds-a-volatile-read-table-lock-for-its-lifetime]
> Read-only snapshots are what serve the kernel's `REG_IOC_BACKUP`, which
> is expected to be long-lived.

Contention confined to the persistent side behaves as WAL promises: a
transaction writing only the hive database does not block reads of it,
[*contend.a-write-to-the-hive-database-does-not-block-reads-of-it] and a
transaction writing only volatile tables does not block reads of the hive
database.
[*contend.a-volatile-only-write-does-not-block-reads-of-the-hive-database]

## Abandoned transactions [*contend.nothing-reclaims-an-abandoned-transaction]

Nothing reclaims a transaction that is never committed or aborted. There
is no timeout, and no sweep at any point in the daemon's life. Such a
transaction holds its hive's write connection — and, if it wrote volatile
data, its volatile table locks — until the process exits.
[*contend.an-abandoned-transaction-holds-its-connection-and-locks-until-the-process-exits]
