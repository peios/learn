---
title: Schema
---

## Event table

Each shard database MUST contain an `events` table with the following schema:

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | SQLite rowid. Auto-assigned, monotonically increasing within the shard. |
| `boot_id` | BLOB NOT NULL | 16-byte boot ID GUID identifying which boot this event belongs to. |
| `timestamp` | INTEGER NOT NULL | Wall clock time. Nanoseconds since Unix epoch. For KMES events, copied from the event header `timestamp` field. For synthetic events, the wall clock time when eventd generated the record. |
| `cpu_id` | INTEGER | CPU on which the event was emitted. Copied from the KMES event header. NULL for synthetic events. |
| `sequence` | INTEGER | Per-CPU, per-boot monotonic sequence number. Copied from the KMES event header. NULL for synthetic events. |
| `origin_class` | INTEGER | Origin of the event (0 = userspace, 1 = KMES, 2 = KACS, 3 = LCS). Copied from the KMES event header. NULL for synthetic events. |
| `event_type` | TEXT NOT NULL | Event type string. For KMES events, copied from the event header. For synthetic events, a `synthetic.` prefixed type string (e.g., `synthetic.startup`, `synthetic.shutdown`, `synthetic.gap`, `synthetic.config_change`, `synthetic.storage_error`). |
| `effective_token_guid` | BLOB | 16-byte GUID of the effective token at emission time. NULL for synthetic events. Null GUID (16 zero bytes) if identity was not available at emission time. |
| `true_token_guid` | BLOB | 16-byte GUID of the process's primary token at emission time. NULL for synthetic events. |
| `process_guid` | BLOB | 16-byte GUID of the emitting process. NULL for synthetic events. |
| `payload` | BLOB | Msgpack-encoded event payload. For KMES events, the raw payload bytes from the event -- eventd MUST NOT interpret, modify, or re-encode them. For synthetic events, a msgpack-encoded map containing event-specific details. NULL if the event carries no payload data. |

All KMES header fields are extracted into individual columns to enable direct SQL filtering without parsing event data. The `event_type` column serves as the sole discriminator between KMES events and synthetic events -- no separate record type column is needed.

## Synthetic event types

The following synthetic event types are defined:

| Event type | Payload contents |
|---|---|
| `synthetic.startup` | Boot ID, restart flag (whether this is a fresh boot or a restart within the same boot), shard count, per-CPU sequence resume points. |
| `synthetic.shutdown` | Per-CPU last persisted sequence numbers. |
| `synthetic.gap` | CPU ID, first missing sequence number, last missing sequence number, count of missing events, timestamp of last event before the gap, timestamp of event that revealed the gap. |
| `synthetic.config_change` | Key name, old value, new value. |
| `synthetic.storage_error` | Shard index, error description. |

The payload schema for each synthetic event type is defined by eventd. Additional synthetic event types MAY be defined in future versions.

## Write-time indexes

At database creation, eventd MUST create the following index:

- `idx_events_timestamp` on `events(timestamp)` -- required for time-range queries, which are the most common access pattern.

No other indexes are created at database creation time. Additional indexes are managed by the adaptive indexing mechanism (§3.3).

## Schema versioning

Each shard database MUST store a schema version number in a `metadata` table:

| Column | Type | Description |
|---|---|---|
| `key` | TEXT PRIMARY KEY | Metadata key name. |
| `value` | TEXT NOT NULL | Metadata value. |

Required metadata entries:

| Key | Value |
|---|---|
| `schema_version` | `1` (for this version of the specification). |
| `created_at` | ISO 8601 timestamp of database creation. |

eventd MUST check the schema version on startup and MUST NOT write to databases with an unrecognised schema version. Migration is a separate administrative operation, not an automatic startup behavior.
