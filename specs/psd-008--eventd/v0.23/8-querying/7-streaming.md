---
title: Streaming
---

## Overview

The STREAM keyword marks a query as a streaming query. It may appear anywhere in the query string and is treated as a boolean flag. Streaming is supported for EVENTS and LOGS queries. METRIC queries do not support streaming.

Streaming supports raw event/log record queries and DISTINCT event/log queries.
A STREAM query that uses `COUNT BY`, `TOP N BY`, or `GROUP` MUST be rejected
with a parse error. `DISTINCT ... STREAM` has distinct-value streaming semantics
defined below.

`STREAM` MUST NOT be combined with `UNTIL`; this is a parse error. `SINCE` is
allowed and applies to both the initial result set and later committed records
using the query evaluation time captured at query start.

> [!INFORMATIVE]
> Streaming queries are a convenience for interactive tailing and dashboards. Streaming behaviour can feel unintuitive under unusual conditions (cross-type filters evaluated per-batch rather than per-event, high-frequency metric thresholds, backpressure disconnects). Where more predictable results are needed, repeated non-streaming queries with a sliding SINCE window are a more reliable approach. Where minimal latency is critical (security monitoring, anti-virus), direct KMES ring buffer attachment via a dedicated tool (e.g., `revstr`) bypasses eventd entirely and provides sub-millisecond event access.

> [!INFORMATIVE]
> Metric streaming is omitted from v0.23 because metric data is sampled at regular intervals (typically every 15 seconds) and the primary metric consumer is a dashboard that polls. Live streaming of individual metric samples adds complexity with limited value for the typical use case. Future versions may add metric streaming if demand warrants it.

## Behavior

1. eventd executes the query normally and delivers the initial result set.
2. eventd sends a streaming `watch` response message to mark that the initial
   result set is complete.
3. Instead of closing the query, eventd enters a watch state.
4. When new records are committed to the relevant store(s), eventd evaluates them against the query's filters.
5. For raw-record streams, matching records are delivered to the client. For
   DISTINCT streams, newly seen distinct values are delivered to the client.
6. The loop continues until the client disconnects or the query is cancelled.

## DISTINCT streaming

A DISTINCT streaming query keeps the fixed DISTINCT output schema defined in
§8.2 for both the initial result set and the streaming phase:

```
EVENTS kacs.* DISTINCT process_guid STREAM
LOGS DISTINCT origin STREAM
```

The initial result set contains the complete distinct set visible at query
start, after access control, primary selector filtering, SINCE filtering, WHERE,
and cross-type filters. eventd then initializes a per-query seen set from that
initial result set. During the streaming phase, each newly committed record that
passes access control and filters is reduced to the DISTINCT field value. eventd
emits `{field: representative}` only if that value is not already present in the
seen set under the grouping equality rules in §8.1; emitted values are then
inserted into the seen set.

The DISTINCT stream seen set is bounded by `MaxDistinctStreamValues`. The limit
applies to the initial distinct values plus values discovered during streaming.
If initializing the seen set or inserting a newly discovered value would exceed
the limit, eventd MUST terminate the streaming query with an error. eventd MUST
NOT evict old seen values, because eviction would make "newly seen" semantics
incorrect.

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| MaxDistinctStreamValues | REG_DWORD | 100000 | 1000--10000000 | Maximum number of values tracked by one DISTINCT streaming query. |

`DISTINCT ... STREAM` MUST NOT be combined with explicit SORT, TAKE, or SKIP.
Those clauses are rejected with a parse error so that the seen set always
matches the full initial visible distinct set. SELECT is already invalid with
DISTINCT queries (§8.2).

## Notification

eventd MUST maintain a monotonic `u64` commit generation counter for each
streamable store: one counter for the event store as a whole and one counter
for the log store. After a writer successfully commits a batch, it increments
the corresponding counter and wakes streaming query handlers waiting on that
store. A streaming handler records the last generation it processed and waits
until the counter is greater than that value. The counter is process-local and
is not persisted. If it wraps, eventd MUST treat the next increment as a wake
for all handlers and continue; at normal commit rates wraparound is not
operationally reachable.

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

For each committed batch, eventd MUST re-evaluate cross-type conditions against
the current state of the referenced store. For metric conditions (WHERE METRIC),
the selector must have resolved to exactly one time series as required by §8.5.
eventd finds the active sample for that series at the batch's latest candidate
record timestamp using the interval semantics in §8.5, then evaluates the
condition against that sample. If no sample is active at that timestamp, the
condition is false. This is a single index seek per cross-type condition per
batch.

For event and log EXISTS conditions during streaming, eventd applies the
centered half-open `CrossTypeWindowMs` rule from §8.5 to each streamed candidate
record's timestamp. These EXISTS conditions are evaluated per record, not once
per batch, because the matching event/log record may be close to only part of
the committed batch.

If a metric cross-type condition is not met, the entire batch is filtered out
(no records delivered for that batch). If the metric condition is met, the
batch's records are filtered by the remaining WHERE predicates as normal. Event
and log EXISTS cross-type conditions are evaluated per candidate record and
filter only records whose centered EXISTS window has no matching referenced
record.

> [!INFORMATIVE]
> Evaluating the metric condition once per batch (using the batch's latest timestamp) rather than once per event is an optimisation that produces identical results at typical metric sample intervals (15 seconds). The batch commit interval (default 100ms) is far shorter than the metric sample interval, so all events in a batch map to the same metric sample. At abnormally high metric resolutions (sub-second sampling), this optimisation can produce slightly coarser filtering than per-event evaluation -- events near a metric threshold crossing may be included or excluded as a group rather than individually.

## Filter restrictions

During the streaming phase, access control, the primary selector, the `SINCE`
lower bound, and WHERE predicates (including cross-type conditions) are evaluated
against new records. For raw-record streams, SORT, TAKE, and SKIP do not apply to
streamed records -- they apply only to the initial raw-record result set.
Streamed raw records are delivered in commit order. For DISTINCT streams, newly
seen distinct values are emitted in the commit order of the records that first
introduced them after the initial result set.

SELECT applies to streamed raw records -- only the specified fields are
included. SELECT is invalid for DISTINCT streams.
