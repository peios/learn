---
title: Retention
---

> [!INFORMATIVE]
> As with event retention (§3.4), the log retention model in v0.23 is a deliberate early simplification. Future versions will introduce more sophisticated retention rules.

## Configuration

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| LogRetentionDays | REG_DWORD | 14 | 1--3650 | Maximum age of log entries in days. Entries older than this are eligible for deletion. |
| LogRetentionMaxBytes | REG_QWORD | 0 | 0--18446744073709551615 | Maximum size of the log store database in bytes. 0 means no size limit. |

Both limits are enforced. The more aggressive limit wins.

> [!INFORMATIVE]
> The default log retention (14 days) is shorter than the default event retention (30 days), reflecting the lower importance of historical log data relative to audit events.

## Retention process

The retention process runs on the same background thread as event retention (§3.4), operating on the log store database after completing event retention.

1. Delete all rows from the `logs` table where `timestamp` is older than `LogRetentionDays` from the current wall clock time.
2. If `LogRetentionMaxBytes` is nonzero and the log store database exceeds the limit, delete the oldest log entries (by `timestamp`) until the size is within the limit.

Deletion MUST be performed in batches to avoid holding a long-running transaction that blocks the log writer thread.

## Disk reclamation

As with the event store, `VACUUM` is not run automatically. Freed pages are recycled by subsequent inserts.
