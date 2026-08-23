---
title: Terminology
description: The registry vocabulary this manual borrows from the kernel-side documentation, and the terms loregd adds.
---

The registry's own vocabulary — hive, key, value, layer, source, watch,
security descriptor, sequence number — is defined by the kernel-side
registry documentation and is used here unchanged.

The terms below are specific to loregd.

**Hive database.** The SQLite database file backing one hive. Each hive
registered by loregd has its own file, whose path is given on the command
line (§2.1). Referred to in SQL as the `main` schema.

**Volatile database.** The in-memory SQLite database backing one hive's
volatile keys, attached to that hive's connections under the schema name
`volatile` (§3.3). It mirrors the hive database's tables, holds no data at
startup, and is destroyed with the process.

**Folded name.** The case-folded form of a key name, value name, or child
name, stored in a `_folded` column beside the canonical case-preserving
name and used for all case-insensitive comparison (§3.4).

**Write connection.** The single SQLite connection per hive through which
every mutation passes. Its uniqueness is what serialises writes (§4.1).

**Read pool.** The fixed set of connections serving reads that are not
part of a transaction, selected round-robin (§4.1).

**Snapshot connection.** A dedicated connection opened for one read-only
transaction, pinning a point-in-time view of the hive database for that
transaction's lifetime (§4.3).

**Orphan.** A key record that no path entry in any layer points at. Orphans
are cleaned up at startup (§2.2) and are reported by `RSI_DELETE_LAYER` as
the keys its deletion left unreachable (§5.6).
