---
title: Database Lifecycle
---

## Log store path

The log store database resides at a path configured via the `LogStorePath` registry key under `Machine\System\eventd\`. The value MUST be a file path (not a directory, unlike the event store which uses a directory of shards). There is no compiled-in default -- if the key does not exist or is invalid, eventd MUST fail to start.

eventd MUST create the database file and its parent directories if they do not exist.

## Database creation

When the log store database does not exist at startup, eventd MUST create it with:

1. WAL mode enabled (`PRAGMA journal_mode=WAL`).
2. Synchronous mode set to NORMAL (`PRAGMA synchronous=NORMAL`).
3. The `logs` and `metadata` tables created as defined in §5.1.
4. The `idx_logs_timestamp`, `idx_logs_origin`, and `idx_logs_job_id` indexes created.
5. The `schema_version` and `created_at` metadata entries populated.

## Database opening

When the log store database exists at startup, eventd MUST:

1. Open the database in WAL mode.
2. Set synchronous mode to NORMAL.
3. Verify the schema version. If the version is missing or unrecognised, eventd
   MUST fail startup. Automatic schema migration is out of scope for v0.23 and
   MUST NOT be attempted.
4. Verify structural integrity (required tables and indexes exist). If
   verification fails without SQLite reporting database corruption, eventd MUST
   fail startup.
5. If SQLite reports database corruption while opening or verifying the log
   store, eventd MUST quarantine the corrupt database files by renaming the main
   database file, and any matching `-wal` and `-shm` files, to names with the
   suffix `.corrupt.<timestamp_ns>`, then create a new empty log store database
   at the configured path.

If a quarantine target name already exists, eventd MUST append `.N` where `N` is
the lowest positive decimal integer that makes the target name unique. The main
database, `-wal`, and `-shm` files from the same quarantine operation MUST use
the same suffix.

## Concurrency

The log store has one read-write connection (owned by the log writer thread) and zero or more read-only connections (owned by query handlers). WAL mode permits concurrent reads alongside the single writer.

## WAL checkpointing

The log writer thread MUST trigger a WAL checkpoint when the WAL reaches or
exceeds `WalCheckpointPages` pages, using `SQLITE_CHECKPOINT_PASSIVE` mode. If
a passive checkpoint cannot make progress because active readers hold pages, the
writer MUST NOT block -- it continues writing and retries the checkpoint after
later commits.
