---
title: Concurrency Model
---

loregd uses SQLite's WAL (Write-Ahead Logging) mode for each hive
database. WAL mode enables concurrent reads with serialised writes.

## Connection pool

For each hive database, loregd maintains:

- **One write path.** All mutating RSI operations
  (RSI_CREATE_KEY, RSI_CREATE_ENTRY, RSI_SET_VALUE,
  RSI_DELETE_ENTRY, RSI_HIDE_ENTRY, RSI_DELETE_VALUE_ENTRY,
  RSI_WRITE_KEY, RSI_DROP_KEY, RSI_SET_BLANKET_TOMBSTONE,
  RSI_DELETE_LAYER, RSI_FLUSH) are dispatched to a single per-hive
  write path: the executor that owns the hive's one write
  connection and is the sole mutator of the hive's volatile store.
  SQLite's single-writer model serialises persistent writes at the
  database level; write-path ownership serialises volatile writes
  with them. A mutating operation targeting a volatile key does
  not touch SQLite, but it still executes on the write path.

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

**Volatile store concurrency.** Each hive's volatile store is
guarded by a readers–writer lock: any number of concurrent
readers, or one writer. Read operations (from the read pool or a
read-only transaction) take the read lock only for the duration of
their map lookups and range scans. All mutations are applied by
the write path, so there is never more than one volatile writer
per hive, and the write lock is held only while applying a
mutation (or swapping in a transaction overlay, §5.1).

Volatile reads are not snapshot-isolated: there is no MVCC for the
volatile store, and a reader observes the live store at the moment
it takes the read lock. This is coarser than WAL's snapshot
isolation on the persistent side. In practice, volatile key
contention is low (volatile keys are typically transient runtime
state, not hot-path configuration), so the difference is
negligible.

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
   and caches the result. Volatile keys need no database probe:
   they exist only for the lifetime of this loregd process, so
   their GUIDs were cached when they were created. For RSI_LOOKUP
   and RSI_ENUM_CHILDREN, the parent_guid identifies the hive. For
   all other operations, the key GUID identifies it.

2. **Classify as read or write.** Read operations go to the read
   pool. Write operations go to the write path.

3. **Transaction routing.** RSI_BEGIN_TRANSACTION does not require
   hive identification — loregd records the txn_id and its mode
   (read-write or read-only) and returns RSI_OK. For subsequent
   operations with a non-zero txn_id:
   - **Read-write, first mutating operation:** identify the target
     hive from the operation's GUID, acquire the write path for
     that hive, and begin a SQLite transaction (BEGIN IMMEDIATE).
     Associate the txn_id with this hive's write path. If
     SQLITE_BUSY, return RSI_TXN_BUSY. This applies equally when
     the first mutating operation targets a volatile key: the
     SQLite transaction brackets any subsequent persistent writes,
     and volatile mutations accumulate in the transaction overlay
     (§5.1).
   - **Read-write, subsequent operations:** verify the txn_id is
     associated with the same hive. LCS enforces hive-scoping at the
     kernel level, so loregd should never receive a cross-hive
     operation within a transaction. Read operations use the write
     connection and, for volatile data, the transaction overlay
     (read-your-own-writes isolation).
   - **Read-only, first read operation:** identify the target hive,
     acquire a dedicated connection (not from the read pool), and
     begin a deferred read transaction (BEGIN DEFERRED) to pin a
     point-in-time snapshot. Subsequent reads reuse this connection.
   - **Read-only, mutating operation:** reject with RSI_INVALID and
     do not mutate (PSD-005 §7.2).

4. **Execute and respond.** Process the operation against the
   appropriate store, construct the RSI response, and write it
   to /dev/pkm_registry.

## Write serialisation

SQLite WAL mode serialises writers at the database level, and the
write path serialises volatile mutations with them. If two RSI
write requests arrive concurrently for the same hive:

- If no transaction is active, each write auto-commits
  independently. The second write blocks briefly while the first
  completes (for persistent writes, while SQLite acquires the
  write lock), then proceeds. No RSI_TXN_BUSY.

- If an explicit transaction holds the write path, non-
  transactional writes — including volatile-only writes — wait for
  the transaction to commit or abort. If the wait exceeds the busy
  timeout, loregd returns RSI_TXN_BUSY.

loregd configures SQLite's busy timeout to a compiled-in default
of 25000 milliseconds (25 seconds), shorter than LCS's default
RequestTimeoutMs (30 seconds). This ensures loregd responds with
RSI_TXN_BUSY before LCS times out the caller. loregd MUST apply
the same 25-second bound when a volatile-only write waits to
acquire the write path, since that wait never reaches SQLite's
timeout machinery.

## Cross-hive transactions

Transactions are hive-scoped. LCS enforces this at the kernel
level — if a transaction bound to Machine\ receives an operation
targeting Users\, LCS returns EXDEV to the caller before the
request reaches loregd. loregd never receives cross-hive
operations within a transaction and does not need to handle this
case.
