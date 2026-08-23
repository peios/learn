---
title: The Volatile Store
description: Volatile keys never reach the hive file, so each hive attaches a second in-memory database mirroring the persistent schema.
---

Volatile keys exist only for the lifetime of the running system, so they
never reach the hive's database file. Each hive instead gets a **second
SQLite database, held entirely in memory**, attached to its connections
under the schema name `volatile`:

```
file:<HiveName>_volatile?mode=memory&cache=shared
```

The hive name in the URI is the case-preserved name from the command
line, which is what keeps one hive's volatile database distinct from
another's.

## A mirror of the persistent schema

The volatile database carries the same four tables as the persistent one
— `keys`, `path_entries`, `[values]`, and `blanket_tombstones` — with
identical columns, identical primary keys, and the same partial
`idx_path_entries_target` index on non-HIDDEN path entries. Column
meanings are exactly those in §3.2.

There is one deliberate difference. In `volatile.keys` the `volatile`
column defaults to **1** rather than 0, and loregd writes 1 into it. Every
record in this database is volatile by definition, and the column carries
that fact back out in responses without a second lookup.

Because the two schemas are structurally identical, a query that needs
both stores is a `UNION ALL` across them rather than two queries merged
in application code:

```sql
SELECT 1 FROM main.keys WHERE guid = ?
UNION ALL
SELECT 1 FROM volatile.keys WHERE guid = ?
LIMIT 1
```

## Why this shape matters

Making the volatile store a SQLite database attached to the same
connection buys transactional behaviour for free. A SQLite transaction
spans every attached schema, so a transaction that mutates both
persistent and volatile data commits or rolls back as one unit, with no
separate mechanism to keep the two halves consistent. Volatile writes
inside a transaction are invisible to other readers until commit and
disappear on rollback for the same reason persistent ones do — see §4.3.

## Lifetime

A shared-cache in-memory database exists as long as at least one
connection has it open. The write connection creates the volatile tables
and holds the database; the read connections and any snapshot connection
attach the same URI and see the same data through the shared cache.

Nothing persists it, and nothing tries to. When loregd exits, the memory
goes with the process and every volatile key in every hive ceases to
exist. That is the entire meaning of volatility here, and it is why the
volatile tables are always empty at startup (§2.2, step 7).

## Which store an operation uses

For an operation naming a single key, the key's own storage decides:
loregd looks the GUID up in `main.keys` and `volatile.keys`, and whichever
holds it determines where the reads and writes go.

`RSI_CREATE_KEY` is the exception, because the key does not exist yet —
the volatile flag in the request decides which database receives it.

Two operations are not scoped to one store at all. `RSI_LOOKUP` and
`RSI_ENUM_CHILDREN` consult both and combine the results, because a
persistent parent may legitimately have volatile children. The reverse
does not arise: a persistent child beneath a volatile parent is forbidden
by the kernel's data model, so a volatile key's whole subtree is
volatile.
