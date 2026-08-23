---
title: Accounting and Limits
description: What every query records for the adaptive indexer, and the concurrency and timeout limits it runs under.
---

## Recording what was asked

Every event query is recorded by the adaptive indexing system (§3.4).
For each `WHERE` predicate:

- a header column reference increments that column's frequency counter
- a payload field reference increments that path's counter

Cross-type `WHERE` predicates are counted like any other, since they
narrow the same data by the same fields.

This applies to **event queries only**. The log and metric stores have
fixed write-time indexes and no candidate space for a policy to explore
(§4.2, §5.2), so their queries increment nothing.

Counters are in-memory and are flushed to the metadata database at each
policy interval (§3.5). Query handlers never write to that database
directly, which is what keeps the once-per-query update off any lock a
writer thread contends for.

Metric queries feed the parallel rollup registry counters instead
(§5.6), which record `(function, window)` pairs rather than fields.

## Concurrency

eventd bounds concurrent queries — streaming and non-streaming together
— at `MaxConcurrentQueries` (§A). Beyond it a query is rejected with an
error rather than queued.

The per-query cost that limit is protecting is real: read-only SQLite
connections, one per shard for an event query (§6.4), memory for the
merge, and CPU for execution and payload decoding.

`MaxStreamingQueries` is enforced separately and is lower. A streaming
query holds its resources for as long as its client stays connected,
where an ordinary one holds them for at most a timeout, so the two
populations need different bounds.

Both are global rather than per-caller. eventd cannot attribute
connections to a caller beyond the token it holds, so one client can
occupy every slot — and the interim protection is that queries and
ingestion are separate channels, so exhausting the query side cannot
exhaust ingestion (PSPU §3.3).

> [!NOTE]
> Per-caller limits would need a way to identify the connecting process
> beyond its token — a process GUID from the connection. That is the same
> class of missing primitive as the datagram peer identity that leaves
> `origin` unverifiable (PSPU §3.28), and the global limit is what stands
> in for it.

## Timeouts

Every query has a maximum execution time, `QueryTimeoutMs` (§A).

The clock starts once the request has been decoded and the caller's
token obtained, and covers everything after: parsing, planning, access
checks, cross-type pre-computation, SQL execution, merging, aggregation,
pagination, projection, and transmitting the initial result set.

It bounds the **initial result set only**. A non-streaming query sends
`end` before it expires; a streaming query sends `watch`. Past `watch`
the stream is not time-limited, and what bounds it instead is
`MaxStreamingQueries`, `MaxDistinctStreamValues` and backpressure
(§6.6).

On expiry eventd cancels the query and sends an error. Any result
messages already sent are discarded by the client, since no terminal
message arrived (PSPU §3.16).

Cancellation has to reach two kinds of work. SQLite work is interrupted
through `sqlite3_interrupt` or an equivalent progress-handler check —
the same responsiveness problem as cancelling an index build (§3.4).
Non-SQL work — MessagePack flattening, the cross-shard merge — checks
the same deadline periodically, because a query can spend most of its
time in neither the database nor the kernel.

Large scans over unindexed fields are the main timeout risk, and the
adaptive indexing system reduces it over time by indexing whatever keeps
being filtered on — which is also why a timeout is a signal worth
watching rather than merely an error to retry.
