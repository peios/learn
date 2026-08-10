---
title: Schema
---

## Event table

Each shard database MUST contain an `events` table with the following schema:

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | SQLite rowid. Auto-assigned, monotonically increasing within the shard. |
| `boot_id` | BLOB NOT NULL | 16-byte boot ID GUID in PSD-002 binary format identifying which boot this event belongs to. |
| `timestamp` | INTEGER NOT NULL | Wall clock time. Nanoseconds since Unix epoch. For KMES events, copied from the event header `timestamp` field. For synthetic events, the wall clock time when eventd generated the record. |
| `cpu_id` | INTEGER | CPU on which the event was emitted. Copied from the KMES event header. NULL for daemon-wide synthetic events (startup, shutdown, config_change, storage_error). Populated for CPU-specific synthetic events (gap records). |
| `sequence` | INTEGER | Per-CPU, per-boot monotonic sequence number. Copied from the KMES event header. NULL for synthetic events. |
| `origin_class` | INTEGER | Origin of the event (0 = userspace, 1 = KMES, 2 = KACS, 3 = LCS). Copied from the KMES event header. NULL for synthetic events. |
| `event_type` | TEXT NOT NULL | Event type string. For KMES events, copied from the event header. For synthetic events, a `synthetic.` prefixed type string (e.g., `synthetic.startup`, `synthetic.shutdown`, `synthetic.gap`, `synthetic.config_change`, `synthetic.storage_error`). |
| `effective_token_guid` | BLOB | 16-byte GUID in PSD-002 binary format for the effective token at emission time. NULL for synthetic events. Null GUID (16 zero bytes) if identity was not available at emission time. |
| `true_token_guid` | BLOB | 16-byte GUID in PSD-002 binary format for the process's primary token at emission time. NULL for synthetic events. |
| `process_guid` | BLOB | 16-byte GUID in PSD-002 binary format for the emitting process. NULL for synthetic events. |
| `payload` | BLOB | Msgpack-encoded event payload. For KMES events, the raw payload bytes from the event -- eventd MUST NOT interpret, modify, or re-encode them. For synthetic events, a msgpack-encoded map containing event-specific details. NULL if the event carries no payload data. |

All KMES header fields are extracted into individual columns to enable direct SQL filtering without parsing event data. The `event_type` column serves as the sole discriminator between KMES events and synthetic events -- no separate record type column is needed.

## Synthetic event types

The following synthetic event types are defined:

| Event type | Payload contents |
|---|---|
| `synthetic.startup` | Boot ID, restart flag (whether this is a fresh boot or a restart within the same boot), shard count, per-CPU sequence resume points. |
| `synthetic.shutdown` | Per-CPU last committed sequence numbers. |
| `synthetic.gap` | CPU ID, first missing sequence number, last missing sequence number, count of missing events, timestamp of last event before the gap, timestamp of event that revealed the gap. |
| `synthetic.config_change` | Key name, old value, new value. |
| `synthetic.storage_error` | Store type (event, log, metric, or metadata), shard index (for event store errors, NULL for log/metric/metadata), error description. |

Synthetic event payloads are msgpack maps with the exact schemas below. Field
names are stable query-language payload field names after flattening unless the
field value is a nested array/map value that §8.1 does not traverse.

**`synthetic.startup` payload:**

| Field | Type | Description |
|---|---|---|
| `boot_id` | string | Current boot ID in PSD-002 canonical GUID string form. |
| `restart` | bool | True if committed event rows for this boot already existed at startup; false for the first eventd start of the boot. |
| `shard_count` | unsigned integer | Active event shard count after resolving `StorageShards`. |
| `resume_points` | array of map | One entry per CPU, sorted by `cpu_id` ascending. Each entry has `cpu_id` (unsigned integer) and `sequence` (unsigned integer, the startup resume sequence for that CPU). |

**`synthetic.shutdown` payload:**

| Field | Type | Description |
|---|---|---|
| `last_sequences` | array of map | One entry per CPU, sorted by `cpu_id` ascending. Each entry has `cpu_id` (unsigned integer) and `sequence` (unsigned integer, the last committed sequence for that CPU in the current boot, or 0 if none was committed). |

**`synthetic.gap` payload:**

| Field | Type | Description |
|---|---|---|
| `cpu_id` | unsigned integer | CPU on which the gap was detected. |
| `first_sequence` | unsigned integer | First missing sequence number. |
| `last_sequence` | unsigned integer | Last missing sequence number. |
| `count` | unsigned integer | Number of missing sequence numbers. |
| `last_seen_timestamp` | timestamp or nil | Timestamp of the last successfully processed event before the gap, if known. |
| `revealing_timestamp` | timestamp | Timestamp of the event or ring position that revealed the gap. |

**`synthetic.config_change` payload:**

| Field | Type | Description |
|---|---|---|
| `key` | string | Configuration key name relative to `Machine\System\eventd\`. |
| `old_value_type` | string | One of `absent`, `REG_SZ`, `REG_DWORD`, `REG_QWORD`, or `REG_BINARY`. |
| `old_value` | string or nil | Previous value rendered as described below, or nil when `old_value_type` is `absent`. |
| `new_value_type` | string | One of `absent`, `REG_SZ`, `REG_DWORD`, `REG_QWORD`, or `REG_BINARY`. |
| `new_value` | string or nil | New value rendered as described below, or nil when `new_value_type` is `absent`. |

Configuration values are rendered deterministically for the config-change
payload: `REG_SZ` values are the registry string as UTF-8, `REG_DWORD` and
`REG_QWORD` values are unsigned decimal without leading zeroes, and
`REG_BINARY` values are lowercase hexadecimal with two digits per byte.

**`synthetic.storage_error` payload:**

| Field | Type | Description |
|---|---|---|
| `store` | string | One of `event`, `log`, `metric`, or `metadata`. |
| `shard_index` | unsigned integer or nil | Event shard index for event-store errors; nil for log, metric, and metadata errors. |
| `error` | string | Human-readable error description. |

Additional synthetic event types MAY be defined in future versions.

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
| `created_at` | UTC creation time formatted as `YYYY-MM-DDTHH:MM:SSZ`. |

eventd MUST check the schema version on startup and apply the lifecycle rules
in §3.2 for active and historical shard databases. Migration is a separate
administrative operation, not an automatic startup behavior.
