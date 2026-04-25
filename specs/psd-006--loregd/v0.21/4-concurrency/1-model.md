---
title: Concurrency Model
---

loregd uses SQLite's WAL (Write-Ahead Logging) mode for each hive
database. WAL mode enables concurrent reads with serialised writes.

## Connection pool

For each hive database, loregd maintains:

- **One write connection.** All mutating RSI operations
  (RSI_CREATE_KEY, RSI_CREATE_ENTRY, RSI_SET_VALUE,
  RSI_DELETE_ENTRY, RSI_HIDE_ENTRY, RSI_DELETE_VALUE_ENTRY,
  RSI_WRITE_KEY, RSI_DROP_KEY, RSI_SET_BLANKET_TOMBSTONE,
  RSI_DELETE_LAYER, RSI_FLUSH) are dispatched to this connection.
  SQLite's single-writer model serialises all writes at the
  database level.

- **Multiple read connections.** Read-only RSI operations
  (RSI_LOOKUP, RSI_READ_KEY, RSI_QUERY_VALUES,
  RSI_ENUM_CHILDREN) are dispatched to a pool of read connections.
  WAL mode allows concurrent readers that do not block writers
  and are not blocked by writers. Each reader sees a consistent
  snapshot from the point at which its transaction began.

The number of read connections is a compiled-in default. A
reasonable starting point is the number of available CPU cores,
capped at a maximum (e.g., 16). This is not configurable via the
registry (loregd has no self-configuration).

**Volatile store concurrency.** The volatile store uses SQLite
shared-cache mode, not WAL mode (in-memory databases do not
support WAL). Shared-cache uses table-level locking: concurrent
reads are allowed, but a write to a volatile table blocks readers
of that table and vice versa. This is coarser than WAL's MVCC
snapshot isolation. In practice, volatile key contention is low
(volatile keys are typically transient runtime state, not hot-path
configuration), so the difference is negligible.

## Request dispatch

RSI requests arrive multiplexed on the /dev/pkm_registry fd. Each
request carries a request_id and (for requests within a
transaction) a txn_id in the header.

loregd dispatches requests as follows:

1. **Identify the target hive.** The request's key GUID or parent
   GUID determines the hive. loregd maintains an in-memory
   GUID→hive cache, seeded at startup with each hive's root GUID.
   On RSI_CREATE_KEY, loregd adds the new GUID to the cache. On
   RSI_DROP_KEY, loregd removes it. For a GUID not in the cache
   (e.g., after restart with existing data), loregd queries each
   hive database (`SELECT 1 FROM keys WHERE guid = ? LIMIT 1`)
   and caches the result. For RSI_LOOKUP and RSI_ENUM_CHILDREN,
   the parent_guid identifies the hive. For all other operations,
   the key GUID identifies it.

2. **Classify as read or write.** Read operations go to the read
   pool. Write operations go to the write connection.

3. **Transaction routing.** RSI_BEGIN_TRANSACTION does not require
   hive identification — loregd records the txn_id and returns
   RSI_OK. For subsequent operations with a non-zero txn_id:
   - For the first mutating operation: identify the target hive
     from the operation's GUID, acquire the write connection for
     that hive, and begin a SQLite transaction (BEGIN IMMEDIATE).
     Associate the txn_id with this hive's write connection. If
     SQLITE_BUSY, return RSI_TXN_BUSY.
   - For subsequent operations: verify the txn_id is associated
     with the same hive. LCS enforces hive-scoping at the kernel
     level, so loregd should never receive a cross-hive operation
     within a transaction.
   - For read operations within a transaction: use the write
     connection (to get read-your-own-writes isolation).

4. **Execute and respond.** Process the operation against the
   appropriate database, construct the RSI response, and write it
   to /dev/pkm_registry.

## Write serialisation

SQLite WAL mode serialises writers at the database level. If two
RSI write requests arrive concurrently for the same hive:

- If no transaction is active, each write auto-commits
  independently. The second write blocks briefly while SQLite
  acquires the write lock, then proceeds. No RSI_TXN_BUSY.

- If an explicit transaction holds the write connection, non-
  transactional writes wait for the transaction to commit or
  abort. If the wait exceeds SQLite's busy timeout, loregd
  returns RSI_TXN_BUSY.

loregd configures SQLite's busy timeout to a compiled-in default
of 25000 milliseconds (25 seconds), shorter than LCS's default
RequestTimeoutMs (30 seconds). This ensures loregd responds with
RSI_TXN_BUSY before LCS times out the caller.

## Cross-hive transactions

Transactions are hive-scoped. LCS enforces this at the kernel
level — if a transaction bound to Machine\ receives an operation
targeting Users\, LCS returns EXDEV to the caller before the
request reaches loregd. loregd never receives cross-hive
operations within a transaction and does not need to handle this
case.
