---
title: Metric Queries
---

## Syntax

```
METRIC name[label_selector] [SINCE time] [UNTIL time] [function] [window_function] [clauses...]
```

The primary selector is the metric name with an optional label selector in brackets, placed immediately after `METRIC`. Functions and window functions transform the values. All other clauses may appear in any order.

## Metric name

The metric name selects which measurement to query:

```
METRIC cpu.usage                    -- the cpu.usage metric
METRIC http.requests.total          -- the http.requests.total metric
```

Glob patterns with `*` are supported:

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
METRIC cpu.usage SINCE 1h ago       -- averaged time series across all cores
```

The default aggregation function for no-bracket queries is AVG. To use a different aggregation, specify it explicitly.

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

Label values support the same comparison operators as WHERE:

```
METRIC http.requests.total[method="GET"]
METRIC disk.usage[device STARTS_WITH "sd"]
```

## Value functions

Value functions transform metric values. They appear after the metric selector. At most one value function may be specified per query.

### RATE

Computes the per-second rate of change. Handles counter resets (a decrease in value is treated as a reset, not a negative delta). MUST only be applied to counter-type metrics.

```
METRIC http.requests.total SINCE 1h ago RATE
```

### DELTA

Computes the absolute change between consecutive samples. Handles counter resets. Useful for "how many in this interval" rather than "per second."

```
METRIC http.requests.total SINCE 1h ago DELTA
```

### P50, P95, P99

Computes percentiles from histogram-type metrics. Each histogram sample produces one percentile value. MUST only be applied to histogram-type metrics.

```
METRIC request.duration P95
METRIC request.duration[origin="loregd"] SINCE 1h ago P99
```

### AVG, MIN, MAX, SUM

Aggregates values. For no-bracket queries, aggregates across all matching series. For bracket queries, aggregates over time within each series. For queries with SINCE, operates over the time range.

```
METRIC cpu.usage AVG                            -- average across all cores, latest window
METRIC cpu.usage[] SINCE 1d ago AVG             -- average over the day, per core
METRIC cpu.usage[core="0"] SINCE 1h ago MIN     -- minimum value in the last hour for core 0
```

## Window functions

Window functions aggregate values into fixed time windows. They appear after a value function (or alone) and take a duration argument.

### AVG_OVER, MIN_OVER, MAX_OVER

Divides the time range into fixed windows of the specified duration and computes the aggregate per window:

```
METRIC cpu.usage SINCE 1d ago AVG_OVER 1h       -- hourly averages over the last day
METRIC cpu.usage[] SINCE 1d ago AVG_OVER 5m     -- 5-minute averages per core
METRIC request.duration P95 SINCE 1h ago AVG_OVER 5m  -- 5-min averaged P95
```

Window functions produce one data point per window, reducing data density for trend visualisation.

If adaptive rollups (§7.4) exist for the requested function and window size, the query engine serves results from the pre-computed rollup table instead of scanning raw samples. This is transparent -- the result is identical, only the performance differs.

## Without SINCE

When no SINCE clause is present, the query returns the latest value:

```
METRIC cpu.usage                    -- latest average across cores
METRIC cpu.usage[]                  -- latest value per core
METRIC cpu.usage[core="0"]          -- latest value for core 0
```

"Latest" means the most recent sample in the metric store.

## Result format

Metric results are flat maps, consistent with event and log results. Labels appear as top-level keys:

```
{timestamp: 1714000000000000000, name: "cpu.usage", core: "0", value: 42.7}
{timestamp: 1714000015000000000, name: "cpu.usage", core: "0", value: 38.2}
```

For time series results, one record per sample. For aggregated results (e.g., `METRIC cpu.usage AVG`), one record with the aggregated value.

Windowed results include the window start timestamp:

```
{timestamp: 1714000000000000000, name: "cpu.usage", core: "0", value: 41.2}  -- 5min avg
{timestamp: 1714000300000000000, name: "cpu.usage", core: "0", value: 39.8}  -- next window
```

## Examples

Current CPU usage per core:
```
METRIC cpu.usage[]
```

Average CPU over the last day with hourly windows:
```
METRIC cpu.usage SINCE 1d ago AVG_OVER 1h
```

Request rate for loregd in the last hour:
```
METRIC http.requests.total[service="loregd"] SINCE 1h ago RATE
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
