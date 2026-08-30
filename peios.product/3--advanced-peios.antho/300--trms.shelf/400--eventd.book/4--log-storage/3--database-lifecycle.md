---
title: Database Lifecycle
description: The log store directory and fixed database file — its creation, opening, concurrency and checkpointing.
---

## Path

`LogStorePath` (§A) names a provisioned directory, conventionally
`/var/state/eventd/logs`. The database itself has the fixed name
`logs.db` inside it. A missing, invalid or unsafe directory is a startup
failure.

The directory has the provisioning, descriptor and path-resolution
requirements defined for the event store (§3.3). eventd does not create
it or any parent directory, never follows a symbolic-link component,
and creates or opens the database relative to an already validated
directory handle.

## Creation

A log store that does not exist is created with:

1. WAL mode, `PRAGMA journal_mode=WAL`
2. `PRAGMA synchronous=NORMAL`
3. the `logs`, `log_origins` and `metadata` tables (§4.2)
4. the `idx_logs_timestamp`, `idx_logs_origin` and `idx_logs_job_id`
   indexes
5. the `schema_version` and `created_at` entries

## Opening

1. Open in WAL mode.
2. Set synchronous to NORMAL.
3. Verify the schema version. Missing or unrecognised is a **startup
   failure**; no migration is attempted.
4. Verify structural integrity — required tables and indexes present.
   Failing this, with SQLite reporting no corruption, is a **startup
   failure**.
5. On SQLite reporting corruption, quarantine and replace.

Quarantine works exactly as for a shard (§3.3): the database, `-wal` and
`-shm` files are renamed with a shared `.corrupt.<timestamp_ns>` suffix,
`.N` appended with the lowest positive integer if the name is taken, and
a fresh empty log store is created at the configured path.

The log store is a **required** store. There is no degraded mode in
which eventd runs without one (§8.2), which is why steps 3 and 4 fail
startup rather than proceeding without logs.

## Concurrency

Exactly one read-write connection, owned by the log writer thread, and
any number of read-only query and maintenance connections. WAL mode
lets readers run concurrently. Retention and catalogue cleanup submit
bounded commands to the writer and never open another read-write
connection (§3.6).

## Checkpointing

The log writer checkpoints when its write-ahead log reaches
`WalCheckpointPages` (§A), in passive mode, and does not block if
readers hold pages — it keeps writing and retries after a later commit.

Checkpointing matters more here than in the event store, because
`synchronous=NORMAL` makes the checkpoint the durability boundary rather
than merely a space-reclamation event: data committed since the last
checkpoint is what a power cut takes (§9.5).
