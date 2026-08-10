---
title: Metric Queries
---

## Syntax

```
METRIC name[label_selector] [SINCE time] [UNTIL time] [transform] [aggregation | window_aggregation duration] [clauses...]
```

The primary selector is the metric name with an optional label selector in brackets, placed immediately after `METRIC`. Metric function keywords are split into transforms, scalar aggregations, and window aggregations. All other clauses may appear in any order.

Metric queries have fixed result schemas and do not support SELECT. A metric
query containing SELECT MUST be rejected with a parse error.

## Metric name

The metric name selects which measurement to query:

```
METRIC cpu.usage                    -- the cpu.usage metric
METRIC http.requests.total          -- the http.requests.total metric
```

Glob patterns with `*` are supported. The `*` wildcard matches zero or more of any character, including dots. The same glob semantics as event type patterns (§8.2) apply:

```
METRIC cpu.*                        -- all metrics starting with "cpu."
METRIC disk.usage.*                 -- all disk usage metrics
```

## Label selector

The label selector in brackets controls how multiple time series for the same metric are handled.

### No brackets -- aggregate

When no brackets are present, all matching series are aggregated into a single result using the implicit or explicit aggregation function:

```
METRIC cpu.usage                    -- average across all cores (implicit AVG)
METRIC cpu.usage MAX                -- maximum across all cores
METRIC cpu.usage SINCE 1h ago AVG_OVER 5m -- 5-minute averages across all cores
METRIC http.requests.total RATE SUM -- current total request rate
```

The default scalar aggregation for no-bracket queries without SINCE is AVG. To use a different aggregation, specify it explicitly. No implicit scalar aggregation is added when a window aggregation is present.

For no-SINCE no-bracket queries, eventd computes one latest transformed scalar value per matching series, then aggregates those per-series values using the explicit scalar aggregation or implicit AVG. The result timestamp is the maximum timestamp among the contributing per-series values. A series that cannot produce a value (for example, a RATE query with fewer than two samples) contributes nothing. If no series contributes a value, the query returns no records.

For queries with a SINCE clause, no-bracket aggregation across multiple series MUST use a window aggregation (`AVG_OVER`, `MIN_OVER`, `MAX_OVER`, or `SUM_OVER`). eventd does not synthesize an interpolated merged time series from raw samples with different timestamps. If a SINCE no-bracket query resolves to more than one series and has no window aggregation, the query MUST be rejected at execution time with an error requesting an explicit window aggregation. If it resolves to zero series, it returns no records. If it resolves to exactly one series, it behaves like a single-series bracket query.

### Empty brackets -- break out

Empty brackets return each label combination independently:

```
METRIC cpu.usage[]                  -- latest value per core
METRIC cpu.usage[] SINCE 1h ago     -- time series per core
```

### Label filter -- select specific series

Label filters inside brackets select specific series:

```
METRIC cpu.usage[core="0"]              -- only core 0
METRIC cpu.usage[core="0", host="srv1"] -- core 0 on srv1
```

Label selector entries are comma-separated predicates and are logically ANDed.
The equality predicate may be written as either `=` or `==` inside label
selectors; outside label selectors, `=` is not a comparison operator and MUST
produce a parse error. Other label predicates use the same comparison operators
as WHERE:

```
METRIC http.requests.total[method="GET"]
METRIC disk.usage[device STARTS_WITH "sd"]
```

Label keys use query identifiers. Label values may be quoted strings or unquoted identifiers when they match the lexical rules in §8.1.
Absent labels resolve to NULL using the common field-resolution rules in §8.1.
For example, `[device IS NULL]` selects series that do not have a `device`
label.

## Boot filtering

Metric samples carry `boot_id`, but metric series remain continuous across boots. A metric query MAY filter by `boot_id` using a WHERE predicate:

```
METRIC cpu.usage[] WHERE boot_id == "550e8400-e29b-41d4-a716-446655440000"
```

When a metric query filters by `boot_id`, the query engine MUST execute against raw samples and MUST NOT use adaptive rollups, because rollup rows are boot-agnostic.

## Metric function stages

Metric function keywords execute in fixed stages regardless of their textual position in the query:

