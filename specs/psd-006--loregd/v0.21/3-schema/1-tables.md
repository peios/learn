---
title: Database Schema
---

Each hive has its own SQLite database. The schema is identical
across all hive databases. loregd creates these tables on first
boot and migrates them on schema version changes.

## Schema version tracking

```sql
CREATE TABLE schema_version (
    version INTEGER NOT NULL
);
```

A single row. The current schema version is **1** (the initial
release defined by this specification). loregd checks this at
startup. If the version is older, loregd runs migrations. If
newer, loregd refuses to start (prevents downgrade corruption).
On first boot (empty database), loregd creates the schema and
inserts version 1.

## Keys table

```sql
CREATE TABLE keys (
    guid           BLOB NOT NULL PRIMARY KEY,
    name           TEXT NOT NULL,
    name_folded    TEXT NOT NULL,
    parent_guid    BLOB,
    sd             BLOB NOT NULL,
    volatile       INTEGER NOT NULL DEFAULT 0,
    symlink        INTEGER NOT NULL DEFAULT 0,
    last_write_time INTEGER NOT NULL
);
```

- **guid:** 16-byte GUID assigned by LCS. Primary key.
- **name:** Case-preserving key name component.
- **name_folded:** Unicode Simple Case Folded form of name. Used
  for case-insensitive lookups.
- **parent_guid:** GUID of the parent key. NULL for hive root.
- **sd:** Security Descriptor in PSD-004 binary format.
- **volatile:** 1 if volatile, 0 if persistent. Volatile keys are
  stored in the in-process volatile store, not this table. This
  column exists only for persistent keys and is always 0 in the
  on-disk database. See §3.1.6.
- **symlink:** 1 if this key is a symbolic link, 0 otherwise.
- **last_write_time:** Unix nanoseconds.

## Path entries table

```sql
CREATE TABLE path_entries (
    parent_guid    BLOB NOT NULL,
    child_name     TEXT NOT NULL,
    child_name_folded TEXT NOT NULL,
    layer          TEXT NOT NULL,
    target_type    INTEGER NOT NULL,
    target_guid    BLOB,
    sequence       INTEGER NOT NULL,
    PRIMARY KEY (parent_guid, child_name_folded, layer)
);

CREATE INDEX idx_path_entries_target
    ON path_entries (target_guid)
    WHERE target_type = 0;
```

- **parent_guid:** GUID of the parent key.
- **child_name:** Case-preserving child name.
- **child_name_folded:** Folded form for case-insensitive primary
  key.
- **layer:** Layer name (case-sensitive, binary comparison).
- **target_type:** 0 = GUID (key exists in this layer), 1 = HIDDEN
  (tombstone masking lower layers).
- **target_guid:** The key GUID if target_type=0. NULL if HIDDEN.
- **sequence:** Monotonic sequence number assigned by LCS.

The index on target_guid (for non-HIDDEN entries) enables efficient
orphan detection: keys whose GUID does not appear in any path
entry.

## Values table

```sql
CREATE TABLE values (
    key_guid       BLOB NOT NULL,
    name           TEXT NOT NULL,
    name_folded    TEXT NOT NULL,
    layer          TEXT NOT NULL,
    type           INTEGER NOT NULL,
    data           BLOB,
    sequence       INTEGER NOT NULL,
    PRIMARY KEY (key_guid, name_folded, layer)
);
```

- **key_guid:** GUID of the key this value belongs to.
- **name:** Case-preserving value name. Empty string for the
  default value.
- **name_folded:** Folded form. Empty string for the default value.
- **layer:** Layer name.
- **type:** Registry value type (REG_SZ=1, REG_DWORD=4, etc.).
  REG_TOMBSTONE (0xFFFF) for tombstones.
- **data:** Value payload. NULL for tombstones.
- **sequence:** Monotonic sequence number.

## Blanket tombstones table

```sql
CREATE TABLE blanket_tombstones (
    key_guid       BLOB NOT NULL,
    layer          TEXT NOT NULL,
    sequence       INTEGER NOT NULL,
    PRIMARY KEY (key_guid, layer)
);
```

- **key_guid:** GUID of the key this blanket tombstone belongs to.
- **layer:** Layer name.
- **sequence:** Monotonic sequence number.

## Volatile store

Volatile keys are not stored in SQLite. Each hive has a volatile
store: an in-process, in-memory structure owned by loregd, created
empty at startup and discarded at exit. The volatile store consists
of four ordered maps mirroring the on-disk tables:

```
keys:                guid
                       → (name, name_folded, parent_guid, sd,
                          symlink, last_write_time)
path_entries:        (parent_guid, child_name_folded, layer)
                       → (child_name, target_type, target_guid,
                          sequence)
values:              (key_guid, name_folded, layer)
                       → (name, type, data, sequence)
blanket_tombstones:  (key_guid, layer)
                       → (sequence)
```

The maps MUST be ordered maps (B-tree or equivalent: any structure
supporting point lookup and in-order range scans over a key
prefix). Map keys are the same as the corresponding tables' primary
keys, giving the same uniqueness guarantees. Composite keys order
componentwise with bytewise comparison per component (GUIDs as
16-byte values, folded names and layer names as binary strings),
matching the binary comparisons the SQL schema performs. This makes
every enumeration a contiguous range scan: all path entries under a
parent_guid, all layer entries for one (parent_guid,
child_name_folded), and all values or blanket tombstones for one
key_guid.

Field semantics are identical to the corresponding on-disk columns.
The volatile record has no `volatile` field — every record in the
volatile store is volatile by definition, and loregd reports
volatile=1 for these keys in RSI responses.

No secondary index is prescribed. Reverse lookups by target_guid
(RSI_DROP_KEY, orphan capture in RSI_DELETE_LAYER) scan the
path_entries map. Volatile stores hold transient runtime state and
stay small; a scan is acceptable where the on-disk schema uses
idx_path_entries_target.

When processing RSI operations, loregd checks the volatile flag
on the target key to determine which store to query/write:
- volatile=1 → the volatile store's maps
- volatile=0 → the `main.*` tables

For RSI_LOOKUP and RSI_ENUM_CHILDREN, loregd MUST query both the
main tables and the volatile store and merge the results, since a
parent key may be persistent while a child is volatile (or vice
versa, though a non-volatile child under a volatile parent is
forbidden by PSD-005 §2.1).

For RSI_CREATE_KEY, loregd stores the key in the volatile store
if the volatile flag is set in the request, otherwise in the main
database.

Concurrency (readers–writer lock, single-writer discipline) is
specified in §4.1; transactional behaviour (the transaction
overlay) in §5.1.

## Case folding

The `name_folded` and `child_name_folded` columns store the
Unicode Simple Case Folded form (CaseFolding.txt, status S and C
entries, Unicode 16.0 per PSD-005 §2.3) of the
corresponding name. loregd computes the folded
form at write time and uses the folded column in all WHERE clauses
and primary key lookups.

This avoids the need for a custom SQLite collation function.
Queries use exact binary comparison on the folded column:

```sql
-- Lookup by name (case-insensitive):
SELECT * FROM path_entries
WHERE parent_guid = ? AND child_name_folded = ?
```

The canonical (case-preserving) name is stored separately and
returned in RSI responses. Callers see the original case; storage
comparisons use the folded form.
