---
title: Adaptive Indexing
---

## Purpose

Secondary indexes accelerate queries but slow writes. The optimal set of indexes depends on the actual query patterns of the deployment, which vary between systems and over time. Adaptive indexing allows eventd to maintain the right indexes for the workload without manual tuning.

## Global desired index set

eventd MUST maintain a global desired index set -- an ordered list of columns that should be indexed across all shard databases. The list is ordered by priority: the most frequently queried column has the highest priority.

The adaptive indexing system has three decoupled components:

1. **Query frequency counters.** Query handlers increment per-field counters when a field appears in a WHERE predicate. This is the sole write-heavy path. Counters are stored in memory and periodically persisted to a dedicated metadata database in the event store directory (not in the shard databases, since the counters are global state independent of shard configuration).
2. **Index policy logic.** A periodic process reads the query frequency counters, applies the creation and removal thresholds, and computes the desired index set. This runs at the interval configured by `AdaptiveIndexPolicyIntervalMinutes` (default 60 minutes). The policy logic is the sole writer to the desired set. The desired set is stored in memory and persisted to the same metadata database. Future versions MAY extend the policy logic with manual rules (e.g., "always index event_type regardless of query frequency") or administrative overrides.
3. **Shard convergence.** Writer threads read the desired index set and converge their material indexes toward it during quiet periods. Writer threads never read the counters and never write to the desired set.

This separation ensures that the high-frequency counter updates (one per query) do not contend with the writer threads' index convergence checks (one per drain cycle). The policy logic is the bridge between the two and runs infrequently enough to never be a contention point.

The desired index set is global -- it applies to all shards uniformly. Individual shards do not make independent indexing decisions.

## Shard convergence

Each shard independently converges its material indexes toward the global desired set during periods of low write activity. When a shard's writer thread has no pending events and the shard's material indexes do not match the desired set, the writer thread SHOULD create or drop indexes to converge.

Index creation uses `CREATE INDEX IF NOT EXISTS`. Index removal uses `DROP INDEX IF EXISTS`. Both operations run on the shard's writer thread.

Index creation MUST be cancellable. If the drain threads detect rising write pressure while an index build is in progress, the drain threads MUST signal the writer thread to abort the build. The writer thread MUST cancel the in-progress `CREATE INDEX`, causing SQLite to roll back the partial index cleanly. The writer thread then resumes normal event batch writing immediately. The aborted index build is reattempted during the next quiet period.

Throughput MUST always take priority over index maintenance.

> [!INFORMATIVE]
> `sqlite3_interrupt()` sets a flag that SQLite checks at SQL VM opcode boundaries. During B-tree construction for a large index, the gap between checks can be tens of milliseconds -- long enough to cause ring buffer overrun at high event rates. Implementations SHOULD use `sqlite3_progress_handler()` to register a callback invoked every N VM opcodes (e.g., every 1000 opcodes). The callback checks a cancellation flag and returns non-zero to abort the operation. This provides much more responsive cancellation than `sqlite3_interrupt()` alone.

Shards converge at their own pace. A shard under sustained write pressure may lag behind the desired set indefinitely. This is acceptable -- the shard is prioritising throughput over query performance.

## Pressure-based index shedding

When a shard is under sustained write pressure, it MUST shed indexes to reduce per-insert overhead and protect throughput.

**Graduated shedding.** If more than `SheddingBatchPercent`% of a shard's batches exceed 75% of `MaxBatchSize` within a sliding window of `SheddingWindowSeconds` seconds, the shard MUST drop its lowest-priority secondary index (the index whose corresponding column has the lowest query frequency in the global desired set). If pressure remains after dropping the lowest-priority index, the next-lowest is dropped, and so on. The shedding check runs once per batch commit.

**Emergency shedding.** If a shard is at maximum batch size and the drain thread signals rising ring buffer pressure (see below), the shard MUST drop all secondary indexes immediately. `DROP INDEX` is a fast metadata operation (milliseconds, not seconds) and is safe to execute under pressure.

### Ring buffer pressure signaling

The drain thread monitors the gap between `write_pos` and its `read_pos` in the KMES ring buffer. If this gap exceeds `EmergencySheddingBufferPercent`% of the ring buffer capacity, the drain thread MUST signal the writer thread that emergency shedding is required. This signal is distinct from the index-build cancellation signal -- it triggers immediate shedding of all secondary indexes regardless of whether an index build is in progress.

### Shedding configuration

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| SheddingWindowSeconds | REG_DWORD | 30 | 10--300 | Sliding window for graduated shedding evaluation. |
| SheddingBatchPercent | REG_DWORD | 75 | 50--100 | Percentage of batches within the window that must exceed 75% of MaxBatchSize to trigger graduated shedding. |
| EmergencySheddingBufferPercent | REG_DWORD | 75 | 50--95 | Ring buffer fill percentage that triggers emergency shedding. |

The `idx_events_timestamp` index is exempt from shedding. It is always maintained regardless of write pressure. Time-range queries are the foundational access pattern and cannot function without a timestamp index.

## Recovery

When write pressure subsides after index shedding, the shard MUST rebuild dropped indexes to converge back toward the global desired set. Rebuilding follows the same low-write-activity scheduling and cancellability rules as initial index creation.

The rebuild order follows the priority order of the desired set: highest-priority (most frequently queried) indexes are rebuilt first.

## Candidate fields

All fields that can appear in a WHERE predicate are candidates for adaptive indexing. This includes both header columns and payload fields.

### Header column indexes

The following `events` table columns are candidates for standard column indexes:

- `event_type`
- `origin_class`
- `cpu_id`
- `effective_token_guid`
- `true_token_guid`
- `process_guid`
- `boot_id`

