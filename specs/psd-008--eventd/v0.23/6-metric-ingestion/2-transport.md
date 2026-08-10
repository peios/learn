---
title: Transport
---

## Metric socket

eventd MUST expose an `AF_UNIX` `SOCK_DGRAM` socket for metric ingestion. The
socket path is configured via the `MetricSocketPath` registry key under
`Machine\System\eventd\`. There is no compiled-in default -- if the key does not
exist or is invalid, eventd MUST fail to start.

After binding the metric socket, eventd MUST set its filesystem mode to `0666`
and MUST NOT rely on process umask for the final permissions. Administrators who
need a narrower coarse gate must place the socket inside a directory with
restrictive permissions. v0.23 does not perform sender identity checks on metric
datagrams (§9.2).

Datagram sockets are used for the same reasons as log ingestion (§4.2): each metric submission is an independent message with no framing concerns, and dropped datagrams under backpressure are acceptable.

eventd MUST receive metric datagrams with a buffer of
`MaxMetricDatagramBytes` bytes. If the kernel reports that a datagram was
truncated, eventd MUST drop that datagram silently.

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| MaxMetricDatagramBytes | REG_DWORD | 262144 | 4096--1048576 | Maximum accepted metric ingestion datagram size in bytes. |

## Metric record format

Each datagram is a single msgpack-encoded map or an array of maps (batched submission). Each map represents one data point for a single time series:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Non-empty metric name (e.g., `cpu.usage`, `http.requests.total`). |
| `labels` | map | No | Key-value string pairs providing dimensions. If omitted, the time series has no labels. |
| `type` | string | Yes | Exactly one of `"counter"`, `"gauge"`, or `"histogram"`. |
| `timestamp` | integer | No | Wall clock timestamp in nanoseconds since Unix epoch. If omitted, eventd uses its receipt time. Both msgpack unsigned integers and non-negative signed integers are accepted if the value is within the v0.23 timestamp domain (§1.3). |
| `value` | varies | Yes | The measurement. For counter and gauge: a single numeric value encoded as a msgpack integer or finite floating-point value. For histogram: a map (see below). |

### Histogram value format

| Field | Type | Description |
|---|---|---|
| `boundaries` | array of numeric | Non-empty finite bucket upper bounds, each encoded as a msgpack integer or finite floating-point value and converted to float64. Boundaries MUST be strictly monotonically increasing after conversion in sender-provided order. |
| `counts` | array of integer | Cumulative count per bucket. Each count MUST be a msgpack unsigned integer or non-negative signed integer. Length MUST equal the length of `boundaries`. Counts MUST be monotonically non-decreasing and each count MUST be less than or equal to `total_count`. |
| `total_count` | integer | Total number of observations. MUST be a msgpack unsigned integer or non-negative signed integer. |
| `sum` | numeric | Finite sum of all observed values, encoded as a msgpack integer or finite floating-point value and converted to float64. |

### Batching

Senders MAY batch multiple metric records into a single datagram by sending a msgpack array of maps. eventd MUST accept both a single map and an array of maps.

Batching is especially valuable for metrics because collection agents typically gather many metrics simultaneously (e.g., collectord reading all CPU cores, all disk devices, and all network interfaces in one pass). The encoded datagram size MUST NOT exceed `MaxMetricDatagramBytes`; larger datagrams are dropped by eventd if received.

## Metric naming conventions

eventd does not enforce naming conventions. The following conventions are recommended but not normative:

- Dot-separated hierarchy: `system.cpu.usage`, `service.http.requests`
- Units as the final component: `disk.read.bytes`, `request.duration.seconds`
- Counter names should reflect the cumulative nature: `http.requests.total`, `errors.total`

## Malformed input handling

The same rules as log ingestion (§4.2) apply:

- Invalid msgpack: drop the entire datagram silently.
- Valid msgpack but not a map or array of maps: drop silently.
- Map missing required fields, with wrong types, or with duplicate top-level
  keys: drop the record silently.
- Unknown top-level fields in a metric record map: ignore the unknown fields.
- Empty metric name or a `type` value other than the exact lowercase strings
  `"counter"`, `"gauge"`, and `"histogram"`: drop the record silently.
- Present timestamp with the wrong type, negative value, or outside the v0.23
  timestamp domain (§1.3): drop the record silently.
- Label keys or values that are empty, are not strings, contain reserved canonicalization delimiters, or duplicate an earlier key in the same labels map: drop the record silently.
- Label keys that use a reserved fixed metric result field name (`timestamp`, `boot_id`, `name`, `type`, or `value`): drop the record silently.
- Counter values with the wrong type, or that convert to a negative or
  non-finite float64 value: drop the record silently.
- Gauge values with the wrong type or that convert to a non-finite float64
  value: drop the record silently.
- Histogram values with duplicate field keys, missing or wrong-type fields, empty
  `boundaries`, boundaries or sum that convert to non-finite float64 values,
  mismatched `boundaries` and `counts` array lengths, non-strictly-increasing
  converted boundaries, negative counts, non-monotonic counts, counts greater
  than `total_count`, or `total_count == 0` with nonzero counts or nonzero `sum`:
  drop the record silently.
- Batched datagrams: invalid records are dropped individually; valid records in the same batch are still processed.
- eventd MUST NOT emit events or log errors in response to malformed metric input.

## Dropped records

As with log ingestion, if the socket receive buffer is full, datagrams are
dropped silently. eventd MAY set the metric socket receive buffer to at most
four times `MaxMetricDatagramBytes`. Metric ingestion MUST NOT exert
backpressure on senders.
