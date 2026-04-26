---
title: Recommended Implementation Optimisations
---

The following optimisations are not normative. They do not affect the storage format, wire protocol, query language, or any observable behavior. An implementation that omits all of them is fully conformant. However, each one provides measurable throughput or latency improvement with no behavioural trade-offs, and implementers are encouraged to adopt them.

## Arena allocation for event copies

Drain threads copy events from the KMES ring buffer into process-local memory at rates up to hundreds of thousands of events per second. Using the system allocator (`malloc`/`Box::new`) for each variable-sized event creates allocator pressure: freelist bookkeeping, potential lock contention in multi-threaded allocators, and occasional page faults when the allocator requests new pages from the OS.

Implementations SHOULD use a per-drain-cycle arena allocator (e.g., `bumpalo` in Rust). Pre-allocate a block of memory at the start of each drain cycle, hand out sequential chunks for each event copy (a pointer bump, no bookkeeping), and free the entire block after the batch is handed off to the writer thread. This reduces per-event allocation cost from ~20-50ns to ~1-2ns and eliminates allocation-related latency spikes.

## Consumer thread affinity

Drain threads that read from per-CPU ring buffers benefit from being pinned to the same NUMA node as the CPU whose buffer they read. While not strictly necessary (the per-CPU design eliminates write contention regardless of consumer placement), NUMA-local reads avoid cross-node memory traffic during the drain loop.

For the 1:1 case (one shard per CPU), pinning the drain thread to the same CPU as its ring buffer gives optimal cache locality: the ring buffer pages are likely already in that CPU's L3 cache from the kernel write.

## Partial msgpack extraction for query results

When constructing flat-map query results from event records, implementations SHOULD use partial/lazy msgpack extraction rather than decoding the entire payload. When a SELECT clause names specific payload fields, only those fields need to be extracted. A streaming msgpack decoder that scans for specific keys and skips unneeded values avoids the cost of building a full in-memory representation of the payload.

For payloads with many fields where only one or two are selected, partial extraction reduces per-row CPU cost by an order of magnitude.

## Prepared statement pooling

Writer threads use one prepared INSERT statement each (§2.4). Query handlers executing translated SQL SHOULD maintain a pool of prepared statements for common query patterns. SQLite prepared statements cache the query plan; re-preparing the same SQL on every query wastes CPU on parsing and planning.

A small LRU pool of ~50-100 prepared statements per read connection covers the common case where operators repeat similar queries.

## Batch socket reads for logs and metrics

The log and metric ingestion threads read datagrams from Unix sockets. The `recvmmsg` syscall reads multiple datagrams in a single kernel round-trip, reducing per-message syscall overhead. On Linux, `recvmmsg` can read up to `vlen` messages at once (typically up to 1024).

Under sustained log or metric load, `recvmmsg` with a batch size of 64-256 messages reduces syscall overhead by the same factor, improving ingestion throughput without any protocol or format changes.

## SQLite page cache tuning

Each SQLite connection has a page cache (default ~2MB). For event shard writer connections, the page cache holds B-tree pages for the events table and its indexes. Under sustained writes with adaptive indexes, the working set of hot pages can exceed the default cache size, causing frequent page evictions and re-reads.

Implementations SHOULD tune the page cache size per connection based on the number of active indexes. A reasonable heuristic: 2MB base + 1MB per active secondary index. For read-only query connections, a smaller cache (512KB-1MB) is sufficient since queries are typically short-lived.

## Shard file descriptor management

With many active and historical shard databases, the number of open file descriptors can be significant (each SQLite connection opens 1-2 fds for the database and WAL). For the query path, which opens read-only connections to every database in the event store directory, implementations SHOULD use a connection pool with a bounded number of open connections, opening and closing historical shard connections on demand rather than holding them all open permanently.

Active shard writer connections MUST remain open for the lifetime of the process. Historical shard read connections can be opened lazily when a query touches them and closed after a period of inactivity.
