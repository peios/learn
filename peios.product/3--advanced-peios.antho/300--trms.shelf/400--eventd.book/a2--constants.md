---
title: Constants
description: eventd's own constants — access rights, generic mapping, the field GUID namespace, data type roots and origin names.
---

Wire-protocol constants — framing, ingestion limits, the query request
ceiling and response target — belong to the interfaces rather than to
eventd and are in PSPU §3.A.

## Access rights

| Right | Bit | Value | Meaning |
|---|---|---|---|
| `EVENTD_READ` | 0 | 0x0001 | Read records matching the pattern. [*constant.eventd-read-is-bit-0-value-0x0001] |
| `EVENTD_CLEAR` | 1 | 0x0002 | Delete records matching the pattern. Reserved; nothing uses it yet (§7.1). [*constant.eventd-clear-is-bit-1-value-0x0002-and-reserved] |
| `EVENTD_ADMINISTER` | 2 | 0x0004 | Change eventd's own policy — the `INDEX` command. [*constant.eventd-administer-is-bit-2-value-0x0004-and-governs-index] |
| `EVENTD_PUBLISH` | 3 | 0x0008 | Publish metric records under the matching name. [*constant.eventd-publish-is-bit-3-value-0x0008-and-governs-metric-publication] |

## Generic mapping

Passed to AccessCheck in the `generic_read`, `generic_write`,
`generic_execute` and `generic_all` fields.
[*constant.eventd-passes-its-generic-mapping-to-accesscheck]

| Generic right | Value | Composed of |
|---|---|---|
| `GENERIC_READ` | 0x00020001 | `EVENTD_READ` \| `READ_CONTROL` [*constant.generic-read-maps-to-0x00020001] |
| `GENERIC_WRITE` | 0x0002000E | `EVENTD_CLEAR` \| `EVENTD_ADMINISTER` \| `EVENTD_PUBLISH` \| `READ_CONTROL` [*constant.generic-write-maps-to-0x0002000e] |
| `GENERIC_EXECUTE` | 0x00020001 | `EVENTD_READ` \| `READ_CONTROL` [*constant.generic-execute-maps-to-0x00020001] |
| `GENERIC_ALL` | 0x000F000F | `EVENTD_READ` \| `EVENTD_CLEAR` \| `EVENTD_ADMINISTER` \| `EVENTD_PUBLISH` \| `DELETE` \| `READ_CONTROL` \| `WRITE_DAC` \| `WRITE_OWNER` [*constant.generic-all-maps-to-0x000f000f] |

`EVENTD_ADMINISTER` and `EVENTD_PUBLISH` are in `GENERIC_WRITE` and
deliberately not in `GENERIC_READ` or `GENERIC_EXECUTE` (§7.1, §7.6).
[*constant.administer-and-publish-are-not-in-generic-read-or-generic-execute]

## Field GUID namespace [*constant.the-field-guid-namespace-is-e7d3a1b0-5c2f-4e8a-9b1d-0a6f3c8e2d4b]

```text
EVENTD_FIELD_NAMESPACE = {e7d3a1b0-5c2f-4e8a-9b1d-0a6f3c8e2d4b}
```

Field GUIDs are `uuid_v5(EVENTD_FIELD_NAMESPACE, field_name)` with
`field_name` as UTF-8 (§7.3).
[*constant.a-field-guid-is-uuid-v5-of-the-utf-8-field-name-in-the-eventd-namespace]

## Data type root GUIDs

The level-0 node of an object type list.
[*constant.a-data-type-root-guid-is-the-level-0-object-type-list-node]

| Data type | GUID |
|---|---|
| Events | `{a1b2c3d4-0001-4000-8000-000000000001}` [*constant.the-events-root-guid-is-a1b2c3d4-0001-4000-8000-000000000001] |
| Logs | `{a1b2c3d4-0001-4000-8000-000000000002}` [*constant.the-logs-root-guid-is-a1b2c3d4-0001-4000-8000-000000000002] |
| Metrics | `{a1b2c3d4-0001-4000-8000-000000000003}` [*constant.the-metrics-root-guid-is-a1b2c3d4-0001-4000-8000-000000000003] |

## Field names

Field GUIDs are **computed from the algorithm, never hardcoded**.
[*constant.field-guids-are-computed-never-hardcoded] The names they are
computed from are these.

**Event header fields.** `timestamp`, `cpu_id`, `sequence`,
`origin_class`, `event_type`, `effective_token_guid`,
`true_token_guid`, `process_guid`, `boot_id`.
[*constant.the-nine-event-header-field-names]

**Log fields.** `timestamp`, `origin`, `is_error`, `message`, `job_id`,
`boot_id`. [*constant.the-six-log-field-names]

