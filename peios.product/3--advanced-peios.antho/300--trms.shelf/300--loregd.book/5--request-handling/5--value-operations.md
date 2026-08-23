---
title: Value Operations
description: Querying, setting and deleting value entries, conditional writes, and setting a blanket tombstone.
---

## RSI_QUERY_VALUES

Returns every layer's entry for one value, or for all of a key's values
when the request sets the query-all flag:

```sql
-- single value
SELECT name, layer, type, data, sequence
FROM main.[values] WHERE key_guid = ? AND name_folded = ?
UNION ALL
SELECT name, layer, type, data, sequence
FROM volatile.[values] WHERE key_guid = ? AND name_folded = ?

-- query all
SELECT name, layer, type, data, sequence
FROM main.[values] WHERE key_guid = ?
UNION ALL
SELECT name, layer, type, data, sequence
FROM volatile.[values] WHERE key_guid = ?
```

The response also carries the key's blanket-tombstone state:

```sql
SELECT layer, sequence
FROM main.blanket_tombstones WHERE key_guid = ?
UNION ALL
SELECT layer, sequence
FROM volatile.blanket_tombstones WHERE key_guid = ?
```

Value entries are sorted; blanket tombstones are not (§5.2).

An unresolvable GUID returns `RSI_NOT_FOUND`. An existing key with no
values returns `RSI_OK` with empty arrays.

## RSI_SET_VALUE

The key's volatile flag selects the store; a key GUID in neither store
returns `RSI_NOT_FOUND`.

```sql
INSERT OR REPLACE INTO [values]
    (key_guid, name, name_folded, layer, type, data, sequence)
VALUES (?, ?, fold(?), ?, ?, ?, ?)
```

### Conditional writes

When the request carries a non-zero `expected_sequence`, the write is a
compare-and-swap. loregd reads the current entry's sequence and writes only
if it matches:

```sql
SELECT sequence FROM [values]
WHERE key_guid = ? AND name_folded = ? AND layer = ?
```

If the row is absent, or its sequence differs, the operation returns
`RSI_CAS_FAILED` and writes nothing.

Outside a transaction, the check and the write are wrapped in their own
`BEGIN IMMEDIATE` transaction so no other writer can interleave; if that
transaction cannot begin because the database is busy, the operation
returns `RSI_TXN_BUSY`. Inside a transaction, the caller's transaction
already provides the isolation.

## RSI_DELETE_VALUE_ENTRY

Removes one layer's entry for one value, from both stores:

```sql
DELETE FROM [values]
WHERE key_guid = ? AND name_folded = ? AND layer = ?
```

No rows-affected check, so deleting an absent entry succeeds. A GUID that
resolves to no hive returns `RSI_NOT_FOUND`.

## RSI_SET_BLANKET_TOMBSTONE

Sets or clears the tombstone that masks every value a key holds in lower
layers. The key's volatile flag selects the store, and a GUID in neither
returns `RSI_NOT_FOUND`.

```sql
-- set
INSERT OR REPLACE INTO blanket_tombstones (key_guid, layer, sequence)
VALUES (?, ?, ?)

-- clear
DELETE FROM blanket_tombstones WHERE key_guid = ? AND layer = ?
```
