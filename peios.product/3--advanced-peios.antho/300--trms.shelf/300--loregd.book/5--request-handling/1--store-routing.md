---
title: Store Routing
description: Persistent data in the main schema and volatile data in the attached one — how an operation picks, and the ones that span both.
---

Persistent data lives in the hive database's `main` schema; volatile data
lives in the attached `volatile` schema (§3.3). Most operations act on one
of the two, and loregd has to decide which before it can run any SQL.

## Operations naming one key

For an operation that names a single key, the key's own `volatile` column
selects the store. loregd reads it with one statement across both schemas:

```sql
SELECT volatile FROM main.keys WHERE guid = ?
UNION ALL
SELECT volatile FROM volatile.keys WHERE guid = ?
LIMIT 1
```

A GUID present in neither produces `RSI_NOT_FOUND` for most operations.

Note that routing follows the **column value**, not which table the row
came from. Rows loregd writes are always consistent about this — a row in
`volatile.keys` carries `volatile = 1`, a row in `main.keys` carries 0 —
so the distinction only matters if a database were modified externally.

`RSI_CREATE_KEY` cannot consult a key that does not exist yet, so it
routes on the volatile flag carried in the request instead.

`RSI_CREATE_ENTRY` routes on the volatile flag of the **child** key the
entry points at. When that child GUID is present in neither store, the
entry is written to the persistent table.

`RSI_HIDE_ENTRY` routes on the **parent** key, since a HIDDEN entry
belongs to the parent's child list and a volatile parent's whole subtree
is volatile.

## Operations spanning both stores

`RSI_LOOKUP`, `RSI_ENUM_CHILDREN`, `RSI_READ_KEY` and `RSI_QUERY_VALUES`
are not scoped to one store: a persistent parent may have volatile
children, and a persistent key may have volatile-store rows beneath it.
Each issues a single `UNION ALL` statement over the two schemas rather
than querying them separately, so the merge happens inside SQLite.

Nothing de-duplicates across the two stores. The primary keys that make
`(parent_guid, child_name_folded, layer)` unique apply *per schema*, so if
the same triple exists in both, both rows appear in the response. The same
holds for value entries keyed on `(key_guid, name_folded, layer)`.

The deletions — `RSI_DELETE_ENTRY`, `RSI_DELETE_VALUE_ENTRY` and
`RSI_DROP_KEY` — do not route at all. They delete from both schemas
unconditionally.
