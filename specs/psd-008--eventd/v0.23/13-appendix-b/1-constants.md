---
title: Constants
---

## Access rights

| Right | Value | Description |
|---|---|---|
| EVENTD_READ | 0x0001 | Read records matching the security pattern. |
| EVENTD_CLEAR | 0x0002 | Delete records matching the security pattern. |

## Generic mapping

| Generic right | Maps to |
|---|---|
| GENERIC_READ | 0x00020001 (EVENTD_READ \| READ_CONTROL) |
| GENERIC_WRITE | 0x00020002 (EVENTD_CLEAR \| READ_CONTROL) |
| GENERIC_EXECUTE | 0x00020001 (EVENTD_READ \| READ_CONTROL) |
| GENERIC_ALL | 0x000F0003 (EVENTD_READ \| EVENTD_CLEAR \| DELETE \| READ_CONTROL \| WRITE_DAC \| WRITE_OWNER) |

## Field GUID namespace

All field GUIDs are generated using UUID v5 (RFC 4122) with the following namespace UUID:

```
EVENTD_FIELD_NAMESPACE = {e7d3a1b0-5c2f-4e8a-9b1d-0a6f3c8e2d4b}
```

Field GUIDs are computed as `uuid_v5(EVENTD_FIELD_NAMESPACE, field_name)` where `field_name` is the UTF-8 field name string.

## Data type root GUIDs

Used as the level-0 node in object type lists for access checks.

| Data type | GUID |
|---|---|
| Events | `{a1b2c3d4-0001-4000-8000-000000000001}` |
| Logs | `{a1b2c3d4-0001-4000-8000-000000000002}` |
| Metrics | `{a1b2c3d4-0001-4000-8000-000000000003}` |

## Well-known field GUIDs

Computed from `uuid_v5(EVENTD_FIELD_NAMESPACE, field_name)` for reference. Implementations MUST compute these from the algorithm, not hardcode them.

### Event header fields

| Field name | Description |
|---|---|
| `timestamp` | Wall clock time. |
| `cpu_id` | CPU identifier. |
| `sequence` | Per-CPU sequence number. |
| `origin_class` | Origin class (userspace, KMES, KACS, LCS). |
| `event_type` | Event type string. |
| `effective_token_guid` | Effective token GUID. |
| `true_token_guid` | Process primary token GUID. |
| `process_guid` | Process GUID. |
| `boot_id` | Boot ID GUID. |

### Log fields

| Field name | Description |
|---|---|
| `timestamp` | Wall clock time. |
| `origin` | Service name. |
| `is_error` | stderr flag. |
| `message` | Log text. |
| `boot_id` | Boot ID GUID. |

### Metric fields

| Field name | Description |
|---|---|
| `timestamp` | Sample time. |
| `name` | Metric name. |
| `type` | Metric type (counter, gauge, histogram). |
| `value` | Numeric value. |

Metric label keys produce field GUIDs using the same algorithm. Label key `"core"` produces `uuid_v5(EVENTD_FIELD_NAMESPACE, "core")`.

## Synthetic event types

| Event type | Emitted when |
|---|---|
| `synthetic.startup` | eventd starts and attaches to KMES. |
| `synthetic.shutdown` | eventd begins graceful shutdown. |
| `synthetic.gap` | Sequence gap detected on a CPU. |
| `synthetic.config_change` | Configuration value applied at runtime. |
| `synthetic.storage_error` | Write failure on any store. |

## Metric type identifiers

| Value | Type |
|---|---|
| 0 | Counter |
| 1 | Gauge |
| 2 | Histogram |

## Rollup function identifiers

| Value | Function |
|---|---|
| 0 | AVG |
| 1 | MIN |
| 2 | MAX |
| 3 | SUM |
| 4 | RATE |
| 5 | DELTA |

Percentile functions (P50, P95, P99) are not rollup-eligible. They are computed from raw samples only.

## Log severity

| Value | Meaning |
|---|---|
| 0 | Normal (stdout). |
| 1 | Error (stderr). |

> [!INFORMATIVE]
> The `is_error` column stores this as an integer. The query language exposes it as a boolean. The query engine MUST accept both boolean (`WHERE is_error == true`) and integer (`WHERE is_error == 1`) comparisons -- `true` is equivalent to `1` and `false` is equivalent to `0`. The `ERROR ONLY` clause is syntactic sugar for `WHERE is_error == true`.

## Schema versions

| Store | Schema version |
|---|---|
| Event shard databases | 1 |
| Log store database | 1 |
| Metric store database | 1 |

## Wire protocol

| Field | Size | Type | Description |
|---|---|---|---|
| Message length | 4 bytes | u32 LE | Length of the msgpack payload. |
| Message payload | variable | msgpack | Request or response body. |

### Query response status values

| Status | Meaning |
|---|---|
| `"ok"` | Result records follow in the `records` field. |
| `"end"` | No more results. Query complete. |
| `"error"` | Error occurred. Description in the `error` field. |
