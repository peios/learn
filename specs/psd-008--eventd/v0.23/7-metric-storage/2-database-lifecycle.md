---
title: Database Lifecycle
---

## Metric store path

The metric store database resides at a path configured via the `MetricStorePath` registry key under `Machine\System\eventd\`. The value MUST be a file path. There is no compiled-in default -- if the key does not exist or is invalid, eventd MUST fail to start.

eventd MUST create the database file and its parent directories if they do not exist.

## Database creation

When the metric store database does not exist at startup, eventd MUST create it with:

1. WAL mode enabled.
2. Synchronous mode set to NORMAL (same rationale as the log store -- metric loss on power failure is tolerable).
3. The `series`, `samples`, `rollups`, and `metadata` tables created as defined in §7.1 and §7.4.
4. All write-time indexes created.
5. The `schema_version` and `created_at` metadata entries populated.

## Database opening

When the metric store database exists at startup, eventd MUST:

1. Open the database in WAL mode with synchronous NORMAL.
2. Verify the schema version. If the version is missing or unrecognised, eventd
   MUST fail startup. Automatic schema migration is out of scope for v0.23 and
   MUST NOT be attempted.
3. Verify structural integrity (required tables and indexes exist, including
   the rollups table and rollup lookup index). If verification fails without
   SQLite reporting database corruption, eventd MUST fail startup.
4. If SQLite reports database corruption while opening or verifying the metric
   store, eventd MUST quarantine the corrupt database files by renaming the main
   database file, and any matching `-wal` and `-shm` files, to names with the
   suffix `.corrupt.<timestamp_ns>`, then create a new empty metric store
   database at the configured path.

If a quarantine target name already exists, eventd MUST append `.N` where `N` is
the lowest positive decimal integer that makes the target name unique. The main
database, `-wal`, and `-shm` files from the same quarantine operation MUST use
the same suffix.

After the metric store is opened or created, the series cache starts empty. It
is populated on demand as metric samples arrive -- each cache miss triggers a
SQLite SELECT and inserts the result into the cache. Within one collection cycle
(typically 15 seconds), all active series are cached. No pre-warming is
required.

## Concurrency

The metric store has one read-write connection (owned by the metric writer thread) and zero or more read-only connections (owned by query handlers). WAL mode permits concurrent reads alongside the single writer.

## WAL checkpointing

The metric writer thread MUST trigger a WAL checkpoint when the WAL reaches or
exceeds `WalCheckpointPages` pages, using `SQLITE_CHECKPOINT_PASSIVE` mode. If
a passive checkpoint cannot make progress because active readers hold pages, the
writer MUST NOT block -- it continues writing and retries the checkpoint after
later commits.
