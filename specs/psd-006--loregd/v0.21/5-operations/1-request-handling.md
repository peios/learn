---
title: Request Handling
---

This section describes how loregd handles each RSI operation. For
wire format details, see PSD-005 §11.3.

## Store routing and merging

Persistent data lives in the hive's SQLite database; volatile data
lives in the hive's in-process volatile store (§3.1.6). For
operations targeting a single key, the key's volatile flag selects
the store: loregd looks the GUID up in `main.keys` and in the
volatile store's keys map; whichever contains it determines where
the operation's reads and writes go.

For RSI_LOOKUP and RSI_ENUM_CHILDREN the operation is not scoped
to one store: loregd queries the main database and range-scans the
volatile store, then merges the two result sets in application
code before encoding the response. The SQL shown in the operation
sections below addresses the main database only; the volatile
counterpart of each query is a point lookup or prefix range scan
over the corresponding map, taken under the volatile store's read
lock (§4.1).

## Volatile writes and the transaction overlay

A mutating operation targeting volatile data executes on the
hive's write path (§4.1). Outside an explicit transaction, the
mutation is applied to the shared volatile store immediately,
under the store's write lock, before the response is sent — the
volatile analogue of an auto-committed SQLite statement.

Inside a read-write transaction, volatile mutations MUST NOT
become visible before the transaction commits, and MUST be
discarded if it aborts. loregd achieves this with a **transaction
overlay**: on the first volatile mutation within the transaction,
loregd clones the hive's volatile store into a private copy owned
by the transaction. All subsequent volatile reads and writes
within the transaction use the overlay (read-your-own-writes);
concurrent readers outside the transaction continue to read the
shared store and never observe uncommitted volatile state.

- **RSI_COMMIT_TRANSACTION:** loregd commits the SQLite
  transaction first. On success, it swaps the overlay in as the
  hive's volatile store (under the store's write lock) and
  responds RSI_OK. If the SQLite COMMIT fails, loregd returns
  RSI_STORAGE_ERROR, the transaction remains open, and the
  overlay is retained for retry or abort.
- **RSI_ABORT_TRANSACTION:** the overlay is discarded; the shared
  store was never touched.

The swap cannot lose concurrent updates: the transaction holds
the write path from its first mutating operation until commit or
abort, so no other volatile mutation can be applied to the shared
store between the clone and the swap. Cloning is cheap because
volatile stores are small (transient runtime state, empty at every
boot). The commit is not atomic across the two stores — a crash
after the SQLite COMMIT but before the swap loses the volatile
half — but this is unobservable: volatile data does not survive a
loregd exit under any circumstances.

## Deterministic response ordering

The enumeration and lookup results below are assembled by merging
main-database queries (written with no `ORDER BY`) with volatile
store range scans in application code. SQL without `ORDER BY` does
not guarantee row order, and the merge order is an implementation
accident, so the raw merged result is unordered.

loregd MUST NOT return that raw order. Per the source obligation in
PSD-005 §7.3 (Deterministic enumeration order), the entries within
each response MUST be in a stable, canonical order — LCS walks them by
dense index across repeated calls, so an unstable order makes that walk
duplicate or drop entries. Before encoding a response, loregd sorts:

- **RSI_ENUM_CHILDREN** children by folded child name; the per-layer
  entries of each child by (layer, sequence).
- **RSI_QUERY_VALUES** value entries by (folded value name, layer,
  sequence).
- **RSI_LOOKUP** path entries by (layer, sequence).

Key-metadata blocks are likewise emitted in ascending GUID order. This
ordering is a wire-stability guarantee only; it does not affect layer
resolution, which is order-independent (it selects a maximum).

## Transaction-aware request routing

Every RSI request carries a txn_id in the header. Routing depends on
the transaction's mode (read-write or read-only, established at
RSI_BEGIN_TRANSACTION) and whether it is yet bound to a connection.

**Read-write transactions.** When txn_id is non-zero and the
transaction is bound to a hive (a prior mutating operation established
the binding), loregd routes the request to that hive's write
path — even for read operations. This provides read-your-own-writes
isolation: persistent reads on the write connection see the SQLite
transaction's uncommitted writes, and volatile reads consult the
transaction overlay (if one exists) instead of the shared store.

When txn_id is non-zero but the read-write transaction is not yet
bound (no prior mutating operation), reads use the normal read
connection pool. There are no uncommitted writes to see.

