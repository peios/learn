---
title: Schema Version
description: The single-row table every hive database carries, the current version, and how a version mismatch is handled.
---

Every hive database carries a schema version in a single-row table:

```sql
CREATE TABLE schema_version (
    version INTEGER NOT NULL
);
```

The current version is **1** — the only version that has existed.

loregd checks the version as it opens each database (§2.2, step 4) and
takes one of three paths:

| State | Behaviour |
|---|---|
| No `schema_version` table | The database is new. loregd creates the persistent tables, the volatile tables, and inserts version 1, all in one transaction. |
| Version equals 1 | Normal startup. |
| Version greater than 1 | Startup fails. The database was written by a newer loregd, and proceeding risks corrupting it by writing through an older understanding of its layout. |
| Version less than 1 | Startup fails. |

**There are no migrations.** loregd carries no migration table, no
migration step list, and no upgrade path; an older database is reported
as requiring migration and startup stops there. Since 1 is the only
version ever assigned, this does not arise in practice — but a second
version cannot be stamped without building the migration machinery
first.

Two details of the check are worth knowing. The `schema_version` table
has no primary key, uniqueness constraint, or check constraint, so a
second row is not detected: the first row read wins. And because every
table is created with `IF NOT EXISTS`, a database holding the data tables
but no `schema_version` table is stamped as version 1 without any
validation that its contents match that layout.
