---
title: Database Lifecycle
description: The event store directory — naming, creation, opening an active shard, quarantine and historical shards.
---

## The event store directory

Every shard database and the metadata database live in one directory,
named by `EventStorePath` (§A). There is no compiled-in default: a
missing or invalid value is a startup failure, and eventd writes event
databases nowhere else.

The standard path is `/var/state/eventd/events/`. The eventd package
declares `/var/state/eventd/` and its `events/`, `logs/`, and `metrics/`
children as required peinit provisioned directories. Each carries an
explicit protected, inheritable descriptor granting full control only
to SYSTEM and Administrators:

```text
O:SYG:SYD:P(A;OICI;GA;;;SY)(A;OICI;GA;;;BA)
```

A deployment choosing another configured path MUST provision it with
equivalent protection before eventd starts.

eventd does not create store directories. It opens every path component
without following symbolic links, retains the resulting directory
descriptor, and opens, creates, renames and quarantines database, WAL
and shared-memory files relative to that descriptor. A missing path, a
non-directory component, a symbolic-link component, or protection that
allows an untrusted principal to replace children is a startup failure.
SQLite's database, `-wal`, and `-shm` files inherit the directory's
protection.

## Naming

Active shards are `shard-NNNN.db`, with the shard index zero-padded to
four digits — the index assigned at startup, which is not a CPU number
(§2.3).

Starting with more shards than exist creates the new ones. Starting with
fewer leaves the excess in place: they become historical shards, are
never deleted, and remain available to the query path.

## Creation

A shard database that does not exist is created with:

1. WAL mode, `PRAGMA journal_mode=WAL`
2. `PRAGMA synchronous=FULL`
3. the `events`, `event_types`, `receipt_ranges`, and `metadata` tables
   (§3.1)
4. the `idx_events_timestamp` index
5. the `schema_version` and `created_at` entries

## Opening an active shard

1. Open in WAL mode.
2. Set synchronous to FULL.
3. Read and verify `schema_version`. Missing or unrecognised is a
   **startup failure**. No migration is attempted.
4. Verify structural integrity — the required tables and write-time
   indexes exist. Failing this, with SQLite reporting no corruption, is
   a **startup failure**.
5. If SQLite reports corruption while opening or verifying, quarantine
   and replace (below).

Steps 3 and 4 fail rather than repair because an active shard is
required: eventd has no degraded mode that runs without one (§8.2).

## Quarantine

When SQLite reports corruption in a required store, eventd renames the
database aside and starts a fresh one at the original path. The main
database file and any matching `-wal` and `-shm` files are renamed with
the suffix `.corrupt.<timestamp_ns>`, all three using the same suffix
from one operation, and a new empty `shard-NNNN.db` is created.

If a target name is taken, eventd appends `.N` with the lowest positive
integer that makes it unique — which happens when two quarantines land
in the same nanosecond, and when a previous quarantine already used the
name.

Quarantining rather than deleting is the point: the corrupt file is the
only copy of whatever it held, recovering data from it is an
administrative operation, and eventd attempts no automatic repair.

The corruption is logged and a `synthetic.storage_error` event is
emitted once a shard is available to write it to (§9.2).

## Historical shards

A historical shard is never required for startup. If one has a missing
or unrecognised schema version, fails structural verification, or cannot
be opened read-only, eventd logs the error and **excludes it from the
query path for this run** — it does not fail startup and does not
quarantine it.

The asymmetry is deliberate. An active shard that will not open means
eventd cannot do its job; a historical one that will not open means some
old data is unreadable, which is a smaller problem than refusing to boot
the audit daemon over it.

## Query path discovery

The query path opens every file in the directory matching
`shard-NNNN.db` that has a recognised schema and passes structural
verification — active and historical alike. It assumes no particular
number of them.

It explicitly does **not** treat every `.db` file in the directory as a
shard: `eventd-meta.db` is excluded by the naming pattern, along with
anything else that happens to be there.

Each is opened with a read-only connection. Read-only connections in WAL
mode do not contend with the writer's connection.

## Concurrency

Each shard has exactly one read-write connection, owned by its writer
thread, and any number of read-only connections owned by query handlers.
WAL mode permits concurrent readers alongside one writer without
blocking either.

Writer threads never share connections. Each creates and owns its own
for the process lifetime, which is what makes the prepared statement in
§2.4 a per-thread object with no locking around it.
