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
3. The `series`, `samples`, and `metadata` tables created as defined in §7.1.
4. All write-time indexes created.
5. The `schema_version` and `created_at` metadata entries populated.

## Database opening

When the metric store database exists at startup, eventd MUST:

1. Open the database in WAL mode with synchronous NORMAL.
2. Verify the schema version. If unrecognised, eventd MUST log an error and MUST NOT write to the database. The database remains available for read-only queries.
3. Verify structural integrity (required tables and indexes exist).
4. The series cache starts empty. It is populated on demand as metric samples arrive -- each cache miss triggers a SQLite SELECT and inserts the result into the cache. Within one collection cycle (typically 15 seconds), all active series are cached. No pre-warming is required.

## Concurrency

The metric store has one read-write connection (owned by the metric writer thread) and zero or more read-only connections (owned by query handlers). WAL mode permits concurrent reads alongside the single writer.

## WAL checkpointing

The metric writer thread MUST trigger WAL checkpoints when the WAL exceeds a size threshold, using `SQLITE_CHECKPOINT_PASSIVE` mode.
