---
title: Adaptive Rollups
---

## Purpose

Aggregate metric queries (AVG_OVER, MIN_OVER, MAX_OVER, SUM_OVER, RATE, DELTA,
and scalar AVG/MIN/MAX/SUM over raw counter/gauge time ranges) require reading
and processing raw samples. For large time ranges, this means scanning thousands
or millions of rows. Pre-computing the results of common composable aggregate
queries and storing them as rollups dramatically reduces query time.

Adaptive rollups apply the same principle as adaptive indexing for events: monitor which query patterns occur frequently, pre-compute the results in the background, and serve queries from the rollups when available.

## Rollup model

A rollup is a pre-computed aggregate stored in a dedicated table. Each rollup is defined by:

- **Series** -- which time series the rollup applies to.
- **Function** -- the per-series rollup function (AVG, MIN, MAX, SUM, RATE, DELTA).
- **Window** -- the time window size (e.g., 5m, 1h, 1d).

A rollup for `cpu.usage[core="0"] AVG_OVER 1h` stores one pre-computed average value per hour for that specific series.

Rollups are always per-series. Cross-series no-bracket window aggregations are
computed by reading or composing the per-series rollup rows for each matching
series and then applying the query's terminal window aggregation across those
per-series values.

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
| `sample_count` | INTEGER NOT NULL | Number of scalar inputs that contributed to this value. For AVG/MIN/MAX/SUM this is the number of raw scalar samples. For RATE/DELTA this is the number of valid sample pairs. Allows the query engine to assess rollup quality (a window with 1 input is less reliable than one with 60). |
| `covered_ns` | INTEGER NOT NULL | For RATE and DELTA rollups, the sum of elapsed nanoseconds across contributing sample pairs. For AVG/MIN/MAX/SUM rollups, this MUST be 0. |

A unique constraint MUST exist on `(series_id, function, window_seconds, window_start)`.

An index MUST exist on `(series_id, function, window_seconds, window_start)` to support efficient rollup lookups.

`sample_count` MUST be greater than zero for every rollup row. `value` MUST be a
finite float64. `covered_ns` MUST be greater than zero for RATE and DELTA rows
and MUST be zero for AVG, MIN, MAX, and SUM rows.

## Function identifiers

| Value | Function |
|---|---|
| 0 | AVG |
| 1 | MIN |
| 2 | MAX |
| 3 | SUM |
| 4 | RATE |
| 5 | DELTA |

Percentile functions (P50, P95, P99) are excluded from rollups. Percentiles are not composable -- the P95 of twelve 5-minute P95 values is not the P95 of the full hour. Percentile queries always compute from raw histogram samples.

Future versions MAY add histogram rollups that store merged bucket counts and compute percentiles from the rolled-up distribution. Such histogram rollups are a distinct storage model and are not represented by the scalar `rollups` table in v0.23.

## Rollup registry

eventd MUST maintain a global rollup registry -- a set of (function, window) pairs that should be pre-computed across all series. The registry is computed from query frequency tracking, analogous to the global desired index set for events.

For each metric query that includes a rollup-eligible scalar aggregation or
window aggregation, eventd records the per-series rollup function and window
size:

- `AVG_OVER`, `MIN_OVER`, `MAX_OVER`, and `SUM_OVER` map to the AVG, MIN, MAX,
  and SUM rollup functions when no RATE or DELTA transform is present. The query
  window duration is the recorded window size.
- When RATE or DELTA is present with a window aggregation, the transform (`RATE`
  or `DELTA`) is the rollup function. The query's terminal window aggregation is
  applied after the per-series rollup values are read. The query window duration
  is the recorded window size.
- Scalar `AVG`, `MIN`, `MAX`, and `SUM` over raw counter/gauge samples with a
  `SINCE` clause record the same AVG, MIN, MAX, or SUM rollup function using
  `AdaptiveRollupScalarWindowSeconds` as the recorded window size.

Percentile functions are not recorded. Non-window RATE or DELTA scalar
aggregations are not recorded because the RATE/DELTA rollup value is a
window-level counter rate/delta, not the raw sequence of per-pair scalar values
that scalar aggregation over a transformed time series uses in §8.4.

When a (function, window) pair's query frequency exceeds the creation threshold
over the rolling time window, it is added to the rollup registry. When it falls
below the removal threshold, it is removed.

The rollup registry is global -- it applies to all compatible series. If hourly
averages are frequently queried for any metric, hourly averages are pre-computed
for all active counter and gauge series. Incompatible series are skipped as
defined below.

## Rollup computation

Rollup computation runs on a background thread during periods of low write activity. For each (function, window) pair in the registry, the background thread:

1. Identifies time windows that have raw samples but no rollup entry.
2. Reads the raw samples for those windows.
3. Computes the aggregate value.
4. Inserts the rollup entry.

