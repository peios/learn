---
title: Adaptive Rollups
description: Precomputed aggregates so a wide query does not scan millions of raw samples — the rollups table, the registry, and serving a query from one.
---

Aggregate metric queries read raw samples. Over a large range that means
scanning thousands or millions of rows to produce a handful of numbers,
and the same numbers over and over.

Rollups pre-compute them. The principle is adaptive indexing's (§3.4):
watch which query patterns recur, compute their results in the
background, and serve from the results when they exist. What differs is
that a rollup is an answer rather than an access path, so it has to be
exactly the answer the raw samples would have given.

## The rollups table

| Column | Type | Contents |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | SQLite rowid. |
| `series_id` | INTEGER NOT NULL | References `series(id)`. |
| `function` | INTEGER NOT NULL | Function identifier (§B). |
| `window_seconds` | INTEGER NOT NULL | Window size. |
| `window_start` | INTEGER NOT NULL | Window start, nanoseconds since the epoch. |
| `value` | REAL NOT NULL | The pre-computed value. |
| `sample_count` | INTEGER NOT NULL | Scalar inputs that contributed. For AVG/MIN/MAX/SUM, raw samples; for RATE/DELTA, valid sample pairs. |
| `covered_ns` | INTEGER NOT NULL | For RATE and DELTA, the elapsed nanoseconds the contributing pairs covered. Zero for AVG, MIN, MAX and SUM. |

A unique constraint and an index both cover
`(series_id, function, window_seconds, window_start)`.

Every row satisfies: `sample_count` greater than zero, `value` finite,
and `covered_ns` greater than zero for RATE and DELTA and exactly zero
for the other four.

`sample_count` and `covered_ns` are what make rollups composable. A
window built from one sample is not as good as one built from sixty, and
combining sub-windows correctly needs their weights — an average
composes weighted by `sample_count`, a rate composes weighted by
`covered_ns`. Without them a rollup could only serve a query whose
window matched it exactly.

Rollups are **per series** and carry no `boot_id`. Cross-series
aggregation composes per-series rollup rows and then applies the query's
terminal aggregation across them.

## What is not rolled up

**Percentiles.** P50, P95 and P99 are not composable: the P95 of twelve
five-minute P95 values is not the P95 of the hour. Percentile queries
always compute from raw histogram samples.

A later revision could add histogram rollups storing merged bucket
counts, computing percentiles from the rolled-up distribution — but that
is a different storage model, not a row in this scalar table.

**Histogram samples in scalar rollups.** AVG, MIN, MAX and SUM roll up
raw counter and gauge values only.

**Non-window RATE and DELTA scalar aggregations.** A stored RATE or
DELTA row is a *window-level* rate, whereas a scalar aggregation over a
transformed series operates on the per-pair values (PSPU §3.25). Serving
one from the other would give a different answer, so these are not
recorded and always fall back to raw samples.

## The registry

eventd maintains a global set of `(function, window)` pairs worth
pre-computing, derived from query frequency exactly as the desired index
set is (§3.4), with its counters in the metadata database (§3.5).

Each metric query with a rollup-eligible aggregation records a pair:

- `AVG_OVER`, `MIN_OVER`, `MAX_OVER` and `SUM_OVER` record AVG, MIN, MAX
  and SUM respectively, when no RATE or DELTA transform is present, with
  the query's window duration.
- With RATE or DELTA present alongside a window aggregation, the
  *transform* is the recorded function and the terminal aggregation is
  applied afterward to the per-series values. The window duration is
  again the query's.
- Scalar AVG, MIN, MAX and SUM over raw counter or gauge samples with a
  `SINCE` clause record the same function using
  `AdaptiveRollupScalarWindowSeconds` (§A) as the window — a scalar
  query has no window of its own, so a base window is chosen for it and
  composition covers the rest.

