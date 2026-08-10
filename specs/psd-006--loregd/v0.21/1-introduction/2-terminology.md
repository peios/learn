---
title: Terminology
---

Terms defined in PSD-005 (LCS, RSI, hive,
source, key, value, layer, SD, AccessCheck, token, SID, GUID,
watch, TCB) are used here with the same meaning and are not
redefined.

Additional terms specific to loregd:

- **Hive database**: A SQLite database file backing one hive. Each
  hive registered by loregd has its own database file. The file
  path is provided on the command line.

- **Volatile store**: A per-hive, in-process, in-memory structure
  holding volatile keys: four ordered maps mirroring the hive
  database's tables (§3.1.6). Not a SQLite database. The volatile
  store is lost when loregd exits.

- **Transaction overlay**: A private copy of a hive's volatile
  store, created on the first volatile mutation inside a read-write
  transaction. It replaces the shared volatile store when the
  transaction commits and is discarded when it aborts (§5.1).

- **Folded name**: The Unicode Simple Case Folded form of a key
  name, value name, or child name. Stored alongside the canonical
  (case-preserving) name for case-insensitive lookups.

- **Read connection**: A SQLite connection used for read-only
  operations. Multiple read connections may be open concurrently
  (WAL mode).

- **Write connection**: A SQLite connection used for mutating
  operations. Only one write connection exists per hive database.
  All persistent writes are serialised through this connection.

- **Write path**: The per-hive executor that owns the write
  connection and is the sole mutator of the hive's volatile store.
  All mutating operations — persistent and volatile — are
  serialised through it (§4.1).
