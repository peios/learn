---
title: Database Lifecycle
---

## Event store directory

All event shard databases MUST reside in a single directory, the event store directory. The path is configured via the `EventStorePath` registry key under `Machine\System\eventd\`. There is no compiled-in default -- if the key does not exist or is invalid, eventd MUST fail to start.

eventd MUST create the directory if it does not exist. eventd MUST NOT write event databases to any other location.

## Shard database naming

Active shard databases MUST be named `shard-NNNN.db` where `NNNN` is the zero-padded shard index (0000, 0001, ...). The shard index is the shard number assigned at startup, not the CPU number.

When eventd starts with a shard count that requires new databases, it creates them. When eventd starts with a shard count smaller than the number of existing shard databases, the excess databases are not deleted -- they remain in the directory and are available to the query path.

## Database creation

When a shard database file does not exist at startup, eventd MUST create it with:

1. WAL mode enabled (`PRAGMA journal_mode=WAL`).
2. Synchronous mode set to FULL (`PRAGMA synchronous=FULL`).
3. The `events` and `metadata` tables created as defined in §3.1.
4. The `idx_events_timestamp` index created.
5. The `schema_version` and `created_at` metadata entries populated.

## Database opening

When a shard database file exists at startup, eventd MUST:

1. Open the database in WAL mode.
2. Set synchronous mode to FULL.
3. Read and verify the `schema_version` metadata entry. If the version is unrecognised, eventd MUST log an error and MUST NOT write to that database. The database remains available for read-only queries.
4. Verify structural integrity (the required tables exist). If verification fails, eventd MUST log an error and MUST NOT write to that database.

## Query path discovery

The query path MUST discover all `.db` files in the event store directory and open them for reading. This includes active shard databases, historical shard databases from previous configurations, and any archive databases created by the retention mechanism. The query path MUST NOT assume a fixed number of databases.

Each database is opened with a read-only connection. Read-only connections do not contend with the writer thread's connection.

## Concurrency

Each shard database has exactly one read-write connection (owned by the shard's writer thread) and zero or more read-only connections (owned by query handlers). WAL mode permits concurrent reads alongside a single writer without blocking.

Writer threads MUST NOT share SQLite connections. Each writer thread creates and owns its connection for the lifetime of the eventd process.
