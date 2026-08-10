---
title: Retention
---

> [!INFORMATIVE]
> As with event and log retention, the metric retention model in v0.23 is an early simplification. Future versions will introduce downsampling (automatically aggregating high-resolution data into lower-resolution rollups over time -- e.g., per-second samples become 5-minute averages after one week, and 1-hour averages after one month). Downsampling dramatically reduces storage requirements for long-term metric data while preserving trend visibility. This is part of the more sophisticated retention engine referenced in §3.4.

## Configuration

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| MetricRetentionDays | REG_DWORD | 90 | 1--3650 | Maximum age of metric samples in days. Samples older than this are eligible for deletion. |
| MetricRetentionMaxBytes | REG_QWORD | 0 | 0--18446744073709551615 | Maximum logical live size of the metric store database in bytes. 0 means no size limit. |
| RetentionDeleteBatchRows | REG_DWORD | 10000 | 100--100000 | Maximum rows deleted in one retention transaction. |

Both limits are enforced. The more aggressive limit wins.

`MetricRetentionMaxBytes` uses the same SQLite logical live size definition as event retention (§3.4): `(page_count - freelist_count) * page_size`, measured after a passive WAL checkpoint attempt. Freed pages created by retention deletes do not count against the size limit because they are reusable by future inserts.

> [!INFORMATIVE]
> The default metric retention (90 days) is longer than event and log retention because metric data is small per sample and trend data is valuable over longer periods. A system with 1000 time series sampled every 15 seconds produces approximately 5.7 million samples per day -- a few hundred megabytes in SQLite.

## Retention process

The retention process runs on the same background thread as event and log retention, operating on the metric store database after completing log retention.

1. Delete rows from the `samples` table where `timestamp` is older than
   `MetricRetentionDays` from the current wall clock time until no matching rows
   remain.
2. If `MetricRetentionMaxBytes` is nonzero and the metric store database's
   logical live size exceeds the limit, delete the oldest samples (by
   `timestamp`) until the logical live size is within the limit.
3. Track every `series_id` whose samples were deleted by either age-based or size-based retention.
4. Delete all rows from the `rollups` table for affected `series_id` values. This prevents stale rollups from being served after their contributing raw samples have been removed. Rollups for affected series may be recomputed later from the remaining raw samples.
5. Delete any rows from the `series` table that have no remaining samples in the `samples` table. This cleans up time series definitions for metrics that are no longer being produced.

Deletion MUST be performed in batches to avoid holding long-running
transactions. Each retention transaction MUST delete at most
`RetentionDeleteBatchRows` rows and commit before starting the next batch. After
each batch, the retention thread MUST release any writer coordination primitive
and recheck writer pressure before attempting the next batch.

## Disk reclamation

As with the event and log stores, `VACUUM` is not run automatically. Freed pages are recycled by subsequent inserts and are excluded from retention size enforcement.
