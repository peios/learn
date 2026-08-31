---
title: Metric Queries
description: METRIC mode evaluates rather than searches — series selection, homogeneity, transforms, percentiles and scalar aggregations.
---

```text
METRIC name[label_selector] [transform] [aggregation] [clauses…]
```

Metric mode evaluates rather than searches. A collector MUST reject
`SELECT` in metric mode: the result schemas are fixed (§3.22).

## Selecting series

The primary selector is a metric name, optionally followed by a label
selector in brackets. The name supports `*` with the same glob semantics
as an event type pattern (§3.23).

```text
METRIC cpu.usage
METRIC cpu.*
```

The brackets — present, absent, or present and empty — decide how
multiple matching series are handled, and this is the distinction that
governs the rest of the mode.

**No brackets — aggregate.** Every matching series is combined into one
result.

```text
METRIC cpu.usage                    -- average across all cores
METRIC cpu.usage MAX                -- maximum across all cores
```

**Empty brackets — break out.** Each series is returned separately.

```text
METRIC cpu.usage[]                  -- latest value per core
METRIC cpu.usage[] SINCE 1h ago     -- a time series per core
```

**Filled brackets — select.** Only series matching the label predicates.

```text
METRIC cpu.usage[core="0"]
METRIC cpu.usage[core="0", host="srv1"]
METRIC disk.usage[device STARTS_WITH "sd"]
```

Label predicates are comma-separated and combined with `AND`. They use
the operators of §3.20, and within a label selector `=` is accepted as
equality alongside `==`. Label keys are identifiers; values are
identifiers or quoted strings. An absent label resolves to null, so
`[device IS NULL]` selects the series that carry no `device` label.

## Homogeneity

After the name, the label selector, `WHERE` predicates and access
filtering have been applied, the remaining series MUST be **of one
type**. A collector MUST reject a selection spanning more than one type
at execution time, with an error asking for a narrower name or an
explicit `WHERE type == …`.

A selection resolving to zero series returns no records — a successful
query with an empty result, not an error.

The rule exists because every function below is defined on one type. A
selection mixing counters and gauges has no meaningful rate, and a
selection mixing either with histograms has no meaningful value at all.

## Function stages

Function keywords execute in fixed stages regardless of where they were
written:

1. **Transform** — `RATE`, `DELTA`, `P50`, `P95` or `P99`. Operates
   within each series independently and produces scalars. At most one
   per query.
2. **Terminal aggregation** — either a **scalar** aggregation (`AVG`,
   `MIN`, `MAX`, `SUM`) or a **window** aggregation (`AVG_OVER`,
   `MIN_OVER`, `MAX_OVER`, `SUM_OVER`). At most one per query;
   specifying both a scalar and a window aggregation is a parse error.

The pipeline ordinarily operates on scalars throughout. Counter and gauge
samples are already scalar; a histogram sample is not scalar until a
percentile function has been applied. The sole exceptional result is a
tagged percentile overflow, whose propagation is defined below. A collector
MUST therefore reject, at
execution time when the type is known, a query that resolves to a
histogram series without a percentile function, or that applies `RATE`,
`DELTA`, or any scalar or window aggregation directly to one.

Every numeric output is a **finite** binary64. If any computation would
produce NaN or an infinity, the query MUST fail with an error rather than
returning it. The null in a tagged percentile-overflow result is not a
numeric output.

## Transforms

### RATE and DELTA

`DELTA` is the change between consecutive samples; `RATE` is that change
per second. Both apply **only to counter series**, and a collector MUST
reject them on a gauge or histogram at execution time.

Both use the same pair construction. Samples of one series are taken in
ascending timestamp order, with a deterministic tiebreaker among samples
sharing a timestamp. Each consecutive pair `(s1, s2)` whose `s2` falls
inside the effective query range, and where `s2` is later than `s1`,
produces one scalar at `s2`'s timestamp. The **immediately preceding
sample before the first in-range one MUST be used as `s1`** for the
first pair, when such a sample exists — without it the first point of
every range would be missing, and a chart would show a notch at the
start of every window.

The adjusted delta is `s2 - s1` when the value rose, and `s2` alone when
it fell, because a fall means the counter restarted from zero. `RATE` is
that adjusted delta divided by the elapsed seconds. A pair with
non-positive elapsed time contributes nothing.

```text
METRIC http.requests.total SINCE 1h ago RATE
METRIC http.requests.total SINCE 1h ago DELTA
```

### P50, P95, P99

Percentiles of **histogram series only**; a collector MUST reject them
on a counter or gauge at execution time. Each histogram sample yields
one value.

Evaluation is nearest-rank over the sample's cumulative counts: for
percentile `q`, compute `rank = ceil(q × total_count)`, and take the
first boundary whose cumulative count is at least `rank`.

A sample with `total_count == 0` yields no record. A sample whose rank
falls **above the final cumulative count** — meaning the percentile lies
in the overflow region above the highest boundary — yields a record with
`value` null and `overflow` true. The distribution proves that the
percentile exceeds the highest boundary but does not record a finite value
for it. `overflow` is absent from ordinary percentile results.

```text
METRIC request.duration P95
METRIC request.duration[origin="loregd"] SINCE 1h ago P99
```

> [!NOTE]
> The overflow marker is why a producer's highest bucket boundary still
> matters (§3.10). It prevents a `P99` above that boundary from looking like
> no data, but it cannot recover the value the histogram did not locate. An
> operator seeing `overflow: true` is seeing a mis-provisioned histogram.

