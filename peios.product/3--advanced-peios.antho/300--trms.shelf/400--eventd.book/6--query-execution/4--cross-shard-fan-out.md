---
title: Cross-Shard Fan-Out
description: Event queries run against every database in the store, active and historical — how results merge, and the unbounded case.
---

Event queries execute against **every** database in the event store
directory — active shards and historical ones alike (§3.3). Log and
metric queries touch one database each and need none of this.

Shards carry no meaning for the query path (§2.3). A shard holds
whatever CPUs routed to it during whatever lifetimes wrote it, so there
is no shard a query can skip on the basis of its contents, and a
predicate on `cpu_id` scans all of them.

## Merging

How results combine depends on the query.

**Non-aggregating queries.** Each shard produces rows sorted by the
effective sort key, tiebreakers included (§6.2), and the coordinator
performs an N-way merge of the sorted streams.

With `TAKE` present, each shard returns at most `SKIP + TAKE` rows — or
`TAKE` rows when there is no `SKIP` — and the coordinator applies
`SKIP` and `TAKE` after merging. The total read is therefore at most
`(SKIP + TAKE) × shard_count`, which is the price of not knowing in
advance which shard holds the winning rows.

With `TAKE` absent, each shard streams every matching row until the
query completes or times out.

**Aggregating queries.** Each shard computes a partial aggregate and the
coordinator combines them:

| Query | Shard returns | Coordinator does |
|---|---|---|
| `COUNT` | its local count | sums |
| `COUNT BY`, `TOP N BY`, `GROUP … COUNT` | per-group counts | sums per group key, sorts by count descending, applies `TAKE` |
| `GROUP … SUM` | per-group sums | sums per group |
| `GROUP … AVG` | per-group **sum and count** | computes the average from the combined pair |
| `GROUP … MIN` / `MAX` | per-group min or max | takes the min or max |
| `DISTINCT` | local distinct values | unions |

`AVG` is the one that cannot be composed from its own output. Averaging
per-shard averages weights each shard equally regardless of how many
rows it held, so a shard is asked for the sum and the count and the
coordinator divides once — the same reasoning that makes rollup
composition carry `sample_count` (§5.6).

Pushing aggregation down bounds the coordinator's memory to the group
key cardinality times the shard count, rather than to the total row
count.

## The unbounded case

A non-aggregating query without `TAKE` has no implicit row limit.
`EVENTS SINCE 7d ago` may match millions of rows, all of which pass
through the merge.

The query timeout is the only backstop (§6.5). Streaming merged results
to the client incrementally, rather than materialising the whole set
before sending, is what keeps the memory cost proportional to the merge
frontier instead of to the result.

## Descriptors

An event query opens a read-only connection per database, and each
SQLite connection holds one or two descriptors for the database and its
write-ahead log. With many historical shards this adds up quickly across
concurrent queries.

Active shard writer connections stay open for the process lifetime and
are not negotiable. Historical shard read connections are the pool worth
bounding — opened when a query touches them, closed after a period of
inactivity (§C).