**Read-only transactions.** A read-only transaction never accepts a
mutating operation: loregd MUST reject any mutating operation tagged
with a read-only txn_id with RSI_INVALID and MUST NOT mutate state
(PSD-005 §7.2). Reads tagged with a read-only txn_id observe a stable
point-in-time snapshot of persistent data. loregd binds the snapshot
lazily on the first read: it identifies the hive from the operation's
GUID, opens a dedicated connection (separate from the read pool so a
long-lived snapshot does not starve concurrent readers), and begins a
deferred SQLite read transaction on it. WAL mode fixes the snapshot at
that first read; all subsequent reads with the same txn_id reuse the
connection and observe the same snapshot. The snapshot is released by
RSI_ABORT_TRANSACTION (LCS does not commit read-only transactions).

When txn_id is zero, the request is dispatched normally: reads to
the read pool, writes to the write path.

## RSI_LOOKUP

Select all path entries for (parent_guid, child_name_folded)
across all layers, from the main database:

```sql
SELECT child_name, layer, target_type, target_guid, sequence
FROM path_entries
WHERE parent_guid = ? AND child_name_folded = ?
```

and merge with a range scan of the volatile path_entries map over
(parent_guid, child_name_folded, *).

For each unique target_guid (excluding HIDDEN entries), also fetch
the key metadata:

```sql
SELECT guid, sd, volatile, symlink, last_write_time
FROM keys WHERE guid IN (?)
```

with volatile-store keys looked up in the keys map (reported with
volatile=1).

Return all entries and metadata in the RSI response. loregd MUST
NOT filter or resolve layers.

## RSI_CREATE_ENTRY

The target store is determined by the target_guid's volatile flag
(store routing above). If the target key is persistent, insert a
path entry:

```sql
INSERT INTO path_entries
    (parent_guid, child_name, child_name_folded, layer,
     target_type, target_guid, sequence)
VALUES (?, ?, fold(?), ?, 0, ?, ?)
```

If the target key is volatile, insert the equivalent record into
the volatile path_entries map.

Return RSI_ALREADY_EXISTS if the (parent_guid, child_name_folded,
layer) key already exists in the target store.

## RSI_HIDE_ENTRY

Insert a HIDDEN path entry:

```sql
INSERT OR REPLACE INTO path_entries
    (parent_guid, child_name, child_name_folded, layer,
     target_type, target_guid, sequence)
VALUES (?, ?, fold(?), ?, 1, NULL, ?)
```

HIDDEN entries go in the main database unless the parent key is
volatile (in which case the entire subtree is volatile), where the
record is instead inserted-or-replaced in the volatile
path_entries map.

## RSI_DELETE_ENTRY

Delete a specific path entry from both stores:

```sql
DELETE FROM path_entries
WHERE parent_guid = ? AND child_name_folded = ? AND layer = ?
```

and remove (parent_guid, child_name_folded, layer) from the
volatile path_entries map. Idempotent — deleting a non-existent
entry is not an error.

## RSI_ENUM_CHILDREN

Query all children under a parent, across all layers, from the
main database:

```sql
SELECT child_name, child_name_folded, layer, target_type,
       target_guid, sequence
FROM path_entries WHERE parent_guid = ?
```

and merge with a range scan of the volatile path_entries map over
(parent_guid, *, *).

Collect unique target_guids and fetch metadata (same as
RSI_LOOKUP). Return the full result set.

## RSI_CREATE_KEY

If the volatile flag is set in the request, insert the key record
into the volatile keys map. Otherwise:

```sql
INSERT INTO keys
    (guid, name, name_folded, parent_guid, sd, volatile, symlink,
     last_write_time)
VALUES (?, ?, fold(?), ?, ?, 0, ?, ?)
```

The `last_write_time` field is not provided in the RSI request.
loregd sets it to the current wall-clock time (Unix nanoseconds)
at key creation.

Return RSI_ALREADY_EXISTS if the GUID already exists in either
store.

## RSI_READ_KEY

Fetch a key record by GUID:

```sql
SELECT name, parent_guid, sd, volatile, symlink, last_write_time
FROM keys WHERE guid = ?
```

If not found, look the GUID up in the volatile keys map (reported
with volatile=1). Return RSI_NOT_FOUND if the GUID does not exist
in either store.

## RSI_WRITE_KEY

