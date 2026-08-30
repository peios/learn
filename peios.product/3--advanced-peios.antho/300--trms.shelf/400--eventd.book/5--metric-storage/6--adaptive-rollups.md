---
title: Deferred Adaptive Rollups
description: Why v0.23 answers metric queries from raw samples, and the validity contract a later rollup design must satisfy.
---

eventd v0.23 has no rollup table, registry, configuration or background
rollup worker. Every metric query reads the authoritative raw samples.
This keeps the initial ingestion path and schema small, and makes the
answer independent of whether background maintenance happened to run.

Wide aggregate queries can therefore be expensive. That is an accepted
v0.23 cost, not permission to cache an answer whose inputs cannot be
proved current.

## Required future validity contract

A later schema version may add adaptive rollups, but a rollup is usable
only when it can validate itself against the raw sample set at query
time. At minimum each row records the greatest source sample `id` that
contributed, `source_max_sample_id`, in addition to its series,
function, window and aggregate state.

Before serving the row, the query engine checks whether the same series
and window contains any raw sample with an `id` greater than that source
maximum. If one exists, the row is stale: the query computes from raw
samples and schedules a replacement. It never waits for repair and
never returns the stale value.

`RATE` and `DELTA` have an additional dependency on the sample
immediately preceding the window. Their rows also record
`source_baseline_sample_id`, or an explicit absence, and validate that
the recorded sample is still the correct preceding baseline. A changed,
new or deleted baseline makes the row stale even when no in-window
sample changed.

Retention must invalidate or remove every aggregate whose input or
baseline it deletes. The query-time checks remain mandatory: maintenance
ordering alone is not a correctness proof.

## Writer ownership

Future rollup computation reads through read-only connections. During
quiet write periods it submits bounded, low-priority replacement
commands to the metric writer, which remains the database's only
read-write connection owner (§5.4). The worker is cancellable as write
pressure rises. It takes no hot-path coordination primitive and causes
no additional fsync merely to maintain an optimisation.

The table, exact aggregate-state encodings, registry policy and
configuration keys require their own later schema revision. They are
deliberately not reserved in schema version 1.
