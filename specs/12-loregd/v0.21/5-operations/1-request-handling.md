---
title: Request Handling
---

This section describes how loregd handles each RSI operation. For
wire format details, see the RSI Wire Format appendix of the LCS
v0.21 specification.

## Transaction-aware request routing

Every RSI request carries a txn_id in the header. When txn_id is
non-zero and the transaction is bound to a hive (a prior mutating
operation established the binding), loregd routes the request to
that hive's write connection — even for read operations. This
provides read-your-own-writes isolation: reads within a transaction
see the transaction's uncommitted writes.

When txn_id is non-zero but the transaction is not yet bound (no
prior mutating operation), reads use the normal read connection pool.
There are no uncommitted writes to see.

When txn_id is zero, the request is dispatched normally: reads to
the read pool, writes to the write connection.

## RSI_LOOKUP

Query: select all path entries for (parent_guid, child_name_folded)
across all layers, from both main and volatile databases.

```sql
SELECT child_name, layer, target_type, target_guid, sequence
FROM main.path_entries
WHERE parent_guid = ? AND child_name_folded = ?
UNION ALL
SELECT child_name, layer, target_type, target_guid, sequence
FROM volatile.path_entries
WHERE parent_guid = ? AND child_name_folded = ?
```

For each unique target_guid (excluding HIDDEN entries), also fetch
the key metadata:

```sql
SELECT guid, sd, volatile, symlink, last_write_time
FROM main.keys WHERE guid IN (?)
UNION ALL
SELECT guid, sd, volatile, symlink, last_write_time
FROM volatile.keys WHERE guid IN (?)
```

Return all entries and metadata in the RSI response. loregd MUST
NOT filter or resolve layers.

## RSI_CREATE_ENTRY

Insert a path entry:

```sql
INSERT INTO <main|volatile>.path_entries
    (parent_guid, child_name, child_name_folded, layer,
     target_type, target_guid, sequence)
VALUES (?, ?, fold(?), ?, 0, ?, ?)
```

The target database (main or volatile) is determined by looking
up the target_guid in both databases to find the key's volatile
flag. If the key is volatile, the path entry goes in the volatile
database. If persistent, it goes in main.

Return RSI_ALREADY_EXISTS if the (parent_guid, child_name_folded,
layer) primary key already exists.

## RSI_HIDE_ENTRY

Insert a HIDDEN path entry:

```sql
INSERT OR REPLACE INTO <main|volatile>.path_entries
    (parent_guid, child_name, child_name_folded, layer,
     target_type, target_guid, sequence)
VALUES (?, ?, fold(?), ?, 1, NULL, ?)
```

HIDDEN entries go in the main database unless the parent key is
volatile (in which case the entire subtree is volatile).

## RSI_DELETE_ENTRY

Delete a specific path entry:

```sql
DELETE FROM main.path_entries
WHERE parent_guid = ? AND child_name_folded = ? AND layer = ?;
DELETE FROM volatile.path_entries
WHERE parent_guid = ? AND child_name_folded = ? AND layer = ?;
```

Execute against both databases. Idempotent — deleting a
non-existent entry is not an error.

## RSI_ENUM_CHILDREN

Query all children under a parent, across all layers, from both
databases:

```sql
SELECT child_name, child_name_folded, layer, target_type,
       target_guid, sequence
FROM main.path_entries WHERE parent_guid = ?
UNION ALL
SELECT child_name, child_name_folded, layer, target_type,
       target_guid, sequence
FROM volatile.path_entries WHERE parent_guid = ?
```

Collect unique target_guids and fetch metadata (same as
RSI_LOOKUP). Return the full result set.

## RSI_CREATE_KEY

Insert a new key record:

```sql
INSERT INTO <main|volatile>.keys
    (guid, name, name_folded, parent_guid, sd, volatile, symlink,
     last_write_time)
VALUES (?, ?, fold(?), ?, ?, ?, ?, ?)
```

The `last_write_time` field is not provided in the RSI request.
loregd sets it to the current wall-clock time (Unix nanoseconds)
at key creation.

Target database: volatile database if the volatile flag is set,
main database otherwise.

Return RSI_ALREADY_EXISTS if the GUID already exists.

## RSI_READ_KEY

Fetch a key record by GUID:

```sql
SELECT name, parent_guid, sd, volatile, symlink, last_write_time
FROM main.keys WHERE guid = ?
UNION ALL
SELECT name, parent_guid, sd, volatile, symlink, last_write_time
FROM volatile.keys WHERE guid = ?
```

Return the first match. Return RSI_NOT_FOUND if the GUID does not
exist in either database.

## RSI_WRITE_KEY

Update mutable fields on a key:

loregd builds a single UPDATE statement from the field_mask,
setting only the fields whose bits are present:

```sql
-- Combined update (example with both bits set):
UPDATE <main|volatile>.keys
SET sd = ?, last_write_time = ?
WHERE guid = ?
```

If no explicit transaction is active, this single statement is
auto-committed atomically. If an explicit transaction is active,
it runs within that transaction.

Determine which database by querying both for the GUID.
Return RSI_INVALID if the field_mask has any bits set at positions
other than 0 (SD) and 1 (last_write_time). Valid masks are 0x00,
0x01, 0x02, and 0x03. Any other value indicates an attempt to
modify immutable fields.

## RSI_DROP_KEY

Purge all data for a GUID across both databases:

