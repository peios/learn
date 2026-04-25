---
title: Adaptive Rollups
---

## Purpose

Aggregate metric queries (AVG_OVER, MIN_OVER, MAX_OVER, RATE, P95 over time ranges) require reading and processing raw samples. For large time ranges, this means scanning thousands or millions of rows. Pre-computing the results of common aggregate queries and storing them as rollups dramatically reduces query time.

Adaptive rollups apply the same principle as adaptive indexing for events: monitor which query patterns occur frequently, pre-compute the results in the background, and serve queries from the rollups when available.

## Rollup model

A rollup is a pre-computed aggregate stored in a dedicated table. Each rollup is defined by:

- **Series** -- which time series the rollup applies to.
- **Function** -- the aggregation function (AVG, MIN, MAX, SUM, RATE, P95, P99).
- **Window** -- the time window size (e.g., 5m, 1h, 1d).

A rollup for `cpu.usage[core="0"] AVG_OVER 1h` stores one pre-computed average value per hour for that specific series.

## Rollup table

The metric store database MUST contain a `rollups` table:

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | SQLite rowid. |
| `series_id` | INTEGER NOT NULL | Foreign key referencing `series(id)`. |
| `function` | INTEGER NOT NULL | Aggregation function identifier. |
| `window_seconds` | INTEGER NOT NULL | Window size in seconds. |
| `window_start` | INTEGER NOT NULL | Start timestamp of the window. Nanoseconds since Unix epoch. |
| `value` | REAL NOT NULL | The pre-computed aggregate value. |
| `sample_count` | INTEGER NOT NULL | Number of raw samples that contributed to this value. Allows the query engine to assess rollup quality (a window with 1 sample is less reliable than one with 60). |

A unique constraint MUST exist on `(series_id, function, window_seconds, window_start)`.

An index MUST exist on `(series_id, function, window_seconds, window_start)` to support efficient rollup lookups.

## Function identifiers

| Value | Function |
|---|---|
| 0 | AVG |
| 1 | MIN |
| 2 | MAX |
| 3 | SUM |
| 4 | RATE |
| 5 | P50 |
| 6 | P95 |
| 7 | P99 |

## Rollup registry

eventd MUST maintain a global rollup registry -- a set of (function, window) pairs that should be pre-computed across all series. The registry is computed from query frequency tracking, analogous to the global desired index set for events.

For each metric query that includes a value function and/or window function, eventd records the function and window size. When a (function, window) pair's query frequency exceeds the creation threshold over the rolling time window, it is added to the rollup registry. When it falls below the removal threshold, it is removed.

The rollup registry is global -- it applies to all series. If hourly averages are frequently queried for any metric, hourly averages are pre-computed for all active series.

## Rollup computation

Rollup computation runs on a background thread during periods of low write activity. For each (function, window) pair in the registry, the background thread:

1. Identifies time windows that have raw samples but no rollup entry.
2. Reads the raw samples for those windows.
3. Computes the aggregate value.
4. Inserts the rollup entry.

Only completed windows are rolled up. The current (still-accumulating) window is not pre-computed -- it is always computed from raw samples at query time.

Rollup computation MUST be cancellable. If write pressure rises, the computation is aborted and resumed later. The same cancellation mechanism as adaptive index creation (§3.3) applies.

## Query integration

When executing a metric query with a value function and/or window function, the query engine MUST check whether a matching rollup exists. If a rollup covers the requested function, window size, and time range:

- The query reads from the `rollups` table instead of the `samples` table.
- One row per time window instead of hundreds of raw samples per window.

If the rollup partially covers the time range (e.g., rollups exist for all but the most recent incomplete window), the query reads rollups for completed windows and computes the aggregate from raw samples for the incomplete window.

If no matching rollup exists, the query falls back to raw sample computation. The result is identical -- rollups are a transparent optimisation.

Rollup window sizes do not need to exactly match the query window. A query for `AVG_OVER 1h` can be served from 5-minute rollups by averaging twelve 5-minute values. Smaller rollup windows can serve larger query windows, but not the reverse.

## Rollup retention

Rollup entries follow the same retention policy as raw samples (§7.3). When raw samples are deleted by the retention process, their corresponding rollup entries MUST also be deleted.

When a (function, window) pair is removed from the rollup registry (query frequency dropped below threshold), existing rollup entries for that pair are not deleted immediately. They remain available for queries until they age out through normal retention. New rollup entries are simply no longer computed.

## Configuration

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| AdaptiveRollupWindowHours | REG_DWORD | 48 | 1--168 | Rolling time window in hours over which query frequency is measured. |
| AdaptiveRollupCreateThreshold | REG_DWORD | 50 | 10--10000 | Number of queries with a specific function/window pair required to trigger rollup computation. |
| AdaptiveRollupDropThreshold | REG_DWORD | 5 | 1--1000 | Frequency below which the function/window pair is removed from the registry. MUST be less than the create threshold. |

> [!INFORMATIVE]
> The default rollup thresholds are lower than the adaptive indexing thresholds because rollup computation is cheaper than index creation (it processes data incrementally, window by window) and the query speedup is more dramatic (reading 24 rows instead of 86400 for a daily query at 1-second resolution).

## Persistence

The rollup registry and query frequency counters MUST be persisted across eventd restarts. Existing rollup entries in the `rollups` table are discovered on startup. eventd resumes rollup computation from whatever state the table is in.
