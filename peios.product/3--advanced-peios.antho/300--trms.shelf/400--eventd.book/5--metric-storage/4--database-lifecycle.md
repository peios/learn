---
title: Database Lifecycle
description: The metric store file — its path, creation, opening, concurrency and checkpointing.
---

## Path

The file named by `MetricStorePath` (§A). No compiled-in default; a
missing or invalid value is a startup failure. eventd creates the file
and any absent parent directories.

## Creation

1. WAL mode.
2. `PRAGMA synchronous=NORMAL` — the log store's reasoning, for the same
   reason: metric loss on power failure is acceptable (§4.1).
3. The `series`, `samples`, `rollups` and `metadata` tables (§5.2,
   §5.6).
4. Every write-time index.
5. The `schema_version` and `created_at` entries.

## Opening

1. Open in WAL mode with synchronous NORMAL.
2. Verify the schema version. Missing or unrecognised is a **startup
   failure**; no migration.
3. Verify structural integrity — required tables and indexes present,
   including `rollups` and its lookup index. Failing this, with SQLite
   reporting no corruption, is a **startup failure**.
4. On SQLite reporting corruption, quarantine and replace, exactly as
   for a shard (§3.3): matching `-wal` and `-shm` files renamed with the
   same `.corrupt.<timestamp_ns>` suffix, `.N` appended if the name is
   taken, and a fresh empty store created at the configured path.

The metric store is a required store; there is no degraded mode without
one (§8.2).

After opening or creation the series cache is empty and fills on demand
(§5.3).

## Concurrency

One read-write connection owned by the metric writer thread, and any
number of read-only query connections. WAL mode permits both
concurrently.

The single-writer property is load-bearing here in a way it is not for
the other stores: series resolution checks for an existing row and then
inserts, without a transaction spanning both, and only one writer makes
that safe (§5.2).

## Checkpointing

The metric writer checkpoints at `WalCheckpointPages` (§A) in passive
mode, and does not block when readers hold pages.

As with the log store, the checkpoint is the durability boundary under
`synchronous=NORMAL`, not merely space reclamation (§9.5).
