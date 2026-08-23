---
title: Path Entry Operations
description: Lookup, create, hide, delete and enumerate — the operations over the per-layer entries that give a key its names.
---

## RSI_LOOKUP

Returns every layer's entry for one child name under one parent, together
with metadata for the keys those entries point at.

```sql
SELECT layer, target_type, target_guid, sequence
FROM main.path_entries
WHERE parent_guid = ? AND child_name_folded = ?
UNION ALL
SELECT layer, target_type, target_guid, sequence
FROM volatile.path_entries
WHERE parent_guid = ? AND child_name_folded = ?
```

HIDDEN entries are returned as entries but contribute no metadata GUID.
For each distinct non-HIDDEN `target_guid`, loregd fetches the key's
metadata — one query per GUID — and emits the blocks in ascending GUID
order (§5.2).

loregd does no layer filtering and no resolution: every entry it holds is
returned, and choosing between them is the kernel's job.

An unresolvable parent GUID returns `RSI_NOT_FOUND`.

If a path entry names a `target_guid` for which no key record exists, the
metadata fetch finds nothing and the whole request fails with
`RSI_STORAGE_ERROR`. This is reachable in ordinary operation: the kernel
issues `RSI_CREATE_ENTRY` before `RSI_CREATE_KEY`, so a lookup landing
between the two sees an entry whose key has not yet been written.

## RSI_CREATE_ENTRY

```sql
INSERT INTO path_entries
    (parent_guid, child_name, child_name_folded, layer,
     target_type, target_guid, sequence)
VALUES (?, ?, fold(?), ?, 0, ?, ?)
```

The target table follows the child key's volatile flag (§5.1); a child GUID
in neither store lands in the persistent table.

`RSI_ALREADY_EXISTS` comes from the target table's primary key on
`(parent_guid, child_name_folded, layer)`. Since that key is per-schema, an
identical entry in the *other* store does not collide, and the same triple
can come to exist in both — in which case both rows are returned by lookups
and enumerations (§5.1).

An unresolvable parent GUID returns `RSI_NOT_FOUND`.

## RSI_HIDE_ENTRY

Writes a tombstone that masks the same name in lower layers:

```sql
INSERT OR REPLACE INTO path_entries
    (parent_guid, child_name, child_name_folded, layer,
     target_type, target_guid, sequence)
VALUES (?, ?, fold(?), ?, 1, NULL, ?)
```

`target_type` is 1 and `target_guid` is null. The target table follows the
**parent** key's volatile flag, because a volatile parent's entire subtree
is volatile. A parent GUID in neither store returns `RSI_NOT_FOUND`.

## RSI_DELETE_ENTRY

Removes one layer's entry for one name, from both stores:

```sql
DELETE FROM path_entries
WHERE parent_guid = ? AND child_name_folded = ? AND layer = ?
```

No rows-affected check is made, so deleting an entry that is not there
succeeds. A parent GUID that resolves to no hive returns
`RSI_NOT_FOUND` rather than succeeding.

## RSI_ENUM_CHILDREN

Returns every layer's entry for every child under a parent:

```sql
SELECT child_name, child_name_folded, layer, target_type,
       target_guid, sequence
FROM main.path_entries WHERE parent_guid = ?
UNION ALL
SELECT child_name, child_name_folded, layer, target_type,
       target_guid, sequence
FROM volatile.path_entries WHERE parent_guid = ?
```

Rows are grouped by folded child name into one block per child, each
carrying that child's per-layer entries. Metadata for the distinct
non-HIDDEN target GUIDs is fetched and emitted exactly as for
`RSI_LOOKUP`, and the same `RSI_STORAGE_ERROR` arises for an entry whose
key record does not yet exist.

Ordering, and the treatment of two rows whose folded names match but whose
stored case differs, are covered in §5.2.
