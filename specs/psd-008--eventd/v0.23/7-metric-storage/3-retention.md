---
title: Retention
---

> [!INFORMATIVE]
> As with event and log retention, the metric retention model in v0.23 is an early simplification. Future versions will introduce downsampling (automatically aggregating high-resolution data into lower-resolution rollups over time -- e.g., per-second samples become 5-minute averages after one week, and 1-hour averages after one month). Downsampling dramatically reduces storage requirements for long-term metric data while preserving trend visibility. This is part of the more sophisticated retention engine referenced in §3.4.

## Configuration

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| MetricRetentionDays | REG_DWORD | 90 | 1--3650 | Maximum age of metric samples in days. Samples older than this are eligible for deletion. |
| MetricRetentionMaxBytes | REG_QWORD | 0 | 0--18446744073709551615 | Maximum size of the metric store database in bytes. 0 means no size limit. |

Both limits are enforced. The more aggressive limit wins.

> [!INFORMATIVE]
> The default metric retention (90 days) is longer than event and log retention because metric data is small per sample and trend data is valuable over longer periods. A system with 1000 time series sampled every 15 seconds produces approximately 5.7 million samples per day -- a few hundred megabytes in SQLite.

## Retention process

The retention process runs on the same background thread as event and log retention, operating on the metric store database after completing log retention.

1. Delete all rows from the `samples` table where `timestamp` is older than `MetricRetentionDays` from the current wall clock time.
2. If `MetricRetentionMaxBytes` is nonzero and the metric store database exceeds the limit, delete the oldest samples (by `timestamp`) until the size is within the limit.
3. Delete any rows from the `series` table that have no remaining samples in the `samples` table. This cleans up time series definitions for metrics that are no longer being produced.

Deletion MUST be performed in batches to avoid holding long-running transactions.

## Disk reclamation

As with the event and log stores, `VACUUM` is not run automatically. Freed pages are recycled by subsequent inserts.