Update mutable fields on a key. The target store is determined by
looking the GUID up in both stores. For a persistent key, loregd
builds a single UPDATE statement from the field_mask, setting only
the fields whose bits are present:

```sql
-- Combined update (example with both bits set):
UPDATE keys
SET sd = ?, last_write_time = ?
WHERE guid = ?
```

For a volatile key, loregd updates the same fields on the record
in the volatile keys map.

If no explicit transaction is active, the update is applied
atomically (a single auto-committed statement, or a single
critical section under the volatile write lock). If an explicit
transaction is active, it runs within that transaction (for
volatile keys, against the transaction overlay).

Return RSI_INVALID if the field_mask has any bits set at positions
other than 0 (SD) and 1 (last_write_time). Valid masks are 0x00,
0x01, 0x02, and 0x03. Any other value indicates an attempt to
modify immutable fields.

## RSI_DROP_KEY

Purge all data for a GUID across both stores. In the main
database, within one transaction:

```sql
DELETE FROM keys WHERE guid = ?;
DELETE FROM path_entries WHERE target_guid = ?;
DELETE FROM values WHERE key_guid = ?;
DELETE FROM blanket_tombstones WHERE key_guid = ?;
```

In the volatile store: remove the GUID from the keys map, scan
path_entries for records with this target_guid and remove them,
and remove the (key_guid, *) ranges from the values and
blanket_tombstones maps.

Idempotent — dropping a non-existent GUID is RSI_OK.

## RSI_QUERY_VALUES

Fetch all layer entries for a specific value (or all values if
query_all flag set) from the main database:

```sql
-- Single value:
SELECT name, layer, type, data, sequence
FROM values
WHERE key_guid = ? AND name_folded = ?

-- Query all (query_all flag set):
SELECT name, layer, type, data, sequence
FROM values WHERE key_guid = ?
```

merged with a range scan of the volatile values map over
(key_guid, name_folded, *) (single value) or (key_guid, *, *)
(query all).

Also return blanket tombstone state:

```sql
SELECT layer, sequence
FROM blanket_tombstones WHERE key_guid = ?
```

merged with a range scan of the volatile blanket_tombstones map
over (key_guid, *).

## RSI_SET_VALUE

The target store is determined by the key's volatile flag (look up
the GUID in both stores). If the key GUID does not exist in either
store, return RSI_NOT_FOUND.

For a persistent key, insert or replace a value entry:

```sql
INSERT OR REPLACE INTO values
    (key_guid, name, name_folded, layer, type, data, sequence)
VALUES (?, ?, fold(?), ?, ?, ?, ?)
```

For a volatile key, insert-or-replace the record in the volatile
values map.

**Conditional write (expected_sequence non-zero):** Before
writing, atomically check the current entry:

```sql
-- Within a single transaction:
SELECT sequence FROM values
WHERE key_guid = ? AND name_folded = ? AND layer = ?
```

If the row does not exist or the sequence does not match
expected_sequence, return RSI_CAS_FAILED without writing. For
persistent keys, SQLite's transaction isolation guarantees
atomicity within the write connection. For volatile keys, the
check-then-write is atomic because the write path is the sole
volatile mutator and holds the store's write lock across both
steps.

## RSI_DELETE_VALUE_ENTRY

Delete a specific value entry from both stores:

```sql
DELETE FROM values
WHERE key_guid = ? AND name_folded = ? AND layer = ?
```

and remove (key_guid, name_folded, layer) from the volatile
values map. Idempotent.

## RSI_SET_BLANKET_TOMBSTONE

Set or remove a blanket tombstone. The target store is determined
by the key's volatile flag. For a persistent key:

```sql
-- Set:
INSERT OR REPLACE INTO blanket_tombstones
    (key_guid, layer, sequence)
VALUES (?, ?, ?)

-- Remove:
DELETE FROM blanket_tombstones
WHERE key_guid = ? AND layer = ?
```

For a volatile key, insert-or-replace (or remove) the (key_guid,
layer) record in the volatile blanket_tombstones map.

## RSI_DELETE_LAYER

Remove all entries for a layer across all tables in both stores,
and report the GUIDs orphaned by the deletion. loregd computes the
orphan set in application code by combining both stores:

1. Collect the target GUIDs referenced by layer L: from the main
   database,

   ```sql
   SELECT DISTINCT target_guid FROM path_entries
   WHERE layer = ? AND target_type = 0
   ```

   plus a scan of the volatile path_entries map for records with
   this layer and target_type = 0.

