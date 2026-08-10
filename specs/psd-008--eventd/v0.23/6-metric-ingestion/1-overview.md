---
title: Overview
---

Metrics are numeric measurements over time. CPU usage, memory consumption, request counts, queue depths, error rates -- any quantity that varies and is worth tracking. Metrics are fundamentally different from events and logs: they are dense time-series data (many samples of the same measurement) rather than discrete occurrences or text output.

eventd is a metric sink, not a metric collector. Services and collection agents push metrics to eventd. eventd does not scrape endpoints, read from /proc, or poll for data. The collection mechanism (e.g., a collectord daemon that gathers system metrics) is outside eventd's scope.

## Data model

A metric data point consists of:

- **Name** -- a non-empty string identifying the measurement (e.g., `cpu.usage`, `http.requests.total`, `disk.read.bytes`).
- **Labels** -- a set of key-value string pairs providing dimensions (e.g., `core="0"`, `service="loregd"`, `method="GET"`). Labels distinguish different instances of the same measurement. Label keys and values MUST be non-empty UTF-8 strings. Label keys and values MUST NOT contain the characters `=` (0x3D) or `,` (0x2C), as these are used as delimiters in the canonical label representation (§7.1). Label keys MUST NOT equal any fixed metric result field name: `timestamp`, `boot_id`, `name`, `type`, or `value`. Duplicate label keys are invalid. Records with invalid label keys or values MUST be dropped silently.
- **Type** -- one of counter, gauge, or histogram. The type determines how the metric is interpreted by the query engine.
- **Timestamp** -- wall clock time of the measurement.
- **Value** -- the numeric measurement. The encoding depends on the type. Metric
  numeric inputs are msgpack integers or msgpack floating-point values converted
  to IEEE-754 binary64 using round-to-nearest, ties-to-even. Floating-point
  values MUST be finite; records containing NaN, positive infinity, or negative
  infinity MUST be dropped silently.

For counter and gauge metrics, the combination of name and labels identifies a time series. For histogram metrics, the combination of name, labels, and bucket boundaries identifies a time series. The metric type is immutable metadata for a series; if a later record resolves to an existing series but has a different type, eventd MUST drop that record silently. `cpu.usage{core="0"}` and `cpu.usage{core="1"}` are distinct time series.

> [!INFORMATIVE]
> Labels with unbounded cardinality (per-request IDs, user-provided strings, timestamps as label values) cause series table growth proportional to the number of unique label combinations. Each unique combination creates a new series row and a new entry in the bounded series cache. When the number of active series exceeds the cache size, every collection cycle evicts and reloads the overflow, causing sustained SQLite lookups on the single metric ingestion thread. This is a well-known anti-pattern in metrics systems. Emitters SHOULD use labels with bounded, low-cardinality values (e.g., CPU core ID, service name, HTTP method). High-cardinality dimensions belong in event payloads, not metric labels.

## Metric types

### Counter

A monotonically increasing value that resets to zero when the emitting process restarts. Used for cumulative quantities: total requests served, total bytes transmitted, total errors encountered.

The raw counter value is rarely queried directly. The query engine derives rate (change per unit time) from counter samples, handling resets correctly.

A counter value MUST be a finite, non-negative 64-bit floating-point number.

### Gauge

A point-in-time value that can increase or decrease arbitrarily. Used for current state: CPU usage percentage, memory in use, queue depth, temperature.

The raw gauge value is the measurement. Aggregation over time uses min, max, and average -- not rate.

A gauge value MUST be a finite 64-bit floating-point number (may be negative).

### Histogram

A distribution of observed values across predefined buckets. Used for latency, request sizes, and other quantities where the distribution matters more than the average.

A histogram value consists of:

- A non-empty array of bucket boundaries (upper bounds), strictly monotonically
  increasing in sender-provided order.
- An array of cumulative counts, one per bucket. Each count represents the number of observations less than or equal to the corresponding boundary. Counts MUST be monotonically non-decreasing and each count MUST be less than or equal to `total_count`.
- A total count of all observations.
- A finite sum of all observed values.

Bucket boundaries are defined by the emitter and MUST be consistent across all samples of the same time series. eventd MUST NOT sort or reinterpret boundary order. If bucket boundaries change, it is treated as a new time series.

The final bucket count MAY be less than `total_count`; observations above the
highest explicit boundary are represented by the difference between
`total_count` and the final cumulative bucket count. A `total_count` of zero is
valid and represents an empty histogram sample; in that case all cumulative
counts and `sum` MUST be zero.

## Loss tolerance

Metric loss has similar tolerance characteristics to log loss. A missed data
point creates a gap in the time series -- the gap is visible but not
catastrophic. eventd preserves the gap; v0.23 query execution does not
interpolate missing metric samples. Services MUST NOT assume lossless metric
delivery.
