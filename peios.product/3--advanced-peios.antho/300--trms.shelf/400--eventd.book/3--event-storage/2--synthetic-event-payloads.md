---
title: Synthetic Event Payloads
description: The MessagePack schema of each of the five synthetic event types, whose field names are stable query-language surface.
---

Each of the five synthetic event types (§2.6) carries a MessagePack map
in `payload`, with the schema below. These field names are stable
query-language payload field names after flattening (PSPU §3.22), except
where a value is a nested array or map, which flattening does not
traverse.

## `synthetic.startup`

| Field | Type | Contents |
|---|---|---|
| `boot_id` | string | The current boot ID, PCDS canonical GUID form. |
| `restart` | bool | True when committed rows or receipts for this boot already existed at startup; false on the boot's first successful eventd start. |
| `shard_count` | unsigned integer | Active shard count after resolving `StorageShards`. |
| `resume_points` | array of map | One entry per logical CPU, ordered by `cpu_id` ascending. Each has `cpu_id` and `sequence`, the highest sequence contiguously accounted for after receipt/ring reconciliation, or 0. |

`restart` is the boot-boundary decision of §3.7 recorded as data, which
makes "did eventd crash during this boot, and how often" answerable by
query rather than by inference from gaps.

## `synthetic.shutdown`

| Field | Type | Contents |
|---|---|---|
| `last_sequences` | array of map | One entry per logical CPU, ordered by `cpu_id` ascending. Each has `cpu_id` and `sequence` — the highest sequence contiguously covered by committed receipts for that CPU this boot, or 0 if none was. |

Diagnostic only. Startup derives recovery coverage from committed
receipt ranges, never from this payload (§2.2).

## `synthetic.gap`

| Field | Type | Contents |
|---|---|---|
| `cpu_id` | unsigned integer | Where the gap was detected. |
| `first_sequence` | unsigned integer | First missing sequence number. |
| `last_sequence` | unsigned integer | Last missing sequence number. |
| `count` | unsigned integer | How many are missing. |
| `last_seen_timestamp` | timestamp or nil | The last event successfully processed before the gap, when known. |
| `revealing_timestamp` | timestamp | The event or ring position that revealed the gap. |

`cpu_id` appears both here and in the `cpu_id` column (§2.5). The column
is what a `WHERE cpu_id == N` predicate matches; the payload field is
what a reader of the record sees without joining anything.

## `synthetic.config_change`

| Field | Type | Contents |
|---|---|---|
| `key` | string | The key name, relative to `Machine\System\eventd\`. |
| `old_value_type` | string | `absent`, `REG_SZ`, `REG_DWORD`, `REG_QWORD` or `REG_BINARY`. |
| `old_value` | string or nil | The previous value rendered as below; nil when the type is `absent`. |
| `new_value_type` | string | The same five. |
| `new_value` | string or nil | The new value; nil when `absent`. |

Values are rendered deterministically so that two eventd instances
observing the same change record the same bytes: `REG_SZ` as the string
in UTF-8, `REG_DWORD` and `REG_QWORD` as unsigned decimal without
leading zeroes, `REG_BINARY` as lowercase hexadecimal, two digits per
byte.

Everything is a string, including numbers, because the field is the same
field for all five types and a query filtering `WHERE key == "…"` should
not have to know which.

## `synthetic.storage_error`

| Field | Type | Contents |
|---|---|---|
| `store` | string | `event`, `log`, `metric` or `metadata`. |
| `shard_index` | unsigned integer or nil | The shard for event-store errors; nil for the other three. |
| `error` | string | Human-readable description. |

`error` is diagnostic text and its wording is not stable. `store` and
`shard_index` are the fields worth alerting on.
