---
title: Adaptive Indexing
---

## Purpose

Secondary indexes accelerate queries but slow writes. The optimal set of indexes depends on the actual query patterns of the deployment, which vary between systems and over time. Adaptive indexing allows eventd to maintain the right indexes for the workload without manual tuning.

## Global desired index set

eventd MUST maintain a global desired index set -- an ordered list of columns that should be indexed across all shard databases. The list is ordered by priority: the most frequently queried column has the highest priority.

The desired index set is computed from query frequency tracking. eventd MUST record which columns appear in filter predicates (WHERE clauses) across the query interface. For each queryable column, eventd tracks the number of queries that filter on that column over a rolling time window. Columns whose query frequency exceeds the creation threshold are added to the desired set. Columns whose frequency falls below the removal threshold are removed.

The desired index set is global -- it applies to all shards uniformly. Individual shards do not make independent indexing decisions.

## Shard convergence

Each shard independently converges its material indexes toward the global desired set during periods of low write activity. When a shard's writer thread has no pending events and the shard's material indexes do not match the desired set, the writer thread SHOULD create or drop indexes to converge.

Index creation uses `CREATE INDEX IF NOT EXISTS`. Index removal uses `DROP INDEX IF EXISTS`. Both operations run on the shard's writer thread.

Index creation MUST be cancellable. If the drain threads detect rising write pressure while an index build is in progress, the drain threads MUST signal the writer thread to abort the build. The writer thread MUST cancel the in-progress `CREATE INDEX` (e.g., via `sqlite3_interrupt()`), causing SQLite to roll back the partial index cleanly. The writer thread then resumes normal event batch writing immediately. The aborted index build is reattempted during the next quiet period.

Throughput MUST always take priority over index maintenance.

Shards converge at their own pace. A shard under sustained write pressure may lag behind the desired set indefinitely. This is acceptable -- the shard is prioritising throughput over query performance.

## Pressure-based index shedding

When a shard is under sustained write pressure, it MUST shed indexes to reduce per-insert overhead and protect throughput.

**Graduated shedding.** If a shard's adaptive batch sizing consistently produces batches exceeding 75% of `MaxBatchSize` over an extended period, the shard MUST drop its lowest-priority secondary index (the index whose corresponding column has the lowest query frequency in the global desired set). If pressure remains after dropping the lowest-priority index, the next-lowest is dropped, and so on.

**Emergency shedding.** If a shard is at maximum batch size and still falling behind the ingestion rate (ring buffer levels rising despite maxed-out batching), the shard MUST drop all secondary indexes immediately. `DROP INDEX` is a fast metadata operation (milliseconds, not seconds) and is safe to execute under pressure.

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

Index names MUST follow the convention `idx_events_<column>` (e.g., `idx_events_event_type`, `idx_events_process_guid`).

## Configuration

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| AdaptiveIndexWindowHours | REG_DWORD | 24 | 1--168 | Rolling time window in hours over which query frequency is measured. |
| AdaptiveIndexCreateThreshold | REG_DWORD | 100 | 10--10000 | Number of queries filtering on a column within the window required to add it to the desired set. |
| AdaptiveIndexDropThreshold | REG_DWORD | 10 | 1--1000 | Number of queries filtering on a column within the window below which it is removed from the desired set. The drop threshold MUST be less than the create threshold to provide hysteresis. |

## Persistence

The global desired index set and query frequency counters MUST be persisted across eventd restarts so that indexing decisions are based on long-term patterns, not just the current session. The persistence mechanism is implementation-defined.

The set of material indexes in each shard is discovered from the database schema on startup. eventd resumes convergence from whatever state each shard is in -- it does not drop or rebuild indexes on startup.
