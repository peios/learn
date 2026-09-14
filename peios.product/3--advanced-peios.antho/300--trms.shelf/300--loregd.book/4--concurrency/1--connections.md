---
title: Connections
description: Each hive holds a small fixed set of SQLite connections — what each carries, and which one an operation runs on.
---

Each hive holds a small, fixed set of SQLite connections, and which one an
operation runs on decides both its isolation and what it can block on.

| Connection | Count | Used for |
|---|---|---|
| Write | One per hive | Every mutating operation, and every read inside a bound read-write transaction. [*conn.every-mutation-runs-on-the-hives-single-write-connection] |
| Read pool | `min(NumCPU, 16)`, at least 1 | Reads outside a transaction. Selected round-robin. [*conn.reads-outside-a-transaction-use-the-round-robin-read-pool] |
| Snapshot | One per active read-only transaction | Reads inside a read-only transaction. Created on demand, closed when the transaction ends. [*conn.each-read-only-transaction-gets-its-own-snapshot-connection] |

The pool size is compiled in and cannot be configured — loregd reads no
configuration (§2.1).
[*conn.the-pool-size-is-compiled-in-and-cannot-be-configured]

## One connection per handle [*conn.every-handle-is-limited-to-one-underlying-connection]

Every one of these is a Go `database/sql` handle limited to a **single
underlying connection**. That single limit is what serialises writes:
there is no separate executor or lock arbitrating the write path, only
the fact that the hive's write handle can hand out one connection at a
time, so a second writer waits for the first to release it.
[*conn.a-second-writer-to-a-hive-waits-for-the-write-connection]

It also means the snapshot connections are genuinely separate handles
rather than borrowed pool entries, which is what keeps a long-running
read-only transaction from consuming a pool slot.
[*conn.a-snapshot-connection-never-consumes-a-read-pool-slot]

## What every connection carries [*conn.connection-state-is-established-once-when-the-connection-is-opened]

Connection state is established once, when the connection is opened
(§2.2):

- `journal_mode=wal` on the hive database, verified after being set.
- `foreign_keys=ON`.
- `busy_timeout=25000` — 25 seconds (§4.4).
- The volatile database attached as schema `volatile` (§3.3).

The volatile database's own journal mode is `memory`, not WAL.
[*conn.the-volatile-database-uses-journal-mode-memory-not-wal] The
persistent side therefore has multi-version concurrency — readers see a
consistent snapshot and do not block writers — and the volatile side does
not.
[*conn.persistent-readers-see-a-consistent-snapshot-and-do-not-block-writers]
§4.4 covers what follows from that.

The volatile *tables* are created only on the write connection.
[*conn.volatile-tables-are-created-only-on-the-write-connection] Read and
snapshot connections attach the same shared-cache URI and see the tables
through it.
[*conn.read-and-snapshot-connections-see-volatile-tables-through-the-shared-cache-uri]

## Which connection an operation uses

Nine mutating operations are routed to the write connection through the
transaction-aware write path: `RSI_CREATE_KEY`, `RSI_WRITE_KEY`,
`RSI_DROP_KEY`, `RSI_CREATE_ENTRY`, `RSI_HIDE_ENTRY`,
`RSI_DELETE_ENTRY`, `RSI_SET_VALUE`, `RSI_DELETE_VALUE_ENTRY`, and
`RSI_SET_BLANKET_TOMBSTONE`.
[*conn.nine-mutating-operations-route-through-the-transaction-aware-write-path]

Four read operations are routed to the read pool, or to the transaction's
connection when one is bound: `RSI_LOOKUP`, `RSI_ENUM_CHILDREN`,
`RSI_READ_KEY`, and `RSI_QUERY_VALUES`.
[*conn.four-read-operations-route-to-the-read-pool-or-the-bound-transaction]

`RSI_DELETE_LAYER` and `RSI_FLUSH` take the hive's write connection
directly rather than through the transaction-aware path, and open and
commit work of their own.
[*conn.delete-layer-and-flush-take-the-write-connection-directly] Neither
can join a caller's transaction: `RSI_FLUSH` checkpoints a hive, and
`RSI_DELETE_LAYER` spans every registered hive while a transaction binds
to exactly one.
[*conn.neither-delete-layer-nor-flush-can-join-a-callers-transaction]

They do still consult the request's transaction id, for the two answers
that do not require joining. A read-only transaction is declined with
`RSI_INVALID`, as it is on every other mutating path.
[*conn.delete-layer-and-flush-decline-a-read-only-transaction-with-rsi-invalid]
And because each hive allows a single write connection,
`RSI_DELETE_LAYER` declines with `RSI_TXN_BUSY` while any transaction
holds a pinned write connection rather than blocking on it forever — the
same answer `RSI_FLUSH` gives for its own hive.
[*conn.delete-layer-declines-with-rsi-txn-busy-rather-than-blocking]
