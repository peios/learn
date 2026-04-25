---
title: Streaming
---

## Overview

The STREAM keyword marks a query as a streaming query. It may appear anywhere in the query string and is treated as a boolean flag. Streaming is supported for EVENTS and LOGS queries. METRIC queries do not support streaming.

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

## Backpressure

If a streaming client cannot keep up with the event rate, eventd MUST drop the streaming query and notify the client with an error rather than buffering unboundedly. Streaming queries MUST NOT block or slow the write path.

## Filter restrictions

During the streaming phase, only WHERE predicates (including cross-type conditions) are evaluated against new records. SORT, TAKE, SKIP, COUNT BY, TOP N BY, DISTINCT, and GROUP do not apply to streamed records -- they apply only to the initial result set. Streamed records are delivered in commit order.

SELECT applies to streamed records -- only the specified fields are included.
