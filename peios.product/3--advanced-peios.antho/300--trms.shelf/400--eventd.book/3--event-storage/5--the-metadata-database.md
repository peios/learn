---
title: The Metadata Database
description: The one database in the store that is not a shard — its tables, its concurrency, and why recovering it is cheap.
---

One database in the event store directory is not a shard:
`eventd-meta.db`. It holds the state that is global to eventd rather
than to any shard — adaptive index state and diagnostic sequence
checkpoints — and it is the one database that survives shard
reconfiguration untouched.

It is created on first startup if absent, opened in WAL mode with
`synchronous=NORMAL`. It is written once per policy interval and read at
startup, so per-transaction durability buys nothing: losing the last
interval's counters costs some adaptation, not any data.

The query path excludes it explicitly, since it is in the same directory
as the shards (§3.3).

## Tables

**`index_counters`** — query frequency per field (§3.4).

| Column | Type | Contents |
|---|---|---|
| `field_path` | TEXT PRIMARY KEY | Field name or payload path: `event_type`, `granted_access`, `source.name`. |
| `query_count` | INTEGER NOT NULL | Queries filtering on it within the current window. |
| `window_start` | INTEGER NOT NULL | When the window started, nanoseconds since the epoch. |

**`desired_indexes`** — the computed desired index set.

| Column | Type | Contents |
|---|---|---|
| `field_path` | TEXT PRIMARY KEY | Field name or payload path. |
| `priority` | INTEGER NOT NULL | Rank; lower is higher priority. |
| `is_expression` | INTEGER NOT NULL | 1 for a payload expression index, 0 for a column index. |

**`sequence_checkpoints`** — diagnostic only.

| Column | Type | Contents |
|---|---|---|
| `boot_id` | BLOB NOT NULL | The boot the checkpoint applies to. |
| `cpu_id` | INTEGER NOT NULL | CPU identifier. |
| `sequence` | INTEGER NOT NULL | Last committed sequence for that pair when written. |
| `updated_at` | INTEGER NOT NULL | When it was written. |

Primary key `(boot_id, cpu_id)`. Startup recovery uses committed receipt
ranges and never this table (§2.2). The table exists so that an operator
can see what eventd believed at shutdown and compare it with receipt
coverage — the two disagreeing is itself diagnostic.

**`meta`** — key-value.

| Column | Type | Contents |
|---|---|---|
| `key` | TEXT PRIMARY KEY | Metadata key. |
| `value` | BLOB NOT NULL | Strings as UTF-8 bytes, binary as raw bytes. |

with two required entries: `schema_version` (§B) and `created_at` as a
UTC `YYYY-MM-DDTHH:MM:SSZ` string. The administrative descriptor lives
with every other eventd descriptor at
`Machine\System\eventd\Security\Admin` (§7.2); no access-control state is
stored in this reconstructible database.

## Concurrency

One writer connection, owned by the index policy thread. No
other thread opens the database read-write.

Query handlers write only to the in-memory counters; the policy thread
flushes them at each interval. Writer threads and query handlers read
the desired sets from memory, never from the database. Graceful shutdown
writes `sequence_checkpoints` through the same connection, after policy
activity has stopped (§8.4).

With a single writer and no other database-level access, SQLite's WAL
mode is the whole of the concurrency control needed.

The policy thread checkpoints the write-ahead log at
`WalCheckpointPages` in passive mode, and does not block when readers
hold pages — the same rule as every other store (§2.4).

## Recovery is cheap

If the schema version is missing or unrecognised, or any required table
or `meta` entry is missing or malformed, eventd logs an error and
**recreates the database from defaults**.

This is the opposite of the rule for a shard, which fails startup
(§3.3), and the difference is what is at stake. A shard holds the only
copy of audit data. This database holds an optimisation policy and some
diagnostics — all of it reconstructible, none of it irreplaceable.
Losing it costs the adaptation eventd had accumulated, and the counters
begin refilling immediately. Security policy is unaffected because it
lives in the registry.

## Startup

1. Open `eventd-meta.db`, creating it if absent.
2. Verify the schema version and required `meta` entries; recreate from
   defaults on failure.
3. Load `index_counters` into memory.
4. Load `desired_indexes` into memory.
5. Load `sequence_checkpoints`, for diagnostics only.
6. Discover the material indexes in each shard from its schema and
   compare against the desired set.

eventd resumes convergence from wherever each shard happens to be. It
neither drops nor rebuilds indexes at startup: a shard's material set is
a fact to be observed, not a state to be restored.
