---
title: Retention
---

## Retention model

> [!INFORMATIVE]
> The retention model in v0.23 is a deliberate early simplification. Future versions will introduce a significantly more sophisticated retention engine supporting precise query-like rules (e.g., "retain KACS events for 90 days, retain synthetic events for 7 days, retain events where origin_class == userspace for 14 days") and hot pruning of events during ingestion based on policy. The v0.23 model provides the minimum viable retention needed to prevent unbounded disk growth.

eventd MUST enforce retention policies that limit how long event data is stored. Retention prevents unbounded disk growth and ensures that old data is removed in a predictable, configurable manner.

Retention operates on a per-boot granularity for the primary data boundary and a time-based granularity within the current boot. Data from old boots is the first candidate for removal. Within the current boot, data older than the retention window is removed.

## Configuration

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| EventRetentionDays | REG_DWORD | 30 | 1--3650 | Maximum age of events in days. Events older than this are eligible for deletion. |
| EventRetentionMaxBytes | REG_QWORD | 0 | 0--18446744073709551615 | Maximum total size of all event shard databases in bytes. 0 means no size limit. When exceeded, the oldest events are deleted until the total size is within the limit. |
| RetentionCheckIntervalMinutes | REG_DWORD | 60 | 1--1440 | How often the retention process runs, in minutes. |

Both time-based and size-based retention limits are enforced. If both are configured, the more aggressive limit wins -- an event is deleted if it exceeds either threshold.

## Retention process

The retention process runs periodically on a background thread. It MUST NOT run on the writer threads or drain threads. It operates on one shard database at a time, using a separate read-write connection.

For each shard database:

1. Delete all rows from the `events` table where `timestamp` is older than `EventRetentionDays` from the current wall clock time. This covers KMES events, synthetic events, and gap records uniformly.
2. If `EventRetentionMaxBytes` is nonzero and the total size of all shard databases exceeds the limit, delete the oldest events (by `timestamp`) across all shards until the total size is within the limit.

Deletion MUST be performed in batches to avoid holding a long-running transaction that blocks the writer thread. Each batch deletes a bounded number of rows (implementation-defined) and commits before starting the next batch.

## Impact on writers

The retention process opens a separate read-write connection to the shard database. In WAL mode, a reader does not block the writer. However, a second writer would block. The retention process MUST coordinate with the shard's writer thread to avoid concurrent write transactions.

The simplest coordination mechanism is for the retention process to acquire a shard-level mutex before writing, and for the writer thread to briefly yield when the retention process needs to run. The retention process performs small, bounded delete batches and releases the mutex between batches, minimising writer thread stall time.

## Disk reclamation

Deleting rows from SQLite does not shrink the database file. Freed pages are reused for future inserts. To reclaim disk space, `VACUUM` must be run, but this rewrites the entire database and is expensive.

eventd SHOULD NOT run `VACUUM` automatically. Disk reclamation is an administrative operation triggered explicitly. The freed pages from retention deletes are recycled by subsequent inserts, which is sufficient for steady-state operation.

> [!INFORMATIVE]
> On a system in steady state -- where events are ingested at roughly the same rate they are deleted by retention -- the database file size stabilises at approximately the retention window's worth of data. The freed pages from old events are reused by new inserts without the database file growing.