**Fixed metric fields.** `timestamp`, `boot_id`, `name`, `type`,
`value`. [*constant.the-five-fixed-metric-field-names]

**Event payload fields** use the flattened dot path (PSPU §3.22).
[*constant.a-payload-field-name-is-its-flattened-dot-path]
Suppressed paths and paths colliding with a header name are not
query-language fields and have no GUID.
[*constant.suppressed-and-header-colliding-payload-paths-have-no-field-guid]

**Metric label keys** use the key itself: `core` produces
`uuid_v5(EVENTD_FIELD_NAMESPACE, "core")`.
[*constant.a-metric-label-field-name-is-the-label-key-itself] A label key
can never be one of the five fixed metric field names, because ingestion
rejects records whose labels collide with them.
[*constant.ingestion-rejects-labels-that-collide-with-fixed-metric-field-names]

## Origin class

| Value | Origin |
|---|---|
| 0 | userspace [*constant.origin-class-0-is-userspace] |
| 1 | KMES [*constant.origin-class-1-is-kmes] |
| 2 | KACS [*constant.origin-class-2-is-kacs] |
| 3 | LCS [*constant.origin-class-3-is-lcs] |

The query language accepts these names as aliases (PSPU §3.23).
[*constant.the-query-language-accepts-origin-class-names-as-aliases]

## Synthetic event types

| Type | Emitted when |
|---|---|
| `synthetic.startup` | eventd starts and attaches to KMES. [*constant.synthetic-startup-is-emitted-when-eventd-starts-and-attaches-to-kmes] |
| `synthetic.shutdown` | Graceful shutdown begins. [*constant.synthetic-shutdown-is-emitted-when-graceful-shutdown-begins] |
| `synthetic.gap` | A sequence gap is detected on a CPU. [*constant.synthetic-gap-is-emitted-when-a-cpu-sequence-gap-is-detected] |
| `synthetic.config_change` | A configuration value is applied at runtime. [*constant.synthetic-config-change-is-emitted-when-a-value-is-applied-at-runtime] |
| `synthetic.storage_error` | A write to any store fails. [*constant.synthetic-storage-error-is-emitted-when-a-write-to-any-store-fails] |

Payload schemas are in §3.2.

## Metric types

| Value | Type |
|---|---|
| 0 | counter [*constant.metric-type-0-is-counter] |
| 1 | gauge [*constant.metric-type-1-is-gauge] |
| 2 | histogram [*constant.metric-type-2-is-histogram] |

Stored in `series.type`. [*constant.the-metric-type-is-stored-in-series-type]
The query language exposes the names, not the numbers (PSPU §3.22).
[*constant.the-query-language-exposes-metric-type-names-not-numbers]

## Log severity

| Value | Meaning |
|---|---|
| 0 | Normal — standard output. [*constant.log-severity-0-is-normal-standard-output] |
| 1 | Error — standard error, or explicitly marked. [*constant.log-severity-1-is-error-standard-error-or-explicitly-marked] |

Stored as an integer in `logs.is_error`; exposed as a boolean by the
query language, which accepts both forms (§4.2).
[*constant.is-error-is-stored-as-an-integer-and-exposed-as-a-boolean]

## Series hashing

FNV-1a, 64-bit, over the exact bytes of the canonical label string or
the boundary blob.
[*constant.series-hashes-are-64-bit-fnv-1a-over-the-exact-label-string-or-boundary-bytes]

| Parameter | Value |
|---|---|
| Offset basis | `0xcbf29ce484222325` [*constant.the-fnv-offset-basis-is-0xcbf29ce484222325] |
| Prime | `0x100000001b3` [*constant.the-fnv-prime-is-0x100000001b3] |
| Stored as | `hash & 0x7fff_ffff_ffff_ffff` [*constant.the-stored-series-hash-has-its-high-bit-cleared] |

The high bit is cleared so the value fits SQLite's signed `INTEGER`.
Hashes narrow lookups; identity is always confirmed against the full
string or blob (§5.2).
[*constant.series-identity-is-always-confirmed-against-the-full-string-or-blob]

## Schema versions

| Store | Version |
|---|---|
| Event shard | 1 [*constant.the-event-shard-schema-version-is-1] |
| Log store | 1 [*constant.the-log-store-schema-version-is-1] |
| Metric store | 2 [*constant.the-metric-store-schema-version-is-2] |
| `eventd-meta.db` | 1 [*constant.the-metadata-database-schema-version-is-1] |

An unrecognised version is never migrated.
[*constant.an-unrecognised-schema-version-is-never-migrated] For a
required store it fails startup; for a historical shard it excludes the
shard from the query path; for the metadata database it recreates from
defaults (§3.3, §3.5).
[*constant.an-unrecognised-version-fails-a-required-store-excludes-a-historical-shard-and-recreates-metadata]
