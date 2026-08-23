---
title: Layer and Maintenance Operations
description: Delete-layer and flush — the two operations that ignore the request's transaction id and take the write connection directly.
---

Neither operation in this section consults the request's transaction id
(§4.1). Both take the hive's write connection directly and commit work of
their own.

## RSI_DELETE_LAYER

Removes every entry belonging to one layer and reports the keys that the
removal left unreferenced.

The operation is applied to **every registered hive**, not to one
identified from the request, and the per-hive orphan sets are
concatenated into a single response array.

For each hive, inside one `BEGIN IMMEDIATE` transaction, loregd first
computes the orphan set and then deletes:

```sql
-- GUIDs referenced by the layer being removed
SELECT DISTINCT target_guid FROM main.path_entries
WHERE layer = ? AND target_type = 0
UNION
SELECT DISTINCT target_guid FROM volatile.path_entries
WHERE layer = ? AND target_type = 0
```

minus the GUIDs referenced by any *other* layer, gathered the same way
with `layer != ?`. What remains is reachable only through the layer being
deleted, and is therefore orphaned by it.

```sql
DELETE FROM path_entries       WHERE layer = ?;
DELETE FROM [values]           WHERE layer = ?;
DELETE FROM blanket_tombstones WHERE layer = ?;
```

Both schemas are covered, and all six deletions run inside the same
transaction as the orphan computation, so nothing can be inserted between
the two steps. The orphaned GUIDs are evicted from the hive cache (§4.2)
and returned to the caller.

The response array's order is not stable across calls (§5.2).

Every failure is reported as `RSI_STORAGE_ERROR`; busy errors are not
classified separately, unlike the other write paths.

## RSI_FLUSH

Forces the hive's write-ahead log to be checkpointed so that all
persistent data is durable on disk:

```sql
PRAGMA wal_checkpoint(TRUNCATE)
```

The request carries a hive **name** rather than a GUID. It is matched
case-insensitively against the registered hives by folded name (§3.4); a
name matching none returns `RSI_INVALID`.

Two conditions return `RSI_TXN_BUSY` instead of checkpointing:

- Any transaction is currently bound to the hive. A checkpoint on a
  connection already held by a transaction would deadlock, so loregd
  declines immediately rather than waiting (§4.4).
- The checkpoint itself reports that it could not complete because the
  database was busy.

The volatile store has no durability and is unaffected: nothing is
flushed, and nothing needs to be.
