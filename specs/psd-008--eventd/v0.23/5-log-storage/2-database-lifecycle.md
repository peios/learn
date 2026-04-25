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
4. The `idx_logs_timestamp` and `idx_logs_origin` indexes created.
5. The `schema_version` and `created_at` metadata entries populated.

## Database opening

When the log store database exists at startup, eventd MUST:

1. Open the database in WAL mode.
2. Set synchronous mode to NORMAL.
3. Verify the schema version. If unrecognised, eventd MUST log an error and MUST NOT write to the database.
4. Verify structural integrity (required tables and indexes exist).

## Concurrency

The log store has one read-write connection (owned by the log writer thread) and zero or more read-only connections (owned by query handlers). WAL mode permits concurrent reads alongside the single writer.

## WAL checkpointing

The log writer thread MUST trigger WAL checkpoints when the WAL exceeds a size threshold, using `SQLITE_CHECKPOINT_PASSIVE` mode. The threshold is implementation-defined.