Only completed windows are rolled up. The current (still-accumulating) window is not pre-computed -- it is always computed from raw samples at query time.

For AVG/MIN/MAX/SUM rollups, the input values are raw counter or gauge sample
values whose timestamps fall within the window. Histogram samples are excluded
from scalar rollups in v0.23. RATE and DELTA rollups are computed only for
counter series. Rollup computation MUST skip series whose type is incompatible
with the rollup function.

For RATE and DELTA rollups, eventd uses the same counter-window rule as §8.4:
each completed window considers consecutive counter sample pairs in
`(timestamp, id)` order whose later sample timestamp is inside the window, uses
the immediately preceding sample in that order before the first in-window sample
as the baseline for the first in-window pair when such a sample exists, and
ignores pairs with non-positive elapsed time. DELTA rollup `value` is the sum of
reset-adjusted deltas. RATE rollup `value` is that DELTA divided by
`covered_ns` converted to seconds. If a window has no contributing scalar inputs
or, for RATE, a zero `covered_ns`, no rollup row is inserted for that
(series, function, window, window_start).

Rollup computation MUST be cancellable. If write pressure rises, the computation is aborted and resumed later. The same cancellation mechanism as adaptive index creation (§3.3) applies.

## Query integration

When executing a metric query with a rollup-eligible scalar aggregation or window
aggregation, the query engine MUST check whether a matching rollup exists. If a
rollup covers the requested per-series rollup function, window size, and time
range, and the query does not filter by `boot_id`:

- The query reads from the `rollups` table instead of the `samples` table.
- One row per time window instead of hundreds of raw samples per window.

If the rollup partially covers the time range (e.g., rollups exist for all but
the most recent incomplete window), the query reads rollups for complete windows
that are fully contained in the effective query range and computes the remaining
prefix or suffix from raw samples. This raw edge handling is required for exact
results when the query's `SINCE` or `UNTIL` bound is not aligned to the rollup
window.

If no matching rollup exists, the query filters by `boot_id`, the query uses a
percentile function, or the query is a non-window RATE/DELTA scalar aggregation,
the query falls back to raw sample computation. The result is identical --
rollups are a transparent optimisation.

Rollup window sizes do not need to exactly match the query window for composable functions. A query for `AVG_OVER 1h` can be served from 5-minute AVG rollups by computing a weighted average from twelve 5-minute values (weighted by `sample_count`). MIN and MAX compose directly by taking the min/max across sub-windows. SUM and DELTA compose by addition. RATE composes by covered time: `composed_rate = sum(subrate * sub_covered_ns) / sum(sub_covered_ns)`. Counter resets are handled during rollup computation -- each stored RATE/DELTA row already reflects reset-adjusted deltas. Composition operates on these adjusted values and does not need to handle resets again. Smaller rollup windows can serve larger query windows, but not the reverse.

For cross-series no-bracket window queries, composition occurs per series first.
The terminal window aggregation is then applied across matching series. For
non-transform `AVG_OVER`, per-series AVG rollups are combined across series
weighted by `sample_count`, because the query semantics are the average of all
scalar sample values in the window. For RATE or DELTA with `AVG_OVER`, the
terminal average is an unweighted average of the per-series window RATE or DELTA
values, because each selected series contributes at most one scalar value per
window under §8.4.

## Rollup retention

Rollup entries follow the same retention policy as raw samples (§7.3). When raw samples are deleted by the retention process, their corresponding rollup entries MUST also be deleted.

When a (function, window) pair is removed from the rollup registry (query frequency dropped below threshold), existing rollup entries for that pair are not deleted immediately. They remain available for queries until they age out through normal retention. New rollup entries are simply no longer computed.

## Configuration

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| AdaptiveRollupWindowHours | REG_DWORD | 48 | 1--168 | Rolling time window in hours over which query frequency is measured. |
| AdaptiveRollupScalarWindowSeconds | REG_DWORD | 300 | 60--86400 | Base rollup window used when scalar AVG/MIN/MAX/SUM range queries trigger rollup creation. |
| AdaptiveRollupCreateThreshold | REG_DWORD | 50 | 10--10000 | Number of queries with a specific function/window pair required to trigger rollup computation. |
| AdaptiveRollupDropThreshold | REG_DWORD | 5 | 1--1000 | Frequency below which the function/window pair is removed from the registry. MUST be less than the create threshold. |

> [!INFORMATIVE]
> The default rollup thresholds are lower than the adaptive indexing thresholds because rollup computation is cheaper than index creation (it processes data incrementally, window by window) and the query speedup is more dramatic (reading 24 rows instead of 86400 for a daily query at 1-second resolution).

## Persistence

The rollup registry and query frequency counters MUST be persisted across eventd restarts. Existing rollup entries in the `rollups` table are discovered on startup. eventd resumes rollup computation from whatever state the table is in.
