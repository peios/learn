---
title: Schema
---

## Log table

The log store is a single SQLite database. It MUST contain a `logs` table with the following schema:

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | SQLite rowid. Auto-assigned, monotonically increasing. |
| `boot_id` | BLOB NOT NULL | 16-byte boot ID GUID identifying which boot this log entry belongs to. |
| `timestamp` | INTEGER NOT NULL | Wall clock time in nanoseconds since Unix epoch. If the sender provided a timestamp, that value is used. Otherwise, eventd's receipt time is used. |
| `origin` | TEXT NOT NULL | Name of the service or component that produced the log line. |
| `is_error` | INTEGER NOT NULL | 1 if the log line came from stderr or was explicitly marked as error. 0 otherwise. |
| `message` | TEXT NOT NULL | The log text. |

The log schema is deliberately minimal. Logs are text with light metadata. There are no payload blobs, no identity GUIDs, no origin classes. Services that need richer structure should emit events.

## Write-time indexes

At database creation, eventd MUST create the following indexes:

- `idx_logs_timestamp` on `logs(timestamp)` -- required for time-range queries.
- `idx_logs_origin` on `logs(origin)` -- required for service-filtered queries, the most common log access pattern ("show me logs from service X").

The log store does not use adaptive indexing. The schema is narrow and the two write-time indexes cover the dominant query patterns. Additional indexes are not expected to provide meaningful benefit.

## Schema versioning

The log store database MUST contain a `metadata` table with the same structure as the event store (§3.1). The `schema_version` for the log store is `1`.

eventd MUST check the schema version on startup and MUST NOT write to the database if the version is unrecognised.