The `timestamp` column is always indexed and is not subject to adaptive management.

### Payload field indexes

Any payload field path that appears in a WHERE predicate is a candidate for an expression index. Expression indexes use SQLite's expression index feature with a registered `msgpack_extract` function:

```sql
CREATE INDEX idx_payload_granted_access ON events(msgpack_extract(payload, '$.granted_access'))
```

The expression index extracts the specified field from the msgpack payload on every INSERT and indexes the result. SQLite's query optimiser uses the expression index automatically when the same extraction expression appears in a WHERE clause.

Payload field indexes follow the same priority ordering, pressure-based shedding, and convergence rules as header column indexes. They are part of the same global desired index set.

The raw `payload` column MUST NOT receive a plain column index -- indexing an opaque blob is meaningless. Only expression indexes on specific payload field paths are created.

## Index naming

Index names MUST follow the convention `idx_events_<column>` for header column indexes (e.g., `idx_events_event_type`, `idx_events_process_guid`). For payload expression indexes, dots in the field path are replaced with underscores: `idx_events_payload_<path>` (e.g., `idx_events_payload_granted_access`, `idx_events_payload_source_name` for the path `source.name`).

## Configuration

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| AdaptiveIndexWindowHours | REG_DWORD | 24 | 1--168 | Rolling time window in hours over which query frequency is measured. |
| AdaptiveIndexPolicyIntervalMinutes | REG_DWORD | 60 | 60--1440 | How often the index policy logic recomputes the desired index set from the query frequency counters. Minimum 60 minutes to prevent index churn. |
| AdaptiveIndexCreateThreshold | REG_DWORD | 100 | 10--10000 | Number of queries filtering on a column within the window required to add it to the desired set. |
| AdaptiveIndexDropThreshold | REG_DWORD | 10 | 1--1000 | Number of queries filtering on a column within the window below which it is removed from the desired set. The drop threshold MUST be less than the create threshold to provide hysteresis. |

## Persistence

The global desired index set, query frequency counters, and adaptive rollup state (§7.4) MUST be persisted to a dedicated metadata database in the event store directory. This database is independent of the shard databases and survives shard reconfiguration.

### Metadata database

The metadata database MUST be named `eventd-meta.db` and reside in the event store directory (alongside the shard databases). It is created on first startup if it does not exist.

The database MUST be opened in WAL mode with `synchronous=NORMAL`. It is low-volume (written once per policy interval, read at startup) and does not require per-transaction durability.

The database MUST contain the following tables:

**`index_counters` table:**

| Column | Type | Description |
|---|---|---|
| `field_path` | TEXT PRIMARY KEY | The field name or payload path (e.g., `"event_type"`, `"granted_access"`, `"source.name"`). |
| `query_count` | INTEGER NOT NULL | Number of queries filtering on this field within the current rolling window. |
| `window_start` | INTEGER NOT NULL | Timestamp (nanoseconds since epoch) when the current window started. |

**`desired_indexes` table:**

| Column | Type | Description |
|---|---|---|
| `field_path` | TEXT PRIMARY KEY | The field name or payload path. |
| `priority` | INTEGER NOT NULL | Priority rank (lower number = higher priority = more frequently queried). |
| `is_expression` | INTEGER NOT NULL | 1 if this is a payload expression index, 0 if a column index. |

**`rollup_counters` table:**

| Column | Type | Description |
|---|---|---|
| `function_window` | TEXT PRIMARY KEY | Composite key of function name and window size (e.g., `"avg_3600"` for AVG over 1 hour). |
| `query_count` | INTEGER NOT NULL | Number of queries using this function/window pair within the current rolling window. |
| `window_start` | INTEGER NOT NULL | Timestamp when the current window started. |

**`desired_rollups` table:**

| Column | Type | Description |
|---|---|---|
| `function_window` | TEXT PRIMARY KEY | Composite key matching `rollup_counters`. |
| `priority` | INTEGER NOT NULL | Priority rank. |

**`meta` table:**

| Column | Type | Description |
|---|---|---|
| `key` | TEXT PRIMARY KEY | Metadata key. |
| `value` | TEXT NOT NULL | Metadata value. |

Required `meta` entries: `schema_version` (value `1`), `created_at` (ISO 8601), `admin_sd` (self-relative Security Descriptor in binary, controlling who can execute the INDEX command and other administrative operations on the indexing policy).

The default `admin_sd` grants access to SYSTEM and Administrators. eventd MUST check the caller's token against this SD when processing an INDEX command via `kacs_access_check` with `EVENTD_READ` as the desired access right.

### Concurrency

The metadata database has a single writer: the index/rollup policy logic thread. Query handlers write to in-memory counters only; the policy logic flushes counters to the database at each policy interval. Writer threads and query handlers read the desired index/rollup sets from memory, not from the database.

The metadata database is opened read-write by the policy logic thread and is not accessed by any other thread at the database level. No concurrency control beyond SQLite's built-in WAL mode is required.

### Startup

On startup, eventd MUST:

1. Open `eventd-meta.db` in the event store directory. Create it if it does not exist.
2. Verify the schema version. If unrecognised, log an error and recreate the database (adaptive state is lost but not critical).
3. Load `index_counters` and `rollup_counters` into the in-memory counter structures.
4. Load `desired_indexes` and `desired_rollups` into the in-memory desired sets.
5. Discover material indexes from each shard database's schema and compare against the desired sets.

The set of material indexes in each shard is discovered from the database schema on startup. eventd resumes convergence from whatever state each shard is in -- it does not drop or rebuild indexes on startup.
