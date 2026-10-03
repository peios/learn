---
title: Accounting and Limits
description: What every query records for the adaptive indexer, and the concurrency, memory and timeout limits it runs under.
---

## Recording what was asked

Every event query is recorded by the adaptive indexing system (§3.4).
[*account.every-event-query-is-recorded-by-the-adaptive-indexer]
For each `WHERE` predicate:

- a header column reference increments that column's frequency counter
  [*account.a-header-column-predicate-increments-that-columns-counter]
- a payload field reference increments that path's counter
  [*account.a-payload-field-predicate-increments-that-paths-counter]

Cross-type `WHERE` predicates are counted like any other, since they
narrow the same data by the same fields.
[*account.cross-type-where-predicates-are-counted-like-any-other]

This applies to **event queries only**. The log and metric stores have
fixed write-time indexes and no candidate space for a policy to explore
(§4.2, §5.2), so their queries increment nothing.
[*account.log-and-metric-queries-increment-no-counters]

Counters are in-memory and are flushed to the metadata database at each
policy interval (§3.5).
[*account.counters-are-flushed-to-the-metadata-database-each-policy-interval]
Query handlers never write to that database directly, which is what
keeps the once-per-query update off any lock a writer thread contends
for. [*account.query-handlers-never-write-the-metadata-database-directly]

## Concurrency

eventd bounds concurrent queries — streaming and non-streaming together
— at `MaxConcurrentQueries` (§A).
[*account.max-concurrent-queries-bounds-streaming-and-non-streaming-queries-together]
Beyond it a query is rejected with an error rather than queued.
[*account.a-query-over-the-concurrency-limit-is-rejected-not-queued]

The per-query cost that limit is protecting is real: read-only SQLite
connections, one per shard for an event query (§6.4), memory for the
merge, and CPU for execution and payload decoding.

`MaxStreamingQueries` is enforced separately and is lower.
[*account.max-streaming-queries-is-a-separate-lower-limit] A streaming
query holds its resources for as long as its client stays connected,
where an ordinary one holds them for at most a timeout, so the two
populations need different bounds.

Both are global rather than per-caller.
[*account.both-query-limits-are-global-not-per-caller] eventd cannot
attribute connections to a caller beyond the token it holds, so one
client can occupy every slot — and the interim protection is that
queries and ingestion are separate channels, so exhausting the query
side cannot exhaust ingestion (PSPU §3.3).
[*account.exhausting-the-query-slots-cannot-exhaust-ingestion]

> [!NOTE]
> Per-caller limits would need a way to identify the connecting process
> beyond its token — a process GUID from the connection. That is the same
> class of missing primitive as the datagram peer identity that leaves
> `origin` unverifiable (PSPU §3.28), and the global limit is what stands
> in for it.

## Memory

eventd may not be killed: it runs with `oom_score_adj` −1000, so if its
memory alone fills the machine, the kernel has nothing left to reclaim
and panics. What bounds a query's memory therefore has to hold however
many queries run at once.

A query in the default order holds one row per shard and nothing more
(§6.4), and is never refused for the size of its result (PSPU §3.16).
[*account.a-default-order-query-is-never-refused-for-its-size]

Everything else a query must hold — a sorted query's rows, an
aggregation's groups, a watch batch — counts against
`MaxQueryHeldBytes` (§A), **one budget for every running query
together**.
[*account.max-query-held-bytes-bounds-what-all-running-queries-hold-together]
A query takes from it in 64 KiB granules as it grows, gives back what
it no longer needs when a sorted query trims, and gives back all of it
when it ends.
[*account.held-memory-is-reserved-in-granules-and-given-back]
A query that would take more than is left fails with an error, rather
than being truncated or answered from part of the data.
[*account.a-query-past-the-held-budget-fails-with-an-error]

What a row or group costs is estimated from its fields and values, not
measured from the allocator, so the budget is approximate. It is still a
bound: with the default of 256 MiB, no number of concurrent queries
holds much more than that.

Metric queries are not yet counted against it: they gather the samples
of a range before transforming and aggregating them, and holding them
within the budget waits for windows to fold as samples are read.

## Request and response sizes

eventd rejects an inbound frame above `MaxQueryRequestBytes` before
allocating or reading its payload.
[*account.a-request-frame-over-max-query-request-bytes-is-rejected-before-reading]
Outbound result records are grouped at record boundaries toward
`QueryResponseTargetBytes` (§A).
[*account.result-records-are-grouped-at-record-boundaries-toward-the-response-target]
The target is not a limit: a complete record that exceeds it is sent
alone, never split, truncated, skipped or failed merely for exceeding
the target (PSPU §3.15–§3.16).
[*account.a-record-over-the-response-target-is-sent-alone-and-whole]
Only the protocol's `u32` frame length is a hard outbound bound.
[*account.the-u32-frame-length-is-the-only-hard-outbound-bound]

## Timeouts

Every query has a maximum execution time, `QueryTimeoutMs` (§A).
[*account.every-query-is-bounded-by-query-timeout-ms]

The clock starts once the request has been decoded and the caller's
token obtained, and covers everything after: parsing, planning, access
checks, cross-type pre-computation, SQL execution, merging, aggregation,
pagination, projection, and transmitting the initial result set.
[*account.the-timeout-starts-after-decoding-and-token-acquisition-and-covers-the-rest]

It bounds the **initial result set only**. A non-streaming query sends
`end` before it expires; a streaming query sends `watch`.
[*account.the-timeout-bounds-only-the-initial-result-set] Past `watch`
the stream is not time-limited, and what bounds it instead is
`MaxStreamingQueries`, `MaxDistinctStreamValues` and backpressure
(§6.6). [*account.a-stream-past-watch-is-not-time-limited]

On expiry eventd cancels the query and sends an error.
[*account.on-expiry-the-query-is-cancelled-and-an-error-is-sent] Any result
messages already sent are discarded by the client, since no terminal
message arrived (PSPU §3.16).

Cancellation has to reach two kinds of work. SQLite work is interrupted
through `sqlite3_interrupt` or an equivalent progress-handler check —
the same responsiveness problem as cancelling an index build (§3.4).
[*account.cancellation-interrupts-in-progress-sqlite-work]
Non-SQL work — MessagePack flattening, the cross-shard merge — checks
the same deadline periodically, because a query can spend most of its
time in neither the database nor the kernel.
[*account.non-sql-query-work-checks-the-deadline-periodically]

Large scans over unindexed fields are the main timeout risk, and the
adaptive indexing system reduces it over time by indexing whatever keeps
being filtered on — which is also why a timeout is a signal worth
watching rather than merely an error to retry.
