---
title: Recommended Optimisations
description: Implementation techniques that affect no storage format, protocol or observable behaviour, offered as guidance rather than requirement.
---

None of the following affects the storage format, the wire protocol, the
query language, or any behaviour a client can observe. An
implementation omitting all of them is complete. Each buys measurable
throughput or latency with no behavioural trade-off, which is why they
are collected here rather than described as design.

## Arena allocation for event copies

Drain threads copy events out of the ring buffer at rates reaching
hundreds of thousands per second (§2.2). Using the system allocator for
each variable-sized copy costs freelist bookkeeping, potential lock
contention in a multi-threaded allocator, and occasional page faults
when it asks the kernel for more.

A per-drain-cycle arena avoids all of it: allocate a block at the start
of the cycle, hand out sequential chunks by bumping a pointer, and
release the whole block once the batch has been handed off. Per-event
allocation cost falls from tens of nanoseconds to one or two, and the
latency spikes disappear with it.

## Drain thread affinity

A drain thread reading a per-CPU ring buffer benefits from running on
the same NUMA node as that CPU. It is not necessary — the per-CPU design
eliminates write contention regardless of where the consumer runs — but
NUMA-local reads avoid cross-node traffic in the drain loop.

In the 1:1 case, pinning the drain thread to the CPU whose buffer it
reads gives the best cache locality available: the pages are likely
still in that CPU's L3 from the kernel's write.

## Partial payload extraction

Building flat result records means decoding payloads, and at thousands
of rows that is the dominant query cost (§6.1).

Where a `SELECT` names specific payload paths, only those need
extracting. A streaming MessagePack decoder that scans for the wanted
keys and skips over everything else avoids materialising the payload at
all, and for a payload with many fields where one or two are selected
this cuts per-row CPU by an order of magnitude.

Without a `SELECT`, a streaming decoder emitting flattened key-value
pairs still avoids building a full in-memory representation.

## Prepared statement pooling

Writer threads already prepare one `INSERT` each and reuse it (§2.4).
Query handlers executing translated SQL benefit from the same treatment:
a small LRU pool of prepared statements per read connection, on the
order of fifty to a hundred, covers the case where an operator repeats
similar queries and where a dashboard issues the same query on a timer.

SQLite caches the query plan in a prepared statement, so re-preparing
identical SQL spends CPU on parsing and planning that was already done.

## Batched socket reads

The log and metric ingestion threads read datagrams one at a time by
default. `recvmmsg` reads many in one kernel round trip — up to a
thousand or so — and at a batch of 64 to 256 it cuts syscall overhead by
that factor under sustained load, with no protocol or format change.

It also shortens the window in which the thread is not draining the
socket, which is the window that loses datagrams (§4.1).

## SQLite page cache tuning

Each connection has a page cache, around 2 MB by default. For a shard
writer connection it holds B-tree pages for the events table and its
indexes, and under sustained writes with several adaptive indexes the
hot working set can exceed the default — producing evictions and
re-reads on the write path.

A reasonable heuristic is 2 MB plus 1 MB per active secondary index for
a writer connection, and 512 KB to 1 MB for a read-only query
connection, whose queries are short-lived.

## Bounded shard connection pool

The query path opens a read-only connection to every database in the
event store directory, and each holds one or two descriptors (§6.4).
With many historical shards this becomes the binding resource.

Active shard writer connections stay open for the process lifetime and
are not candidates. Historical shard read connections are: opening them
lazily when a query touches them, and closing them after a period of
inactivity, bounds the descriptor count without affecting any result.