1. **Transform** -- `RATE`, `DELTA`, `P50`, `P95`, or `P99`. Transforms operate independently within each selected series and produce scalar values.
2. **Terminal aggregation** -- either a scalar aggregation (`AVG`, `MIN`, `MAX`, `SUM`) or a window aggregation (`AVG_OVER`, `MIN_OVER`, `MAX_OVER`, `SUM_OVER`). A query may specify at most one terminal aggregation. Specifying both a scalar aggregation and a window aggregation in the same query is a parse error.

A query may specify at most one transform. If no transform is specified, counter and gauge samples are already scalar and pass through unchanged.

The metric query pipeline operates on scalar values. Counter and gauge samples
are scalar. Histogram samples are not scalar until a percentile function
(`P50`, `P95`, or `P99`) is applied. A query that resolves to a histogram series
without a percentile function, or that applies `RATE`, `DELTA`, `AVG`, `MIN`,
`MAX`, `SUM`, `AVG_OVER`, `MIN_OVER`, `MAX_OVER`, or `SUM_OVER` directly to a
histogram series, MUST be rejected at execution time when the series type is
resolved. The `samples.value` storage column is a placeholder for histogram
rows and MUST NOT be returned as a metric query value.

After the primary metric name selector, label selector, WHERE predicates, and
access filtering have been applied, the remaining selected series MUST be
type-homogeneous. If the selected set contains more than one metric type, the
query MUST be rejected at execution time with an error requesting a more specific
metric name or `WHERE type == ...` predicate. A selected set with zero series
returns no records.

All metric transform and aggregation outputs are finite float64 values. If a
RATE, DELTA, percentile, scalar aggregation, or window aggregation computation
would produce NaN, positive infinity, or negative infinity, the query MUST fail
with an error rather than returning a non-finite value.

## Transforms

### RATE

Computes the per-second rate of change. Handles counter resets (a decrease in value is treated as a reset, not a negative delta). MUST only be applied to counter-type metrics. Applying RATE to a gauge or histogram series is an error -- the query MUST be rejected at execution time when the series type is resolved.

For non-windowed queries, RATE operates on consecutive samples from the same
series in ascending `(timestamp, id)` order, where `id` is the internal
`samples.id` tiebreaker defined in §7.1. Each pair `(s1, s2)` where
`s2.timestamp` is inside the effective query range and
`s2.timestamp > s1.timestamp` produces one scalar point at `s2.timestamp`. The
adjusted delta is `s2.value - s1.value` when the value increases, or `s2.value`
when the value decreases because the counter reset. The RATE value is
`adjusted_delta / elapsed_seconds`. A pair with non-positive elapsed time
contributes no value. The immediately preceding sample in `(timestamp, id)`
order before the first in-range sample, if one exists, MUST be used as `s1` for
the first in-range sample.

```
METRIC http.requests.total SINCE 1h ago RATE
```

### DELTA

Computes the absolute change between consecutive samples. DELTA uses the same
sample-pair construction as RATE. For each valid pair `(s1, s2)`, the delta is
`s2.value - s1.value`. If the value decreases (counter reset), the delta is
`s2.value` (the counter restarted from zero). MUST only be applied to
counter-type metrics. Applying DELTA to a gauge or histogram series is an error
-- the query MUST be rejected at execution time when the series type is
resolved. DELTA is the unnormalized form of RATE -- RATE divides by elapsed
time to produce a per-second value, DELTA returns the raw adjusted difference.

```
METRIC http.requests.total SINCE 1h ago DELTA
```

### P50, P95, P99

Computes percentiles from histogram-type metrics. Each histogram sample produces one percentile value. MUST only be applied to histogram-type metrics. Applying a percentile function to a counter or gauge series is an error -- the query MUST be rejected at execution time when the series type is resolved.

Percentile transforms use nearest-rank evaluation over the sample's cumulative
bucket counts. For percentile `q` (`0.50`, `0.95`, or `0.99`), compute
`rank = ceil(q * total_count)`. The percentile value is the first bucket
boundary whose cumulative count is greater than or equal to `rank`. Histogram
samples with `total_count == 0` produce no percentile value. If `rank` is above
the final explicit bucket count, the percentile lies in the overflow bucket
above the largest configured boundary; v0.23 produces no percentile value for
that sample rather than returning a non-finite value.

