---
title: Streaming
---

## Overview

The STREAM keyword marks a query as a streaming query. It may appear anywhere in the query string and is treated as a boolean flag. Streaming is supported for EVENTS and LOGS queries. METRIC queries do not support streaming.

> [!INFORMATIVE]
> Streaming queries are a convenience for interactive tailing and dashboards. Streaming behaviour can feel unintuitive under unusual conditions (cross-type filters evaluated per-batch rather than per-event, high-frequency metric thresholds, backpressure disconnects). Where more predictable results are needed, repeated non-streaming queries with a sliding SINCE window are a more reliable approach. Where minimal latency is critical (security monitoring, anti-virus), direct KMES ring buffer attachment via a dedicated tool (e.g., `revstr`) bypasses eventd entirely and provides sub-millisecond event access.

> [!INFORMATIVE]
> Metric streaming is omitted from v0.23 because metric data is sampled at regular intervals (typically every 15 seconds) and the primary metric consumer is a dashboard that polls. Live streaming of individual metric samples adds complexity with limited value for the typical use case. Future versions may add metric streaming if demand warrants it.

## Behavior

1. eventd executes the query normally and delivers the initial result set.
2. Instead of closing the query, eventd enters a watch state.
3. When new records are committed to the relevant store(s), eventd evaluates them against the query's filters.
4. Matching records are delivered to the client.
5. The loop continues until the client disconnects or the query is cancelled.

## Notification

Writer threads signal when a batch commit completes. Streaming query handlers wait for this signal rather than polling. The signal mechanism is implementation-defined.

## Latency

Streaming latency is bounded by the batch commit interval of the relevant store. For events, this is approximately `MaxBatchLatencyMs` (default 100ms). For logs, approximately `LogMaxBatchLatencyMs` (default 500ms). The actual latency may be lower under light load when the adaptive batcher commits more frequently.

## Connection limits

eventd MUST enforce a maximum number of concurrent streaming queries to prevent resource exhaustion from malicious or excessive streaming connections.

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| MaxStreamingQueries | REG_DWORD | 64 | 1--1024 | Maximum number of concurrent streaming queries across all clients. |

When the limit is reached, new streaming queries MUST be rejected with an error. Non-streaming queries are unaffected by this limit.

> [!INFORMATIVE]
> The global limit prevents total resource exhaustion but does not prevent a single caller from consuming all available slots. Per-caller limits (e.g., maximum streaming queries per process GUID) would provide fairer allocation, but require a KACS primitive for identifying the caller's process GUID on the query socket connection. This is the same datagram peer identity gap noted in §9.2 -- until KACS provides the necessary primitives, per-caller streaming limits are not possible. The global limit is the interim protection.

## Backpressure

If a streaming client cannot keep up with the event rate, eventd MUST drop the streaming query and notify the client with an error rather than buffering unboundedly. Streaming queries MUST NOT block or slow the write path.

Backpressure is detected via the socket send buffer. When eventd attempts to send a result message to a streaming client and the socket send buffer is full, the streaming query MUST be terminated immediately. eventd MUST NOT block on the send. The client receives an error message if the socket can still accept it; otherwise the connection is closed.

## Cross-type conditions during streaming

The initial result set uses pre-computed time ranges for cross-type conditions (§8.5). During the streaming phase, pre-computed ranges are stale and MUST NOT be reused.

For each committed batch, eventd MUST re-evaluate cross-type conditions against the current state of the referenced store. For metric conditions (WHERE METRIC), eventd queries the most recent sample for the referenced series using the batch's latest event timestamp and evaluates the condition against that sample. This is a single index seek per cross-type condition per batch.

If the condition is not met, the entire batch is filtered out (no records delivered for that batch). If the condition is met, the batch's records are filtered by the remaining WHERE predicates as normal.

> [!INFORMATIVE]
> Evaluating the metric condition once per batch (using the batch's latest timestamp) rather than once per event is an optimisation that produces identical results at typical metric sample intervals (15 seconds). The batch commit interval (default 100ms) is far shorter than the metric sample interval, so all events in a batch map to the same metric sample. At abnormally high metric resolutions (sub-second sampling), this optimisation can produce slightly coarser filtering than per-event evaluation -- events near a metric threshold crossing may be included or excluded as a group rather than individually.

## Filter restrictions

During the streaming phase, only WHERE predicates (including cross-type conditions) are evaluated against new records. SORT, TAKE, SKIP, COUNT BY, TOP N BY, DISTINCT, and GROUP do not apply to streamed records -- they apply only to the initial result set. Streamed records are delivered in commit order.

SELECT applies to streamed records -- only the specified fields are included.
