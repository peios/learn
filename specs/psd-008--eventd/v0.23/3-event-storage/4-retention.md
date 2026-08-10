---
title: Retention
---

## Retention model

> [!INFORMATIVE]
> The retention model in v0.23 is a deliberate early simplification. Future versions will introduce a significantly more sophisticated retention engine supporting precise query-like rules (e.g., "retain KACS events for 90 days, retain synthetic events for 7 days, retain events where origin_class == userspace for 14 days") and hot pruning of events during ingestion based on policy. The v0.23 model provides the minimum viable retention needed to prevent unbounded disk growth.

eventd MUST enforce retention policies that limit how long event data is stored. Retention prevents unbounded disk growth and ensures that old data is removed in a predictable, configurable manner.

Retention uses two deletion strategies:

1. **Age-based retention** deletes records older than the configured retention window, regardless of boot ID.
2. **Size-pressure retention** prefers boot boundaries: complete non-current boot partitions are deleted before eventd prunes records from the current boot.

This preserves recent events across boot boundaries while allowing size-pressure cleanup to remove old boots as a single unit.

## Configuration

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| EventRetentionDays | REG_DWORD | 30 | 1--3650 | Maximum age of events in days. Events older than this are eligible for deletion. |
| EventRetentionMaxBytes | REG_QWORD | 0 | 0--18446744073709551615 | Maximum total logical live size of all event shard databases in bytes. 0 means no size limit. When exceeded, the oldest events are deleted until the total logical live size is within the limit. |
| RetentionCheckIntervalMinutes | REG_DWORD | 60 | 1--1440 | How often the retention process runs, in minutes. |
| RetentionDeleteBatchRows | REG_DWORD | 10000 | 100--100000 | Maximum rows deleted in one retention transaction. |

Both time-based and size-based retention limits are enforced. If both are configured, the more aggressive limit wins -- an event is deleted if it exceeds either threshold.

`EventRetentionMaxBytes` is measured as SQLite logical live size, not filesystem file size. For each database, eventd MUST first attempt a passive WAL checkpoint. It then computes:

```text
logical_live_bytes = (page_count - freelist_count) * page_size
```

using `PRAGMA page_count`, `PRAGMA freelist_count`, and `PRAGMA page_size`. The event store total is the sum across all event shard databases. Freed pages created by retention deletes do not count against the size limit because they are reusable by future inserts.

## Retention process

The retention process runs periodically on a background thread. It MUST NOT run on the writer threads or drain threads. It operates on one shard database at a time, using a separate read-write connection.

For age-based retention, each shard database is processed independently:

1. Delete rows from the `events` table where `timestamp` is older than
   `EventRetentionDays` from the current wall clock time until no matching rows
   remain. This covers KMES events, synthetic events, and gap records uniformly.

For size-pressure retention, if `EventRetentionMaxBytes` is nonzero and the total logical live size of all shard databases exceeds the limit:

1. Identify all non-current boot IDs present in the event shard databases.
2. Order those boot IDs by their newest event timestamp, oldest boot first.
3. Delete events for each non-current boot ID across all shards, one boot at a
   time, until the total logical live size is within the limit or no non-current
   boot IDs remain.
4. If the logical live size still exceeds the limit, delete the oldest events
   from the current boot by `timestamp` across all shards until the total logical
   live size is within the limit.

Deletion MUST be performed in batches to avoid holding a long-running
transaction that blocks the writer thread. Each retention transaction MUST
delete at most `RetentionDeleteBatchRows` rows and commit before starting the
next batch. After each batch, the retention thread MUST release the shard-level
write coordination primitive and recheck writer pressure before attempting the
next batch.

## Impact on writers

The retention process opens a separate read-write connection to the shard database. In WAL mode, a reader does not block the writer. However, a second writer would block. The retention process MUST coordinate with the shard's writer thread to avoid concurrent write transactions.

The simplest coordination mechanism is for the retention process to acquire a shard-level mutex before writing, and for the writer thread to briefly yield when the retention process needs to run. The retention process performs small, bounded delete batches and releases the mutex between batches, minimising writer thread stall time.

## Disk reclamation

Deleting rows from SQLite does not usually shrink the database file. Freed pages are reused for future inserts and are excluded from the logical live size used for retention enforcement. To reclaim filesystem space, `VACUUM` must be run, but this rewrites the entire database and is expensive.

eventd MUST NOT run `VACUUM` automatically. Disk reclamation is an administrative operation triggered explicitly. The freed pages from retention deletes are recycled by subsequent inserts, which is sufficient for steady-state operation.

> [!INFORMATIVE]
> On a system in steady state -- where events are ingested at roughly the same rate they are deleted by retention -- the database file size stabilises at approximately the high-water mark of retained data. The freed pages from old events are reused by new inserts without the database file growing.
