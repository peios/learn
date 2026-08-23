---
title: Key Operations
description: The four key operations and the SQL behind each — create, read, write and drop.
---

## RSI_CREATE_KEY

The request's volatile flag selects the target table (§5.1). For a
persistent key:

```sql
INSERT INTO keys
    (guid, name, name_folded, parent_guid, sd, volatile, symlink,
     last_write_time)
VALUES (?, ?, fold(?), ?, ?, 0, ?, ?)
```

`last_write_time` is not carried in the request. loregd sets it to the
current wall-clock time in Unix nanoseconds at insertion.

Uniqueness comes from the target table's primary key on `guid`, surfaced
as `RSI_ALREADY_EXISTS`. Because that key is per-schema, a GUID already
present in the *other* store does not collide: creating a persistent key
whose GUID exists in `volatile.keys` succeeds, and the GUID then exists in
both. Subsequent metadata reads resolve such a GUID to the `main` row,
since the reading query takes the first row of a `UNION ALL` that puts
`main` first.

The new GUID is added to the hive cache immediately, before the enclosing
transaction commits, with an abort hook to remove it if that transaction
rolls back (§4.2).

An unresolvable parent GUID returns `RSI_NOT_FOUND`, after a fallback
check of the registered hives' root GUIDs.

## RSI_READ_KEY

```sql
SELECT name, parent_guid, sd, volatile, symlink, last_write_time
FROM main.keys WHERE guid = ?
UNION ALL
SELECT name, parent_guid, sd, volatile, symlink, last_write_time
FROM volatile.keys WHERE guid = ?
LIMIT 1
```

`RSI_NOT_FOUND` if the GUID is in neither store, and likewise if it
resolves to no hive. The `volatile` field in the response is the stored
column value.

## RSI_WRITE_KEY

Updates the two mutable fields of a key, selected by a field mask:

| Bit | Value | Field |
|---|---|---|
| 0 | `0x01` | `sd` |
| 1 | `0x02` | `last_write_time` |

Valid masks are therefore `0x00`, `0x01`, `0x02` and `0x03`. Any other bit
set returns `RSI_INVALID` — it indicates an attempt to modify an immutable
field.

loregd builds one `UPDATE` from the mask, setting only the named fields:

```sql
-- mask 0x03
UPDATE keys SET sd = ?, last_write_time = ? WHERE guid = ?
```

A mask of `0x00` names no fields and acts as an existence check, returning
`RSI_OK` or `RSI_NOT_FOUND`. An update that matches no row also returns
`RSI_NOT_FOUND`.

Outside a transaction the update is a single auto-committed statement.
Inside one it runs on the transaction's connection.

## RSI_DROP_KEY

Purges every trace of a GUID from both stores — four tables in each
schema:

```sql
DELETE FROM keys               WHERE guid = ?;
DELETE FROM path_entries       WHERE target_guid = ?;
DELETE FROM [values]           WHERE key_guid = ?;
DELETE FROM blanket_tombstones WHERE key_guid = ?;
```

Outside a transaction, the eight statements are wrapped in a
`BEGIN IMMEDIATE` transaction of their own so the purge is atomic. Inside
one, they run on the transaction's connection.

Dropping a GUID that does not exist returns `RSI_OK`; so does one that
resolves to no hive. The operation is idempotent. The GUID is evicted from
the hive cache (§4.2).
