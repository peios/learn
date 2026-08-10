---
title: Schema
---

## Log table

The log store is a single SQLite database. It MUST contain a `logs` table with the following schema:

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | SQLite rowid. Auto-assigned, monotonically increasing. |
| `boot_id` | BLOB NOT NULL | 16-byte boot ID GUID in PSD-002 binary format identifying which boot this log entry belongs to. |
| `timestamp` | INTEGER NOT NULL | Wall clock time in nanoseconds since Unix epoch. If the sender provided a timestamp, that value is used. Otherwise, eventd's receipt time is used. |
| `origin` | TEXT NOT NULL | Name of the service or component that produced the log line. |
| `is_error` | INTEGER NOT NULL | 1 if the log line came from stderr or was explicitly marked as error. 0 otherwise. |
| `message` | TEXT NOT NULL | The log text. |
| `job_id` | BLOB | 16-byte GUID in PSD-002 binary format for the job that produced this line, when peinit forwarded it with a job correlation. NULL for direct logging or output with no associated job. |

The log schema is deliberately minimal. Logs are text with light metadata: the originating service, an error flag, a timestamp, and an optional job-correlation GUID. There are no payload blobs and no origin classes; the only identity-like field is the optional `job_id` correlation key. Services that need richer structure should emit events.

## Write-time indexes

At database creation, eventd MUST create the following indexes:

- `idx_logs_timestamp` on `logs(timestamp)` -- required for time-range queries.
- `idx_logs_origin` on `logs(origin)` -- required for service-filtered queries, the most common log access pattern ("show me logs from service X").
- `idx_logs_job_id` on `logs(job_id) WHERE job_id IS NOT NULL` -- a partial index supporting per-job log queries ("show me logs for job X"). Partial because direct-logged lines carry no `job_id`, so only correlated lines are indexed.

The log store does not use adaptive indexing. The schema is narrow and the write-time indexes cover the dominant query patterns. Additional indexes are not expected to provide meaningful benefit.

> [!INFORMATIVE]
> The `idx_logs_origin` index adds write amplification beyond the required timestamp index. In practice the overhead is modest: the origin column has low cardinality (tens of distinct service names), so the index pages stay in SQLite's page cache and insertions are cheap. The partial `idx_logs_job_id` index is updated only for correlated log lines. This is a deliberate trade-off: "show me logs from service X" and "show me logs for job X" must be fast without a full table scan.

## Schema versioning

The log store database MUST contain a `metadata` table with the same structure as the event store (§3.1). The `schema_version` for the log store is `1`.

eventd MUST check the schema version on startup and apply the lifecycle rules
in §5.2. Migration is a separate administrative operation, not an automatic
startup behavior.
