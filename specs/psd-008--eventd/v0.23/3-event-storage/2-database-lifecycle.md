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

When an active shard database file exists at startup, eventd MUST:

1. Open the database in WAL mode.
2. Set synchronous mode to FULL.
3. Read and verify the `schema_version` metadata entry. If the version is
   missing or unrecognised, eventd MUST fail startup. Automatic schema
   migration is out of scope for v0.23 and MUST NOT be attempted.
4. Verify structural integrity (the required tables and write-time indexes
   exist). If verification fails without SQLite reporting database corruption,
   eventd MUST fail startup.
5. If SQLite reports database corruption while opening or verifying the active
   shard, eventd MUST quarantine the corrupt database files by renaming the
   main database file, and any matching `-wal` and `-shm` files, to names with
   the suffix `.corrupt.<timestamp_ns>`, then create a new empty active shard
   database at the original `shard-NNNN.db` path.

If a quarantine target name already exists, eventd MUST append `.N` where `N` is
the lowest positive decimal integer that makes the target name unique. The main
database, `-wal`, and `-shm` files from the same quarantine operation MUST use
the same suffix.

Historical shard databases from previous configurations are never required for
startup. If a historical shard has a missing/unrecognised schema version, fails
structural verification, or cannot be opened read-only, eventd MUST log the
error and exclude that database from the query path for this run.

## Query path discovery

The query path MUST discover all files in the event store directory whose names
match the active shard naming pattern (`shard-NNNN.db`) and open them for
reading when they have a recognised schema and pass structural verification.
This includes active shard databases and historical shard databases from
previous configurations. The query path MUST NOT assume a fixed number of shard
databases.

The query path MUST NOT treat every `.db` file in the event store directory as an event shard. In particular, it MUST exclude `eventd-meta.db` and any other non-shard database file.

Each database is opened with a read-only connection. Read-only connections do not contend with the writer thread's connection.

## Concurrency

Each shard database has exactly one read-write connection (owned by the shard's writer thread) and zero or more read-only connections (owned by query handlers). WAL mode permits concurrent reads alongside a single writer without blocking.

Writer threads MUST NOT share SQLite connections. Each writer thread creates and owns its connection for the lifetime of the eventd process.
