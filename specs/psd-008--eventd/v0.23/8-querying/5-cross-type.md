---
title: Cross-Type Filtering
---

## Overview

Cross-type filtering allows a query on one data type to be filtered by conditions on another data type. This is the primary mechanism for correlating events, logs, and metrics without explicit JOINs.

Cross-type filters appear as WHERE clauses with a type keyword (METRIC, EVENT, LOG) indicating the data source for the condition.

## WHERE METRIC

Filters records to time periods when a metric condition holds. Available in EVENTS and LOGS queries.

```
EVENTS kacs.* SINCE 1h ago WHERE METRIC cpu.usage[core="0"] > 80
LOGS FROM loregd SINCE 1h ago WHERE METRIC mem.usage[service="loregd"] > 90
```

### Semantics

The query engine pre-computes the time ranges where the metric condition is true by scanning the metric store for matching samples. These time ranges are then applied as additional timestamp filters on the primary data source.

The effective query window is `[SINCE, UNTIL)`. Metric cross-type filters scan
the selected series in `(timestamp, id)` order, where `id` is the internal
`samples.id` tiebreaker defined in §7.1. eventd MUST include the latest sample
before `SINCE` as the initial state if such a sample exists. A sample's value is
considered active over `[sample.timestamp, next_sample.timestamp)`, clipped to
the effective query window. If there is no sample before `SINCE`, no metric
condition is true before the first in-window sample. A final sample remains
active through `UNTIL`.

Duplicate timestamps are resolved by `(timestamp, id)` ordering. Earlier samples
with the same timestamp create zero-width intervals; the last sample at that
timestamp is the active value until the next sample with a later timestamp.
This interpolation assumes the metric condition holds between samples.

The metric condition uses the same comparison operators as standard WHERE
clauses. In v0.23, `WHERE METRIC` operates only on raw scalar samples from
counter and gauge series. Metric transform keywords (`RATE`, `DELTA`, `P50`,
`P95`, `P99`), scalar aggregation keywords, and window aggregation keywords are
not valid in `WHERE METRIC` conditions. Histogram series are not raw scalar
series, so a `WHERE METRIC` condition that resolves to a histogram series MUST
be rejected.

The metric selector uses the same metric name and label-selector syntax as
METRIC queries, but v0.23 cross-type metric filters MUST resolve to zero or one
time series. A selector that resolves to zero series produces no true time
ranges. A selector that resolves to more than one series MUST be rejected with
an error requesting a bracketed or more specific label selector.

```
WHERE METRIC cpu.usage[core="0"] > 90           -- specific series
WHERE METRIC disk.io.utilisation[device="sda"] > 95
```

## WHERE EVENT

Filters records to time periods when events of a specified type exist. Available in LOGS and METRIC queries.

```
LOGS FROM loregd SINCE 1h ago WHERE EVENT kacs.access_denied EXISTS
METRIC cpu.usage[] SINCE 1h ago WHERE EVENT synthetic.storage_error EXISTS
```

The `EXISTS` keyword indicates that the condition is satisfied when at least one event of the specified type exists within the relevant time window. The event type supports glob patterns:

```
WHERE EVENT kacs.* EXISTS                       -- any KACS event
WHERE EVENT synthetic.gap EXISTS                -- gap records
```

## WHERE LOG

Filters records to time periods when matching log entries exist. Available in EVENTS and METRIC queries.

```
EVENTS kacs.* SINCE 1h ago WHERE LOG loregd CONTAINING "error" EXISTS
```

The LOG condition specifies an origin and optionally a CONTAINING text filter.

## Time window resolution

Cross-type conditions are evaluated against the metric sample interval or event density, not per-row of the primary data source. The time ranges where the condition holds are computed once and applied as a filter.

For metric conditions, the resolution is the selected series' sample interval (typically 15 seconds). A metric condition like `WHERE METRIC cpu.usage[core="0"] > 80` means "during periods where the most recent cpu.usage sample for core 0 exceeded 80."

For event and log `EXISTS` conditions, `CrossTypeWindowMs` defines a centered
half-open window around each primary record or sample timestamp. Let
`W = CrossTypeWindowMs * 1_000_000` nanoseconds. Let `lower = floor(W / 2)` and
`upper = W - lower`. For a primary timestamp `t`, the condition is true if at
least one matching event or log record has:

```
timestamp >= t - lower
timestamp <  t + upper
```

Equivalently, during pre-computation a matching event or log record at timestamp
`e` contributes the true range `[e - lower, e + upper)`. If `W` is odd, the
extra nanosecond is on the upper side so the total window width remains exactly
`W`.

The window size for event and log existence checks is configurable:

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| CrossTypeWindowMs | REG_DWORD | 15000 | 1000--300000 | Time window in milliseconds for cross-type event and log existence checks. |

## Lookback limit

Cross-type filter pre-computation scans the referenced store for the query's time range. Scanning large time ranges (weeks or months of metric samples) is expensive. eventd MUST enforce a maximum lookback period for cross-type conditions:

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| CrossTypeMaxLookbackSeconds | REG_DWORD | 604800 | 3600--2592000 | Maximum time range in seconds that a cross-type filter may scan. Default is 7 days. |

If the query's effective time range (from SINCE to UNTIL, or SINCE to now)
exceeds `CrossTypeMaxLookbackSeconds`, the cross-type filter MUST be rejected
with an error indicating the time range is too large. The error MUST suggest
narrowing the range with SINCE/UNTIL.

A query with no SINCE clause and a cross-type filter MUST be rejected -- unbounded cross-type scans are never permitted.

## Performance

Cross-type filters require reading from multiple stores. The cross-type condition is evaluated first to produce time ranges, then the primary query is executed with additional timestamp filters. This is efficient when the cross-type condition is selective (narrow time ranges), and expensive when the condition is broadly true (e.g., CPU above 10% for the entire query window).

Metric cross-type filters are evaluated from raw samples for the single selected series. Adaptive rollups are not used for cross-type metric filters in v0.23, because the filter needs exact sample-boundary intervals rather than aggregate windows.

Cross-type WHERE predicates are tracked by the adaptive indexing system, same as standard WHERE predicates.