```
METRIC request.duration P95
METRIC request.duration[origin="loregd"] SINCE 1h ago P99
```

## Scalar aggregations

### AVG, MIN, MAX, SUM

Aggregates scalar values into one output value. These functions MUST NOT be
applied directly to histogram series. For no-SINCE no-bracket queries, the
aggregation is across the latest transformed value from each matching series as
described above. For bracket queries, the aggregation is over time within each
selected series. For no-bracket queries with SINCE, scalar aggregation is only
valid when the selector resolves to zero or one series; a selector resolving to
more than one series MUST use a window aggregation instead.

```
METRIC cpu.usage AVG                            -- average of latest values across all cores
METRIC http.requests.total RATE SUM             -- sum of latest per-series rates
METRIC cpu.usage[] SINCE 1d ago AVG             -- average over the day, per core
METRIC cpu.usage[core="0"] SINCE 1h ago MIN     -- minimum value in the last hour for core 0
```

If no scalar values contribute to an aggregation, the query returns no record for
that output group. If scalar values do contribute, the output timestamp is the
maximum timestamp among the contributing scalar values. For RATE and DELTA
values, this is the timestamp of the later sample in the contributing pair.

## Window aggregations

Window aggregations aggregate scalar values into fixed time windows. They appear
after an optional transform, take a duration argument, and require a SINCE
clause. A query with a window aggregation but no SINCE MUST be rejected with a
parse error. The duration defines fixed windows aligned to Unix epoch multiples
of that duration; the output timestamp is the window start timestamp.

Window aggregations are terminal aggregations and MUST NOT be combined with
scalar aggregations in the same query. `AVG` and `AVG_OVER` are different
keywords: `AVG` produces one scalar result for the selected time range, while
`AVG_OVER` produces one result per non-empty window.

### AVG_OVER, MIN_OVER, MAX_OVER, SUM_OVER

Divides the time range into fixed windows of the specified duration and computes the aggregate per window:

```
METRIC cpu.usage SINCE 1d ago AVG_OVER 1h       -- hourly averages over the last day
METRIC cpu.usage[] SINCE 1d ago AVG_OVER 5m     -- 5-minute averages per core
METRIC http.requests.total SINCE 1h ago RATE SUM_OVER 5m -- total request rate per 5-minute window
METRIC request.duration P95 SINCE 1h ago AVG_OVER 5m  -- 5-min averaged P95
```

Window aggregations produce one data point per non-empty window, reducing data density for trend visualisation. Windows with no contributing scalar values are omitted from the result set.

For no-bracket queries, window aggregations define the common time grid used to aggregate across multiple matching series. For raw counter/gauge values and percentile-transformed histogram values, each output window contains the scalar sample values whose timestamps fall within that window. `AVG_OVER` computes the average of those values, `MIN_OVER` the minimum, `MAX_OVER` the maximum, and `SUM_OVER` the sum. No interpolation is performed between samples.

For RATE or DELTA with a window aggregation, eventd first computes at most one
counter-derived scalar per selected series per output window:

- DELTA is the sum of reset-adjusted deltas for consecutive sample pairs in
  `(timestamp, id)` order whose later sample is inside the window.
- RATE is that window DELTA divided by the covered elapsed seconds for those
  contributing pairs.
- The immediately preceding sample in `(timestamp, id)` order before the first
  in-window sample, if one exists, MUST be used as the baseline for the first
  in-window pair.
- A sample pair with non-positive elapsed time does not contribute to either the
  DELTA or the covered elapsed time.
- A series with no contributing pairs for a window contributes no scalar value
  for that window.

The terminal window aggregation then combines those per-series window scalars.
For example, `RATE SUM_OVER 5m` sums the per-series 5-minute rates, and
`RATE AVG_OVER 5m` averages the per-series 5-minute rates. For a selector that
resolves to exactly one series, `RATE AVG_OVER`, `RATE MIN_OVER`,
`RATE MAX_OVER`, and `RATE SUM_OVER` all return that series' window RATE value;
the same rule applies to DELTA.

For bracket queries, window aggregations are computed independently for each selected series, and labels remain present in result rows. For no-bracket queries, the aggregation output is a single series and labels are omitted from result rows unless the selector resolves to exactly one series.

