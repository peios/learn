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

- **Volatile store**: A SQLite in-memory database (`:memory:`)
  ATTACHed to a hive database connection. Volatile keys are stored
  here. The volatile store is lost when loregd exits.

- **Folded name**: The Unicode Simple Case Folded form of a key
  name, value name, or child name. Stored alongside the canonical
  (case-preserving) name for case-insensitive lookups.

- **Read connection**: A SQLite connection used for read-only
  operations. Multiple read connections may be open concurrently
  (WAL mode).

- **Write connection**: A SQLite connection used for mutating
  operations. Only one write connection exists per hive database.
  All writes are serialised through this connection.
