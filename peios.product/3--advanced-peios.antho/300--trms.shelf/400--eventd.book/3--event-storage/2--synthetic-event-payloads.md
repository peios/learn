---
title: Synthetic Event Payloads
description: The MessagePack schema of each of the five synthetic event types, whose field names are stable query-language surface.
---

Each of the five synthetic event types (§2.6) carries a MessagePack map
in `payload`, with the schema below.
[*payload.every-synthetic-event-carries-a-messagepack-map] These field names are stable
query-language payload field names after flattening (PSPU §3.22), except
where a value is a nested array or map, which flattening does not
traverse.
[*payload.synthetic-field-names-are-stable-query-fields-except-nested-values]
None of them is at a header field's path, so none is suppressed:
`boot_id` in `synthetic.startup` and `cpu_id` in `synthetic.gap` are
payload fields like the rest, and the boot and CPU columns are read as
`event.boot.guid` and `event.cpu` (§3.1).

## `synthetic.startup` [*payload.the-synthetic-startup-payload-schema]

| Field | Type | Contents |
|---|---|---|
| `boot_id` | string | The current boot ID, PCDS canonical GUID form. [*payload.startup-boot-id-is-the-current-boot-in-canonical-guid-form] |
| `restart` | bool | True when committed rows or receipts for this boot already existed at startup; false on the boot's first successful eventd start. [*payload.startup-restart-is-true-when-the-boot-already-had-committed-rows-or-receipts] |
| `shard_count` | unsigned integer | Active shard count after resolving `StorageShards`. [*payload.startup-shard-count-is-the-resolved-active-shard-count] |
| `resume_points` | array of map | One entry per logical CPU, ordered by `cpu_id` ascending. Each has `cpu_id` and `sequence`, the highest sequence contiguously accounted for after receipt/ring reconciliation, or 0. [*payload.startup-resume-points-give-each-cpus-highest-contiguous-sequence-in-cpu-order] |

`restart` is the boot-boundary decision of §3.7 recorded as data, which
makes "did eventd crash during this boot, and how often" answerable by
query rather than by inference from gaps.

## `synthetic.shutdown` [*payload.the-synthetic-shutdown-payload-schema]

| Field | Type | Contents |
|---|---|---|
| `last_sequences` | array of map | One entry per logical CPU, ordered by `cpu_id` ascending. Each has `cpu_id` and `sequence` — the highest sequence contiguously covered by committed receipts for that CPU this boot, or 0 if none was. [*payload.shutdown-last-sequences-give-each-cpus-highest-contiguous-receipted-sequence] |

Diagnostic only. Startup derives recovery coverage from committed
receipt ranges, never from this payload (§2.2).
[*payload.startup-never-derives-recovery-coverage-from-the-shutdown-payload]

## `synthetic.gap` [*payload.the-synthetic-gap-payload-schema]

| Field | Type | Contents |
|---|---|---|
| `cpu_id` | unsigned integer | Where the gap was detected. [*payload.gap-cpu-id-is-where-the-gap-was-detected] |
| `first_sequence` | unsigned integer | First missing sequence number. [*payload.gap-first-sequence-is-the-first-missing-sequence] |
| `last_sequence` | unsigned integer | Last missing sequence number. [*payload.gap-last-sequence-is-the-last-missing-sequence] |
| `count` | unsigned integer | How many are missing. [*payload.gap-count-is-how-many-sequences-are-missing] |
| `last_seen_timestamp` | timestamp or nil | The last event successfully processed before the gap, when known. [*payload.gap-last-seen-timestamp-is-the-last-event-before-the-gap-or-nil] |
| `revealing_timestamp` | timestamp | The event or ring position that revealed the gap. [*payload.gap-revealing-timestamp-is-what-revealed-the-gap] |

`cpu_id` appears both here and in the `cpu_id` column (§2.5).
[*payload.a-gap-carries-cpu-id-in-both-the-payload-and-the-column] The column
is what a `WHERE event.cpu == N` predicate matches and what a query
presents as `event.cpu`; the payload field is what `WHERE cpu_id == N`
matches and a query presents as `cpu_id`, and what a reader of the
stored payload sees without joining anything.
[*payload.an-event-cpu-predicate-matches-the-gap-column-and-cpu-id-the-payload-field]

## `synthetic.config_change` [*payload.the-synthetic-config-change-payload-schema]

| Field | Type | Contents |
|---|---|---|
| `key` | string | The key name, relative to `Machine\System\eventd\`. [*payload.config-change-key-is-relative-to-the-eventd-configuration-key] |
| `old_value_type` | string | `absent`, `REG_SZ`, `REG_DWORD`, `REG_QWORD` or `REG_BINARY`. [*payload.config-change-old-value-type-is-absent-or-one-of-four-registry-types] |
| `old_value` | string or nil | The previous value rendered as below; nil when the type is `absent`. [*payload.config-change-old-value-is-nil-when-absent] |
| `new_value_type` | string | The same five. [*payload.config-change-new-value-type-uses-the-same-five-names] |
| `new_value` | string or nil | The new value; nil when `absent`. [*payload.config-change-new-value-is-nil-when-absent] |

Values are rendered deterministically so that two eventd instances
observing the same change record the same bytes: `REG_SZ` as the string
in UTF-8, `REG_DWORD` and `REG_QWORD` as unsigned decimal without
leading zeroes, `REG_BINARY` as lowercase hexadecimal, two digits per
byte.
[*payload.config-values-render-as-utf8-unpadded-decimal-or-lowercase-hex]

Everything is a string, including numbers, because the field is the same
field for all five types and a query filtering `WHERE key == "…"` should
not have to know which.
[*payload.config-change-values-are-strings-even-for-numeric-types]

## `synthetic.storage_error` [*payload.the-synthetic-storage-error-payload-schema]

| Field | Type | Contents |
|---|---|---|
| `store` | string | `event`, `log`, `metric` or `metadata`. [*payload.storage-error-store-is-event-log-metric-or-metadata] |
| `shard_index` | unsigned integer or nil | The shard for event-store errors; nil for the other three. [*payload.storage-error-shard-index-is-set-only-for-event-store-errors] |
| `error` | string | Human-readable description. [*payload.storage-error-error-is-a-human-readable-description] |

`error` is diagnostic text and its wording is not stable. `store` and
`shard_index` are the fields worth alerting on.
