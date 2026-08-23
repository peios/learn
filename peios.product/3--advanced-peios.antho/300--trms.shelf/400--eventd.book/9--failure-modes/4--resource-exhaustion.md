---
title: Resource Exhaustion
description: Memory, query slots, descriptors and writer stalls — how each runs out, and what eventd does when it does.
---

## Memory

If the out-of-memory killer takes eventd, it is treated exactly as a
crash (§8.5): the databases are consistent, the ring buffers are
untouched, peinit restarts the daemon, and the gap is recorded.

Three things bound eventd's memory, and each is worth knowing because
each has a configuration that governs it:

| Consumer | Proportional to | Bounded by |
|---|---|---|
| Series cache | distinct metric series held in memory | `MetricSeriesCacheSize` (§5.3) |
| Index and rollup counters | distinct fields and function-window pairs queried | the query surface itself |
| SQLite page caches | connections and active indexes | per-connection configuration (§C) |

The handoff channels are deliberately not on that list. They are bounded
by the batch size (§2.3), which is the entire point of the
ring-buffers-are-the-only-buffer rule: the thing that would otherwise
grow without limit under load is the thing that is fixed.

The consumer most likely to surprise is the series cache under a
high-cardinality producer — not because the cache grows, since it is
bounded, but because the `series` table does, and the cache then
thrashes on the thread that also drains the metric socket (§5.3).

## Query slots

Reaching `MaxConcurrentQueries` or `MaxStreamingQueries` rejects new
queries with an error rather than queueing them (§6.5). Both bounds are
global, so one client can occupy every slot.

Ingestion is unaffected, because queries and ingestion are separate
channels and separate threads. That separation is what makes query-side
exhaustion an inconvenience rather than data loss.

## Descriptors

An event query opens a read-only connection per shard database, and each
connection holds one or two file descriptors (§6.4). Many historical
shards multiplied by many concurrent queries reaches a process limit
faster than anything else eventd does.

Where eventd cannot allocate what an admitted query needs, it fails that
query rather than blocking a writer or exceeding its own limit (§6.1).

## Writer stalls

Two things stall a writer thread briefly, and both are bounded by
design.

**An index build in progress.** Drain threads detect rising write
pressure and signal cancellation; the writer aborts the `CREATE INDEX`,
SQLite rolls back the partial index, and event writing resumes
immediately (§3.4).

**Retention holding a write lock.** The shard's writer blocks until
retention releases it. Retention works in small bounded batches and
releases the coordination primitive between them, and under sustained
write pressure it delays the next batch long enough for a waiting writer
to make progress (§3.6). Events accumulate in the ring buffer during the
stall, which is the ordinary absorption path.

Neither stall loses anything by itself. Both contribute to ring buffer
pressure, and prolonged enough, both end at §9.1.
