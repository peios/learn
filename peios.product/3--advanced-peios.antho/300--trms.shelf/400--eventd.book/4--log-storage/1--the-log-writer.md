---
title: The Log Writer
description: One thread reads the log socket and writes the store, independent of the event path — batching, durability and what it adds to a record.
---

One thread reads datagrams from the log socket and writes log records to
the log store. It is independent of the event drain and writer threads,
so log ingestion never contends with event ingestion.

The wire contract — socket type, datagram ceiling, record format, and
exactly which malformations cost what — is PSPU §3.6 to §3.8. What
follows is what eventd does with a record once it has one.

## One thread does both jobs

The log thread performs both the socket reads and the SQLite writes.

The consequence is direct: **during a batch commit the socket is not
being drained**, and datagrams arriving in that window occupy the
receive queue until it fills, after which the kernel discards them. The
queue — `SO_RCVBUF` — is sized at four times the datagram ceiling, and it
is the whole cushion.

> [!NOTE]
> Linux's default `SO_RCVBUF` for a Unix datagram socket is around
> 212 KB, roughly a thousand typical log records. A batch commit takes
> one to ten milliseconds, and that buffer is the only thing absorbing
> arrivals in the window. A service dumping a stack trace will lose
> datagrams, which is the intended degradation for a loss-tolerant path
> (PSPU §3.4) — the alternatives being backpressure or unbounded
> buffering, and the design forbids both.

Splitting into a reader and a writer with a bounded handoff — the shape
the event path uses (§2.3) — would decouple them. It is not done, and
the reasoning is that log loss is tolerable by design (PSPU §3.4), log
volume is normally well below event volume, and the single-thread model
avoids a handoff channel and its backpressure semantics entirely.

Where log throughput does become the constraint, sharding the log store
the way the event store is sharded is the larger lever; splitting the
thread only moves the stall.

## Batching

The writer batches on the same adaptive principle as the event writer
(§2.4), with the socket receive queue as its input. A transaction opens
when the first valid record is available and commits when any of these
holds:

- no further datagram is immediately available in the receive queue
- the batch holds `LogMaxBatchSize` records
- `LogMaxBatchLatencyMs` has elapsed since the first record entered it

If a datagram yields more valid records than fit in the remaining space,
the writer commits, then continues with the same datagram in a new
transaction. A transaction never exceeds the size cap and never stays
open past the latency cap — a batched datagram cannot smuggle a larger
transaction past either.

The defaults (§A) are 5000 records and 500 milliseconds. The latency is
five times the event writer's, because log loss on power failure is
acceptable where event loss is not, and larger, less frequent
transactions are more efficient at the moderate volumes logs normally
run at.

## Durability

The log store runs in WAL mode with `synchronous=NORMAL`, not FULL.

NORMAL syncs at checkpoint time rather than at every commit. It is
durable against process crashes — the write-ahead log survives — but not
against power loss, where commits since the last checkpoint may be gone.

This is a deliberate divergence from the event store, and it is the
single clearest expression of the hierarchy the whole daemon is
organised around: events are sacred, logs are not. Paying an fsync per
transaction to protect data whose loss is defined as acceptable would be
paying for nothing.

## Adding to the record

eventd supplies the `boot_id` and, where the producer omitted
`timestamp`, its own clock at receipt. Everything else is stored as
given — `message` byte for byte (PSPU §3.8).