2. Collect the target GUIDs referenced by any *other* layer, the
   same way (`WHERE layer != ? AND target_type = 0`, plus the
   volatile scan).

3. The orphan set is (1) minus (2).

Then delete, in the main database within one transaction:

```sql
BEGIN;
DELETE FROM path_entries WHERE layer = ?;
DELETE FROM values WHERE layer = ?;
DELETE FROM blanket_tombstones WHERE layer = ?;
COMMIT;
```

and in the volatile store: remove all path_entries, values, and
blanket_tombstones records with this layer.

The whole operation executes on the write path, so the two stores
cannot be mutated by anyone else between the orphan computation
and the deletions. Outside an explicit transaction, the volatile
deletions are applied after the SQLite COMMIT succeeds and before
the response is sent; the momentary non-atomicity between the two
stores is invisible to the caller and irrelevant across crashes
(volatile data does not survive a restart). Within a transaction,
the volatile deletions go to the transaction overlay as usual.

Return the set of orphaned GUIDs in the response.

## RSI_BEGIN_TRANSACTION

The request carries the txn_id and a transaction mode
(RSI_TXN_READ_WRITE = 0 or RSI_TXN_READ_ONLY = 1, PSD-005 §11.3).
loregd records the txn_id as a pending transaction of the requested
mode and returns RSI_OK immediately. No SQLite transaction is opened
at this point — connection binding is deferred. loregd supports both
modes (its SQLite backing provides both atomic read-write commits and
stable read-only snapshots), so it never returns
RSI_TXN_NOT_SUPPORTED.

**Read-write transaction lifecycle:**
- **First mutating op with this txn_id:** loregd identifies the
  target hive from the operation's GUID, acquires the hive's write
  path, opens `BEGIN IMMEDIATE` on its write connection, and
  associates the txn_id with the hive. If SQLITE_BUSY, return
  RSI_TXN_BUSY. If the operation targets volatile data, it
  additionally creates the transaction overlay (see above).
- **RSI_COMMIT_TRANSACTION:** `COMMIT` on the associated
  connection; on success, swap in the transaction overlay if one
  exists.
- **RSI_ABORT_TRANSACTION:** `ROLLBACK` on the associated
  connection; discard the transaction overlay if one exists.

**Read-only transaction lifecycle:**
- **First read op with this txn_id:** loregd identifies the target
  hive from the operation's GUID, opens a dedicated connection, and
  begins a deferred read transaction (`BEGIN DEFERRED`). The snapshot
  is fixed at this first read (see the routing rules above). Subsequent
  reads reuse the connection for a stable point-in-time view.
- **Any mutating op with this txn_id:** rejected with RSI_INVALID; no
  state is mutated (PSD-005 §7.2).
- **RSI_ABORT_TRANSACTION:** `ROLLBACK` and release the dedicated
  connection. This is how LCS releases the snapshot after
  REG_IOC_BACKUP completes or fails.
- **RSI_COMMIT_TRANSACTION:** LCS MUST NOT commit a read-only
  transaction. If one nonetheless arrives, loregd releases the
  snapshot and returns RSI_OK.

The read-only snapshot covers persistent data exactly (WAL fixes
it at the first read). The volatile store has no snapshot
mechanism: volatile reads within a read-only transaction observe
the live store under its read lock, so the point-in-time guarantee
is exact only for persistent data. This matches REG_IOC_BACKUP's
use of read-only snapshots over persistent hives.

## RSI_COMMIT_TRANSACTION

Commit the SQLite transaction:

```sql
COMMIT;
```

On success, swap in the transaction overlay if one exists (see
above), then return RSI_OK. If COMMIT fails (I/O error), return
RSI_STORAGE_ERROR. The transaction remains open — and the overlay
is retained — for retry or abort.

## RSI_ABORT_TRANSACTION

Roll back the SQLite transaction:

```sql
ROLLBACK;
```

Discard the transaction overlay if one exists, and disassociate
the txn_id from the write path. Always succeeds.

## RSI_FLUSH

The request carries a hive name. loregd maps the hive name to the
corresponding database connection and forces a WAL checkpoint:

```sql
PRAGMA wal_checkpoint(TRUNCATE);
```

Returns when the checkpoint completes and all persistent data is
durable. The volatile store has no durability and is unaffected by
RSI_FLUSH. If the hive name does not match any hive registered by
this loregd instance, return RSI_INVALID.
