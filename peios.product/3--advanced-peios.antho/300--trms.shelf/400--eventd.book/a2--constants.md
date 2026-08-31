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
| `EVENTD_READ` | 0 | 0x0001 | Read records matching the pattern. |
| `EVENTD_CLEAR` | 1 | 0x0002 | Delete records matching the pattern. Reserved; nothing uses it yet (§7.1). |
| `EVENTD_ADMINISTER` | 2 | 0x0004 | Change eventd's own policy — the `INDEX` command. |
| `EVENTD_PUBLISH` | 3 | 0x0008 | Publish metric records under the matching name. |

## Generic mapping

Passed to AccessCheck in the `generic_read`, `generic_write`,
`generic_execute` and `generic_all` fields.

| Generic right | Value | Composed of |
|---|---|---|
| `GENERIC_READ` | 0x00020001 | `EVENTD_READ` \| `READ_CONTROL` |
| `GENERIC_WRITE` | 0x0002000E | `EVENTD_CLEAR` \| `EVENTD_ADMINISTER` \| `EVENTD_PUBLISH` \| `READ_CONTROL` |
| `GENERIC_EXECUTE` | 0x00020001 | `EVENTD_READ` \| `READ_CONTROL` |
| `GENERIC_ALL` | 0x000F000F | `EVENTD_READ` \| `EVENTD_CLEAR` \| `EVENTD_ADMINISTER` \| `EVENTD_PUBLISH` \| `DELETE` \| `READ_CONTROL` \| `WRITE_DAC` \| `WRITE_OWNER` |

`EVENTD_ADMINISTER` and `EVENTD_PUBLISH` are in `GENERIC_WRITE` and
deliberately not in `GENERIC_READ` or `GENERIC_EXECUTE` (§7.1, §7.6).

## Field GUID namespace

```text
EVENTD_FIELD_NAMESPACE = {e7d3a1b0-5c2f-4e8a-9b1d-0a6f3c8e2d4b}
```

Field GUIDs are `uuid_v5(EVENTD_FIELD_NAMESPACE, field_name)` with
`field_name` as UTF-8 (§7.3).

## Data type root GUIDs

The level-0 node of an object type list.

| Data type | GUID |
|---|---|
| Events | `{a1b2c3d4-0001-4000-8000-000000000001}` |
| Logs | `{a1b2c3d4-0001-4000-8000-000000000002}` |
| Metrics | `{a1b2c3d4-0001-4000-8000-000000000003}` |

## Field names

Field GUIDs are **computed from the algorithm, never hardcoded**. The
names they are computed from are these.

**Event header fields.** `timestamp`, `cpu_id`, `sequence`,
`origin_class`, `event_type`, `effective_token_guid`,
`true_token_guid`, `process_guid`, `boot_id`.

**Log fields.** `timestamp`, `origin`, `is_error`, `message`, `job_id`,
`boot_id`.

**Fixed metric fields.** `timestamp`, `boot_id`, `name`, `type`,
`value`.

**Event payload fields** use the flattened dot path (PSPU §3.22).
Suppressed paths and paths colliding with a header name are not
query-language fields and have no GUID.

**Metric label keys** use the key itself: `core` produces
`uuid_v5(EVENTD_FIELD_NAMESPACE, "core")`. A label key can never be one
of the five fixed metric field names, because ingestion rejects records
whose labels collide with them.

## Origin class

| Value | Origin |
|---|---|
| 0 | userspace |
| 1 | KMES |
| 2 | KACS |
| 3 | LCS |

The query language accepts these names as aliases (PSPU §3.23).

## Synthetic event types

| Type | Emitted when |
|---|---|
| `synthetic.startup` | eventd starts and attaches to KMES. |
| `synthetic.shutdown` | Graceful shutdown begins. |
| `synthetic.gap` | A sequence gap is detected on a CPU. |
| `synthetic.config_change` | A configuration value is applied at runtime. |
| `synthetic.storage_error` | A write to any store fails. |

Payload schemas are in §3.2.

## Metric types

| Value | Type |
|---|---|
| 0 | counter |
| 1 | gauge |
| 2 | histogram |

Stored in `series.type`. The query language exposes the names, not the
numbers (PSPU §3.22).

## Log severity

| Value | Meaning |
|---|---|
| 0 | Normal — standard output. |
| 1 | Error — standard error, or explicitly marked. |

Stored as an integer in `logs.is_error`; exposed as a boolean by the
query language, which accepts both forms (§4.2).

## Series hashing

FNV-1a, 64-bit, over the exact bytes of the canonical label string or
the boundary blob.

| Parameter | Value |
|---|---|
| Offset basis | `0xcbf29ce484222325` |
| Prime | `0x100000001b3` |
| Stored as | `hash & 0x7fff_ffff_ffff_ffff` |

The high bit is cleared so the value fits SQLite's signed `INTEGER`.
Hashes narrow lookups; identity is always confirmed against the full
string or blob (§5.2).

## Schema versions

| Store | Version |
|---|---|
| Event shard | 1 |
| Log store | 1 |
| Metric store | 2 |
| `eventd-meta.db` | 1 |

An unrecognised version is never migrated. For a required store it fails
startup; for a historical shard it excludes the shard from the query
path; for the metadata database it recreates from defaults (§3.3, §3.5).