```sql
DELETE FROM main.keys WHERE guid = ?;
DELETE FROM main.path_entries WHERE target_guid = ?;
DELETE FROM main.values WHERE key_guid = ?;
DELETE FROM main.blanket_tombstones WHERE key_guid = ?;
DELETE FROM volatile.keys WHERE guid = ?;
DELETE FROM volatile.path_entries WHERE target_guid = ?;
DELETE FROM volatile.values WHERE key_guid = ?;
DELETE FROM volatile.blanket_tombstones WHERE key_guid = ?;
```

Idempotent — dropping a non-existent GUID is RSI_OK.

## RSI_QUERY_VALUES

Fetch all layer entries for a specific value (or all values if
query_all flag set):

```sql
-- Single value:
SELECT name, layer, type, data, sequence
FROM main.values
WHERE key_guid = ? AND name_folded = ?
UNION ALL
SELECT name, layer, type, data, sequence
FROM volatile.values
WHERE key_guid = ? AND name_folded = ?

-- Query all (query_all flag set):
SELECT name, layer, type, data, sequence
FROM main.values WHERE key_guid = ?
UNION ALL
SELECT name, layer, type, data, sequence
FROM volatile.values WHERE key_guid = ?
```

Also return blanket tombstone state:

```sql
SELECT layer, sequence
FROM main.blanket_tombstones WHERE key_guid = ?
UNION ALL
SELECT layer, sequence
FROM volatile.blanket_tombstones WHERE key_guid = ?
```

## RSI_SET_VALUE

Insert or replace a value entry:

```sql
INSERT OR REPLACE INTO <main|volatile>.values
    (key_guid, name, name_folded, layer, type, data, sequence)
VALUES (?, ?, fold(?), ?, ?, ?, ?)
```

**Conditional write (expected_sequence non-zero):** Before
writing, atomically check the current entry:

```sql
-- Within a single transaction:
SELECT sequence FROM <main|volatile>.values
WHERE key_guid = ? AND name_folded = ? AND layer = ?
```

If the row does not exist or the sequence does not match
expected_sequence, return RSI_CAS_FAILED without writing. SQLite's
transaction isolation guarantees atomicity within the write
connection.

Target database: determined by the key's volatile flag (look up
the GUID in both databases). If the key GUID does not exist in
either database, return RSI_NOT_FOUND.

## RSI_DELETE_VALUE_ENTRY

Delete a specific value entry:

```sql
DELETE FROM main.values
WHERE key_guid = ? AND name_folded = ? AND layer = ?;
DELETE FROM volatile.values
WHERE key_guid = ? AND name_folded = ? AND layer = ?;
```

Idempotent.

## RSI_SET_BLANKET_TOMBSTONE

Set or remove a blanket tombstone:

```sql
-- Set:
INSERT OR REPLACE INTO <main|volatile>.blanket_tombstones
    (key_guid, layer, sequence)
VALUES (?, ?, ?)

-- Remove:
DELETE FROM <main|volatile>.blanket_tombstones
WHERE key_guid = ? AND layer = ?
```

Target database: determined by the key's volatile flag.

## RSI_DELETE_LAYER

Remove all entries for a layer across all tables in both databases:

```sql
BEGIN;

-- Capture orphaned GUIDs before deletion (both databases)
SELECT DISTINCT target_guid FROM (
    SELECT target_guid FROM main.path_entries
    WHERE layer = ? AND target_type = 0
    UNION ALL
    SELECT target_guid FROM volatile.path_entries
    WHERE layer = ? AND target_type = 0
) AS deleted_entries
WHERE target_guid NOT IN (
    SELECT target_guid FROM main.path_entries
    WHERE layer != ? AND target_type = 0
    UNION
    SELECT target_guid FROM volatile.path_entries
    WHERE layer != ? AND target_type = 0
);

DELETE FROM main.path_entries WHERE layer = ?;
DELETE FROM main.values WHERE layer = ?;
DELETE FROM main.blanket_tombstones WHERE layer = ?;
DELETE FROM volatile.path_entries WHERE layer = ?;
DELETE FROM volatile.values WHERE layer = ?;
DELETE FROM volatile.blanket_tombstones WHERE layer = ?;

COMMIT;
```

Return the set of orphaned GUIDs in the response.

## RSI_BEGIN_TRANSACTION

Record the txn_id as a pending transaction. No SQLite transaction
is opened at this point — hive binding and BEGIN IMMEDIATE are
deferred until the first mutating operation arrives with this
txn_id (see the Transaction routing section of the Concurrency
Model). Return RSI_OK immediately.

The actual SQLite transaction lifecycle:
- **First mutating op with this txn_id:** loregd identifies the
  target hive from the operation's GUID, opens `BEGIN IMMEDIATE`
  on that hive's write connection, and associates the txn_id with
  the hive. If SQLITE_BUSY, return RSI_TXN_BUSY.
- **RSI_COMMIT_TRANSACTION:** `COMMIT` on the associated
  connection.
- **RSI_ABORT_TRANSACTION:** `ROLLBACK` on the associated
  connection.

## RSI_COMMIT_TRANSACTION

Commit the SQLite transaction:

```sql
COMMIT;
```

Return RSI_OK on success. If COMMIT fails (I/O error), return
RSI_STORAGE_ERROR. The transaction remains open for retry or
abort.

## RSI_ABORT_TRANSACTION

Roll back the SQLite transaction:

```sql
ROLLBACK;
```

Disassociate the txn_id from the write connection. Always succeeds.

## RSI_FLUSH

The request carries a hive name. loregd maps the hive name to the
corresponding database connection and forces a WAL checkpoint:

```sql
PRAGMA wal_checkpoint(TRUNCATE);
```

Returns when the checkpoint completes and all data is durable.
If the hive name does not match any hive registered by this loregd
instance, return RSI_INVALID.
