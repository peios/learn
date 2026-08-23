---
title: Retention
description: The metric retention pass, its long default, why downsampling is not yet part of it, and how space is reclaimed.
---

Metric retention runs on the same background thread as the other two,
after the log store (§3.6, §4.4). Both limits are enforced and the more
aggressive wins.

## The pass

1. Delete rows from `samples` older than `MetricRetentionDays` (§A)
   until none remain.
2. If `MetricRetentionMaxBytes` is non-zero and the store's logical live
   size exceeds it, delete the oldest samples by timestamp until it is
   within the limit.
3. Track every `series_id` whose samples were deleted by either step.
4. Delete every `rollups` row for those series.
5. Delete every `series` row with no remaining samples.

Logical live size is the same measure as §3.6.

Step 4 is not optional bookkeeping. A rollup is a pre-computed aggregate
of raw samples, so a rollup outliving its inputs would be served to a
query as an exact answer computed from data the store no longer has —
and the query engine, finding a matching rollup, would never look at the
raw samples to notice (§5.6). Rollups for the affected series can be
recomputed later from whatever samples remain.

Step 5 removes the definitions of series nobody produces any more, which
is the only mechanism that ever removes a `series` row. A series that
stopped receiving samples persists until its last sample ages out —
ninety days by default — so a burst of short-lived series from a
high-cardinality producer stays in the table for that long.

## The longest default

Ninety days, against fourteen for logs and thirty for events (§A).

A metric sample is small and its value grows with age: a year of CPU
utilisation is a capacity-planning input in a way that a year of log
lines is not. A thousand series sampled every fifteen seconds produce
about 5.7 million samples a day, which is a few hundred megabytes in
SQLite.

## Not yet: downsampling

The v0.23 model deletes; it does not downsample. A later retention
engine is expected to aggregate high-resolution data into
lower-resolution rollups as it ages — per-second samples becoming
five-minute averages after a week, hourly averages after a month —
which is what makes long-term metric retention affordable while
preserving the trend. The `rollups` table is the mechanism that would
serve it, but nothing currently promotes raw samples into rollups as a
retention action.

## Batching and reclamation

Batched at `RetentionDeleteBatchRows` per transaction, with the
coordination primitive released and writer pressure rechecked between
batches — the same rule and the same reason as §4.4, since the metric
writer is also the thread draining the metric socket.

`VACUUM` is never run automatically. Freed pages are recycled and are
excluded from the size measure.