A pair crossing `AdaptiveRollupCreateThreshold` over the rolling window
joins the registry; one falling below `AdaptiveRollupDropThreshold`
leaves it. Both thresholds are lower than the indexing ones, because
rollup computation is cheaper — it proceeds window by window rather than
building a whole B-tree — and the speedup is larger, twenty-four rows
instead of eighty-six thousand for a daily query at one-second
resolution.

The registry is global: if hourly averages are queried often for
anything, they are computed for every compatible series. Incompatible
series are skipped.

## Computation

On a background thread, during low write activity. For each registry
pair, the thread finds windows with raw samples but no rollup row, reads
those samples, computes, and inserts.

**Only completed windows.** The current, still-accumulating window is
never pre-computed and is always computed from raw samples at query
time.

AVG, MIN, MAX and SUM take the raw counter or gauge values whose
timestamps fall in the window. RATE and DELTA are computed for counter
series only, and computation skips any series whose type the function
does not fit.

RATE and DELTA use the same counter-window rule the query engine uses
(PSPU §3.25): consecutive pairs in `(timestamp, id)` order whose later
sample falls inside the window; the immediately preceding sample before
the first in-window one as the baseline for the first pair, where it
exists; pairs with non-positive elapsed time ignored. DELTA's `value` is
the sum of reset-adjusted deltas, and RATE's is that divided by
`covered_ns` in seconds. A window with no contributing inputs — or, for
RATE, zero `covered_ns` — gets no row at all rather than a zero.

Computation is **cancellable** on rising write pressure and resumes
later, through the same mechanism as adaptive index creation (§3.4).

## Serving a query from rollups

When a metric query carries a rollup-eligible aggregation, the engine
checks for matching rollups. It uses them when a rollup covers the
requested function, window size and time range **and the query does not
filter by `boot_id`** — rollups are boot-agnostic, so a boot-filtered
query cannot be answered from one (§3.7).

Partial coverage is handled rather than refused. Where rollups exist for
the complete windows fully inside the effective range, the engine reads
those and computes the remaining prefix or suffix from raw samples. That
edge handling is required for exactness whenever a `SINCE` or `UNTIL`
bound is not aligned to the window.

With no matching rollup, or a boot filter, or a percentile, or a
non-window RATE or DELTA scalar aggregation, the query falls back to raw
samples entirely. **The result is identical either way** — rollups are a
transparent optimisation and never a different answer.

## Composition

A rollup window need not match the query window for composable
functions. Smaller windows serve larger queries; the reverse never
works.

| Function | Composes by |
|---|---|
| AVG | weighted average by `sample_count` |
| MIN, MAX | min or max across sub-windows |
| SUM, DELTA | addition |
| RATE | `sum(subrate × sub_covered_ns) / sum(sub_covered_ns)` |

`AVG_OVER 1h` is served from twelve five-minute AVG rollups by weighting
each by its `sample_count`.

Counter resets are handled once, during computation: a stored RATE or
DELTA already reflects reset-adjusted deltas, so composition operates on
adjusted values and never has to consider a reset again.

For cross-series unbracketed window queries, composition happens per
series first and the terminal aggregation is applied across series
afterward. The weighting differs between two cases that look alike:

- **Without a transform**, `AVG_OVER` across series combines per-series
  AVG rollups **weighted by `sample_count`**, because the query means
  the average of every scalar sample value in the window.
- **With RATE or DELTA**, the terminal average is an **unweighted** mean
  of the per-series window values, because under PSPU §3.25 each series
  contributes at most one scalar per window, and weighting one-value
  contributions by their pair counts would silently favour the
  busiest series.

## Retention and departure

Rollup rows follow raw sample retention. When retention deletes samples
it deletes the rollups for the affected series (§5.5).

When a pair leaves the registry, existing rows are **not** deleted. They
remain available to queries until they age out through normal retention;
only new computation stops. Deleting them would discard work already
done in exchange for nothing — the rows are correct, and a query that
can use one still can.

## Persistence

The registry and its counters live in the metadata database (§3.5) and
survive restarts. Existing rollup rows are discovered in the table
itself; eventd resumes computation from whatever state it finds, exactly
as it resumes index convergence (§3.4).
