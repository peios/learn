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
4. Delete every `series` row with no remaining samples.

Logical live size is the same measure as §3.6.

Step 4 removes the definitions of series nobody produces any more, which
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
engine may aggregate high-resolution data as it ages — per-second
samples becoming five-minute aggregates after a week, hourly aggregates
after a month — but doing so requires a versioned storage and query
contract that does not exist in schema version 1 (§5.6).

## Batching and reclamation

The retention coordinator plans with a read-only connection and submits
low-priority delete commands to the metric writer. Each writer-owned
transaction deletes at most `RetentionDeleteBatchRows`, and ingestion is
rechecked before the next command. Under urgent size pressure the writer
may append one bounded retention delete to a transaction it already has
open; retention never takes a writer mutex or opens another read-write
connection (§3.6).

`VACUUM` is never run automatically. Freed pages are recycled and are
excluded from the size measure.
