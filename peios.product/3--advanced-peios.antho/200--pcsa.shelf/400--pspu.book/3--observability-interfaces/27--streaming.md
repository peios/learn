---
title: Streaming
description: STREAM turns a query into a live watch — what may be streamed, what still applies during the watch phase, and what is rejected.
---

`STREAM` turns a query into a live tail. It is a flag, may appear
anywhere in the string, and takes no argument.

Streaming is available for **event and log queries only**. A collector
MUST reject `STREAM` in metric mode.

> [!NOTE]
> Metric streaming is absent because metric data is sampled on an
> interval — typically fifteen seconds — and the consumer is a dashboard
> that polls. Streaming individual samples adds a delivery path with a
> latency budget far finer than the data it carries.

## The shape of a streaming query

1. The collector executes the query normally and sends the initial
   result set as `"ok"` messages.
2. It sends `"watch"` (§3.16). The query is established at this point
   and not before.
3. It stays open. As records are committed, it evaluates them against
   the query and sends those that match.
4. It continues until the client disconnects, an error terminates it, or
   the collector shuts down.

There is no `"end"` message for a streaming query, ever.

## What may be streamed

Raw record queries and `DISTINCT` queries. A collector MUST reject
`STREAM` combined with `COUNT BY`, `TOP N BY` or `GROUP` as a parse
error — those produce one answer about a set, and a set that is still
growing has no answer yet.

A collector MUST reject `STREAM` combined with `UNTIL`. An upper time
bound and an unbounded live tail are contradictory requests.

`SINCE` is permitted and applies to both phases, resolved against the
evaluation time captured at query start (§3.19).

## What still applies during the watch phase

Access control, the primary selector, the `SINCE` bound and every
`WHERE` predicate — cross-type conditions included — are evaluated
against each new record.

`SORT`, `TAKE` and `SKIP` apply to the **initial result set only**.
Streamed records are delivered in commit order and a collector MUST NOT
reorder, limit or skip them: there is no total order over records that
have not arrived, and applying `TAKE` to a stream would silently end it.

`SELECT` applies to streamed records as it does to initial ones.

## DISTINCT streaming

```text
EVENTS kacs.* DISTINCT process_guid STREAM
LOGS DISTINCT origin STREAM
```

A `DISTINCT` stream emits a value the first time it is seen, and never
again. The output schema is `DISTINCT`'s fixed one (§3.23) in both
phases.

The initial result set is the complete distinct set visible at query
start, after access control and every filter. The collector then holds a
**seen set** initialised from it. Each newly committed record that
passes access control and the filters is reduced to its value for the
field, and emitted only if that value is not already in the seen set
under the grouping equality of §3.21; emitted values are then added.

A collector MUST bound the seen set.

> [!NOTE]
> §3.A gives the mainline value and adjustable range
> for this bound and every other in this chapter.

If initialising the set or inserting a value would exceed the bound, the
collector MUST terminate the query with an error. It MUST NOT evict:
"not seen before" is the entire meaning of the output, and a set that
forgets would re-emit values it had already reported, which is worse
than stopping.

A collector MUST reject `DISTINCT … STREAM` combined with `SORT`, `TAKE`
or `SKIP`, so that the seen set always corresponds to the complete
initial visible set. `SELECT` is already invalid with `DISTINCT`
(§3.22).

## Cross-type conditions during the watch phase

The pre-computed time ranges of §3.26 describe the past. A collector
MUST NOT reuse them for streamed records.

For a **metric** condition, the selector has already been required to
resolve to exactly one series (§3.26). For each committed batch, the
collector finds that series' active sample at the batch's latest
candidate timestamp under §3.26's interval rules and evaluates the
condition against it. If no sample is active there, the condition is
false. A false condition filters out the whole batch; a true one leaves
the batch to be filtered by the remaining predicates as usual.

For an **existence** condition, the collector applies §3.26's centred
window to each candidate record's own timestamp. These are evaluated
**per record**, not per batch, because a matching record may be near
some of a batch and not the rest.

> [!NOTE]
> Evaluating the metric condition once per batch rather than once per
> record is an approximation, and an intentional one. A commit batch
> spans a fraction of a second while a metric sample spans fifteen, so
> every record in a batch normally maps to the same sample. At
> sub-second metric resolution it filters more coarsely than per-record
> evaluation would, and records near a threshold crossing are included or
> excluded as a group.

## Backpressure

If a client cannot keep up, the collector MUST drop the query rather
than buffer for it.

Backpressure is detected on the socket send buffer: when a result
message cannot be sent because the buffer is full, the collector MUST
terminate the query immediately and MUST NOT block on the send. It sends
an error if the socket will still take one, and closes otherwise.

Streaming MUST NOT slow or block ingestion. A streaming client is the
lowest-priority consumer of a collector's time, and a slow one is
disconnected rather than accommodated — the same principle as §3.4,
applied on the way out.

## Latency

Delivery latency is bounded below by the collector's commit interval for
the store concerned, because a record is only streamable once it is
committed. A client that needs lower latency than that is not served by
this interface: the KMES ring buffer is the lower-latency path and is
specified in PSPK.

> [!NOTE]
> Streaming is a convenience for interactive tailing and dashboards.
> Where results must be predictable — cross-type conditions evaluated per
> batch, a metric threshold sampled coarsely, a disconnect under load —
> repeated non-streaming queries with a sliding `SINCE` are more
> reliable, and for latency-critical consumption the ring buffer bypasses
> a collector entirely.
