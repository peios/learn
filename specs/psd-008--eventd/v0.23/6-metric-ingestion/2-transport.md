---
title: Transport
---

## Metric socket

eventd MUST expose a Unix domain datagram socket for metric ingestion. The socket path is configured via the `MetricSocketPath` registry key under `Machine\System\eventd\`. There is no compiled-in default -- if the key does not exist or is invalid, eventd MUST fail to start.

Datagram sockets are used for the same reasons as log ingestion (§4.2): each metric submission is an independent message with no framing concerns, and dropped datagrams under backpressure are acceptable.

## Metric record format

Each datagram is a single msgpack-encoded map or an array of maps (batched submission). Each map represents one or more data points for a single time series:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Metric name. Dot-separated hierarchical string (e.g., `cpu.usage`, `http.requests.total`). |
| `labels` | map | No | Key-value string pairs providing dimensions. If omitted, the time series has no labels. |
| `type` | string | Yes | One of `"counter"`, `"gauge"`, or `"histogram"`. |
| `timestamp` | u64 | No | Wall clock timestamp in nanoseconds since Unix epoch. If omitted, eventd uses its receipt time. |
| `value` | varies | Yes | The measurement. For counter and gauge: a single f64. For histogram: a map (see below). |

### Histogram value format

| Field | Type | Description |
|---|---|---|
| `boundaries` | array of f64 | Bucket upper bounds, monotonically increasing. |
| `counts` | array of u64 | Cumulative count per bucket. Length MUST equal the length of `boundaries`. |
| `total_count` | u64 | Total number of observations. |
| `sum` | f64 | Sum of all observed values. |

### Batching

Senders MAY batch multiple metric records into a single datagram by sending a msgpack array of maps. eventd MUST accept both a single map and an array of maps.

Batching is especially valuable for metrics because collection agents typically gather many metrics simultaneously (e.g., collectord reading all CPU cores, all disk devices, and all network interfaces in one pass).

## Metric naming conventions

eventd does not enforce naming conventions. The following conventions are recommended but not normative:

- Dot-separated hierarchy: `system.cpu.usage`, `service.http.requests`
- Units as the final component: `disk.read.bytes`, `request.duration.seconds`
- Counter names should reflect the cumulative nature: `http.requests.total`, `errors.total`

## Malformed input handling

The same rules as log ingestion (§4.2) apply:

- Invalid msgpack: drop the entire datagram silently.
- Valid msgpack but not a map or array of maps: drop silently.
- Map missing required fields or with wrong types: drop the record silently.
- Histogram value with mismatched `boundaries` and `counts` array lengths, or non-monotonic boundaries: drop the record silently.
- Batched datagrams: invalid records are dropped individually; valid records in the same batch are still processed.
- eventd MUST NOT emit events or log errors in response to malformed metric input.

## Dropped records

As with log ingestion, if the socket receive buffer is full, datagrams are dropped silently. Metric ingestion MUST NOT exert backpressure on senders.
