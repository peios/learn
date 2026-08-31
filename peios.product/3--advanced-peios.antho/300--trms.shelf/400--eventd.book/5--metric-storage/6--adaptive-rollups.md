---
title: Adaptive Rollups
description: How repeated wide metric-window queries seed a bounded, self-validating cache without adding work to ingestion.
---

Raw rows in `samples` are always authoritative. The `rollups` table is a
disposable query cache: deleting every rollup can make a query slower, but
cannot change its answer. A miss or a stale row is computed directly from raw
samples and returned immediately; query execution never waits for the cache to
be repaired.

The design protects eventd's primary job. Metric ingestion does not inspect,
update or coordinate with rollups. A query computes a candidate while doing
work it already needed for its own answer, and submits that candidate through a
bounded non-blocking channel. The sole metric writer considers at most one such
command only after the receive queue is idle and the current sample batch is
committed. A full command channel, writer pressure or any ordinary cache-write
failure drops the candidate rather than delaying ingestion.

## Eligible queries

A query can read or seed rollups only when all of these are true:

- it has `SINCE` and an explicit `AVG_OVER`, `MIN_OVER`, `MAX_OVER` or
  `SUM_OVER` function;
- the selected output is per series — the selector is bracketed, or it resolves
  to exactly one series;
- it has no `WHERE` predicate or cross-type filter; and
- `AdaptiveRollupMaxRows` is non-zero.

The label selector has already selected concrete series and is therefore safe.
An unbracketed multi-series query is not eligible because its window result
combines series; reusing independently cached averages or extrema would not in
general reproduce that result. Predicate and cross-filter shapes remain on the
raw path because their result depends on more than the cached series window.

Only complete windows aligned to Unix-epoch multiples of the requested width
are cached. Any partial window at either end of the requested range is always
read from raw samples. A query uses the cache only when every complete interior
window for the series has a valid row, including explicit empty-window rows;
otherwise it evaluates that series from raw samples. This all-or-raw rule keeps
the fallback simple and prevents a cache miss from changing transform pairing.

Streaming continuations do not use or seed rollups. They preserve their normal
incremental raw-query semantics.

## Schema and identity

Metric schema version 2 adds:

```sql
CREATE TABLE rollups (
    series_id INTEGER NOT NULL REFERENCES series(id) ON DELETE CASCADE,
    window_start INTEGER NOT NULL,
    window_width INTEGER NOT NULL CHECK (window_width > 0),
    transform INTEGER NOT NULL CHECK (transform IN (0, 1, 2, 50, 95, 99)),
    function INTEGER NOT NULL CHECK (function BETWEEN 0 AND 3),
    value REAL,
    overflow INTEGER NOT NULL CHECK (overflow IN (0, 1)),
    source_max_sample_id INTEGER NOT NULL CHECK (source_max_sample_id >= 0),
    source_baseline_sample_id INTEGER CHECK (source_baseline_sample_id > 0),
    CHECK (overflow = 0 OR value IS NULL),
    PRIMARY KEY
        (series_id, window_start, window_width, transform, function)
) WITHOUT ROWID;
```

`transform` distinguishes no transform, `RATE`, `DELTA`, `P50`, `P95` and
`P99`. `function` distinguishes `AVG_OVER`, `MIN_OVER`, `MAX_OVER` and
`SUM_OVER`. `value` is null only for an empty window or a percentile overflow;
`overflow` distinguishes those cases. Empty rows are necessary to prove that a
complete cached range really has no missing window.

Opening a version-1 metric store creates the table and its pruning index in one
immediate transaction, then records version 2. Unknown versions still fail
startup (§5.1, §A.2).

## Validity proof

Each row records the greatest raw sample `id` observed inside its window as
`source_max_sample_id`. Before serving it, the query engine proves that the same
series and window has no sample with a greater `id`. A later sample therefore
makes the row stale even when its timestamp was backfilled into an old window.
An empty window records zero, so its first raw sample also invalidates it.

`RATE` and `DELTA` additionally depend on the sample immediately preceding the
window. Their rows record that sample's id in `source_baseline_sample_id`, with
null meaning no preceding sample existed. The query engine compares this with
the current immediately preceding sample. A new, changed or deleted baseline
makes the row stale.

Retention invalidates all rollups for every series from which it deletes a raw
sample before it deletes the sample (§5.5). This is deliberately conservative.
The query-time proof remains mandatory: maintenance ordering alone is not a
freshness guarantee.

Non-finite cached values are rejected. As everywhere in metric evaluation, a
numeric result must be finite; percentile overflow is represented by the
explicit null-and-overflow state instead (§6, PSPU §3.25).

## Seeding and bounds

An eligible raw evaluation may enqueue candidates only after it has scanned at
least `AdaptiveRollupMinSamples` raw inputs. It enqueues no more than
`AdaptiveRollupBatchRows` missing windows, and submission uses `try_send` on a
fixed-capacity channel. Repeating a wide query gradually fills its cache in
bounded pieces without starting a background scanner.

The writer upserts a candidate under the complete cache identity and prunes the
oldest window starts until no more than `AdaptiveRollupMaxRows` remain. The cap
is global to the metric store. It limits this optional acceleration state; it
does not delete series or raw samples.

All three controls are live (§A.1). Setting `AdaptiveRollupMaxRows` to zero
immediately disables cache reads and writes without changing query results.

Adaptive rollups are not downsampling. Raw samples retain their ordinary age
and size policy, and every supported query remains answerable from them (§5.5).