## Scalar aggregations

`AVG`, `MIN`, `MAX` and `SUM` reduce scalars to one value. They MUST NOT
be applied to a histogram series directly.

What they aggregate *over* depends on the brackets:

- **Bracketed**, so one result per series: over time, within each series.
- **Unbracketed without `SINCE`**: over the latest transformed value of
  each matching series. The result timestamp is the greatest of the
  contributing timestamps. A series that cannot produce a value — a
  `RATE` with fewer than two samples, say — contributes nothing.
- **Unbracketed with `SINCE`**: valid only when the selector resolves to
  zero or one series. More than one MUST be rejected with an error
  asking for a window aggregation.

```text
METRIC cpu.usage AVG
METRIC http.requests.total RATE SUM
METRIC cpu.usage[] SINCE 1d ago AVG
METRIC cpu.usage[core="0"] SINCE 1h ago MIN
```

The unbracketed default aggregation, when no `SINCE` and no explicit
function is given, is `AVG`. No implicit scalar aggregation is added
when a window aggregation is present.

If nothing contributes to an aggregation, the query returns no record
for that output group. Otherwise the output timestamp is the greatest
contributing timestamp — for `RATE` and `DELTA`, the later sample of the
contributing pair.

If any contributing percentile result has `overflow` true, a scalar
aggregation MUST conservatively return `value` null and `overflow` true.
It MUST NOT ignore the result and compute from the remaining finite values.

### Why unbracketed plus SINCE needs a window

A collector MUST NOT synthesise a merged time series from samples that
do not share timestamps.

Two series sampled at unrelated moments cannot be averaged point by
point without inventing values between the points, and interpolation
would make the collector responsible for a number nobody measured. A
window aggregation supplies the common time grid explicitly, which is
why it is required rather than assumed.

## Window aggregations

`AVG_OVER`, `MIN_OVER`, `MAX_OVER` and `SUM_OVER` take a duration and
produce one value per window. They **require `SINCE`**; a collector MUST
reject a window aggregation without one as a parse error.

Windows are fixed and aligned to Unix-epoch multiples of the duration —
not to the query's start — so that the same window boundaries fall in
the same places for every query. The output timestamp is the window
start. Windows with nothing in them are omitted rather than emitted as
null.

```text
METRIC cpu.usage SINCE 1d ago AVG_OVER 1h
METRIC cpu.usage[] SINCE 1d ago AVG_OVER 5m
METRIC http.requests.total SINCE 1h ago RATE SUM_OVER 5m
METRIC request.duration P95 SINCE 1h ago AVG_OVER 5m
```

`AVG` and `AVG_OVER` are different keywords and a collector MUST NOT
treat them as synonyms: `AVG` produces one value for the range,
`AVG_OVER` one per window.

For raw and percentile-transformed values, a window contains the scalars
whose timestamps fall inside it, and the function is applied to those.
No interpolation is performed.

If a window contains a percentile result with `overflow` true, its output
MUST also carry `value` null and `overflow` true. This propagation applies
again when per-series window results are combined.

For `RATE` and `DELTA` with a window aggregation, each series first
produces **at most one scalar per window**: the window `DELTA` is the
sum of reset-adjusted deltas for pairs whose later sample is in the
window, and the window `RATE` is that divided by the elapsed seconds
those pairs covered. The preceding-sample rule applies to the first pair
of each window. The terminal aggregation then combines the per-series
window values — so `RATE SUM_OVER 5m` sums the series' five-minute
rates, and `RATE AVG_OVER 5m` averages them. Where the selector resolves
to exactly one series, all four window functions return that series'
window value.

Bracketed window queries keep labels in the result rows. Unbracketed
ones omit them, unless the selector resolved to exactly one series.

## Without SINCE

With no `SINCE`, the query returns the **latest** value.

```text
METRIC cpu.usage[core="0"]
METRIC cpu.usage[]
METRIC cpu.usage
```

"Latest" is per series, by timestamp with the deterministic tiebreaker.
For `RATE` and `DELTA`, it is the latest valid consecutive pair with
positive elapsed time; a series with no such pair returns nothing.

## Boot filtering

Samples carry `boot_id` but series continue across boots (§3.13). A
query MAY restrict to one boot:

```text
METRIC cpu.usage[] WHERE boot_id == "550e8400-e29b-41d4-a716-446655440000"
```

A boot-filtered metric query MUST be evaluated from raw samples. A
collector MUST NOT serve one from any pre-computed aggregate that is not
itself partitioned by boot.

## Results

One record per raw sample; one per valid pair for `RATE` and `DELTA`,
timestamped at the later sample; one per non-empty histogram sample after
a percentile transform, including an explicit overflow record; one per
window for window aggregations; one for a scalar aggregation.

A finite histogram result carries only the percentile in `value`. An
overflow result carries `value` null and `overflow` true. The boundaries,
counts, total and sum are **not** returned by the query language in this
revision, in any mode.

```text
{timestamp: 1714000000000000000, boot_id: "{550e8400-…}", name: "cpu.usage", type: "gauge", core: "0", value: 42.7}
{timestamp: 1714000300000000000, name: "cpu.usage", type: "gauge", core: "0", value: 39.8}
```

Without `SORT`, metric results are ordered by timestamp **ascending**
(§3.21) — the opposite of events and logs, because a metric result is
read as a series rather than as a list of occurrences.
