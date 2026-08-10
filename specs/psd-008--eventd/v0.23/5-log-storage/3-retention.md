---
title: Retention
---

> [!INFORMATIVE]
> As with event retention (§3.4), the log retention model in v0.23 is a deliberate early simplification. Future versions will introduce more sophisticated retention rules.

## Configuration

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| LogRetentionDays | REG_DWORD | 14 | 1--3650 | Maximum age of log entries in days. Entries older than this are eligible for deletion. |
| LogRetentionMaxBytes | REG_QWORD | 0 | 0--18446744073709551615 | Maximum logical live size of the log store database in bytes. 0 means no size limit. |
| RetentionDeleteBatchRows | REG_DWORD | 10000 | 100--100000 | Maximum rows deleted in one retention transaction. |

Both limits are enforced. The more aggressive limit wins.

`LogRetentionMaxBytes` uses the same SQLite logical live size definition as event retention (§3.4): `(page_count - freelist_count) * page_size`, measured after a passive WAL checkpoint attempt. Freed pages created by retention deletes do not count against the size limit because they are reusable by future inserts.

> [!INFORMATIVE]
> The default log retention (14 days) is shorter than the default event retention (30 days), reflecting the lower importance of historical log data relative to audit events.

## Retention process

The retention process runs on the same background thread as event retention (§3.4), operating on the log store database after completing event retention.

1. Delete rows from the `logs` table where `timestamp` is older than
   `LogRetentionDays` from the current wall clock time until no matching rows
   remain.
2. If `LogRetentionMaxBytes` is nonzero and the log store database's logical live
   size exceeds the limit, delete the oldest log entries (by `timestamp`) until
   the logical live size is within the limit.

Deletion MUST be performed in batches to avoid holding a long-running
transaction that blocks the log writer thread. Each retention transaction MUST
delete at most `RetentionDeleteBatchRows` rows and commit before starting the
next batch. After each batch, the retention thread MUST release any writer
coordination primitive and recheck writer pressure before attempting the next
batch.

## Disk reclamation

As with the event store, `VACUUM` is not run automatically. Freed pages are recycled by subsequent inserts and are excluded from retention size enforcement.