If adaptive rollups (§7.4) exist for the requested rollup-eligible function and window size, the query engine serves results from the pre-computed rollup table instead of scanning raw samples. This is transparent -- the result is identical, only the performance differs. Rollups MUST NOT be used for percentile queries or for queries that filter by `boot_id`.

## Without SINCE

When no SINCE clause is present, the query returns the latest value:

```
METRIC cpu.usage                    -- latest average across cores
METRIC cpu.usage[]                  -- latest value per core
METRIC cpu.usage[core="0"]          -- latest value for core 0
```

"Latest" is evaluated per series using `(timestamp, id)` ordering. For bracket queries, each selected series uses its own most recent sample in that order. For no-bracket queries, eventd computes the latest value for each matching series and aggregates those values into one result; the result timestamp is the maximum timestamp among contributing series.

For transforms that require multiple samples (RATE, DELTA), a query without SINCE uses the latest valid consecutive sample pair in `(timestamp, id)` order with positive elapsed time to compute a single instantaneous value. For example, `METRIC http.requests.total RATE` computes the per-second rate for the latest valid counter sample pair. If no valid pair exists for a series, the query returns no result for that series.

## Result format

Metric results are flat maps, consistent with event and log results. Labels
appear as top-level keys. Metric ingestion rejects labels whose keys collide with
fixed metric result fields (`timestamp`, `boot_id`, `name`, `type`, `value`), so
flat metric results cannot contain ambiguous label/fixed-field keys. The `type`
field is the source series type string (`"counter"`, `"gauge"`, or
`"histogram"`). Raw counter and gauge sample results include `boot_id`:

```
{timestamp: 1714000000000000000, boot_id: "{550e8400-e29b-41d4-a716-446655440000}", name: "cpu.usage", type: "gauge", core: "0", value: 42.7}
{timestamp: 1714000015000000000, boot_id: "{550e8400-e29b-41d4-a716-446655440000}", name: "cpu.usage", type: "gauge", core: "0", value: 38.2}
```

For raw counter/gauge time series results, one record is returned per sample.
For RATE and DELTA time series results, one record is returned per valid sample
pair, timestamped at the later sample. For percentile histogram results, one
record is returned per histogram sample that produces a finite percentile value;
empty samples and samples whose percentile falls in the overflow bucket
contribute no record. For aggregated results (e.g., `METRIC cpu.usage AVG`), one
record with the aggregated value is returned. The `timestamp` field is the
timestamp defined by the aggregation rule: the maximum contributing scalar
timestamp for scalar aggregations, and the window start timestamp for window
aggregations.

Histogram results are always scalar percentile results. A histogram query result
contains the percentile value in the `value` field; the original bucket
boundaries, cumulative counts, total count, and sum are not returned by the
metric query language in v0.23.

Window aggregation results include the window start timestamp:

```
{timestamp: 1714000000000000000, name: "cpu.usage", type: "gauge", core: "0", value: 41.2}  -- 5min avg
{timestamp: 1714000300000000000, name: "cpu.usage", type: "gauge", core: "0", value: 39.8}  -- next window
```

If no SORT is present, metric time-series and window-aggregation results are
ordered chronologically by timestamp ascending, with deterministic tiebreakers as
defined in §8.1. No-SINCE latest-value and scalar aggregation queries use the
same tiebreakers, but commonly return only one row or one row per selected
series.

## Examples

Current CPU usage per core:
```
METRIC cpu.usage[]
```

Average CPU over the last day with hourly windows:
```
METRIC cpu.usage SINCE 1d ago AVG_OVER 1h
```

Current total request rate:
```
METRIC http.requests.total RATE SUM
```

Request rate for loregd in the last hour:
```
METRIC http.requests.total[service="loregd"] SINCE 1h ago RATE
```

Total request rate over the last hour with 5-minute windows:
```
METRIC http.requests.total SINCE 1h ago RATE SUM_OVER 5m
```

P95 request latency, 5-minute windows:
```
METRIC request.duration[origin="loregd"] SINCE 1h ago P95 AVG_OVER 5m
```

All disk usage metrics:
```
METRIC disk.usage.*[]
```

CPU usage during access denied events:
```
METRIC cpu.usage[] SINCE 1h ago WHERE EVENT kacs.access_denied EXISTS
```
