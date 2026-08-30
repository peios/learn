---
title: Overview
description: eventd is the single persistent sink for everything a Peios system records about itself — the shape of the daemon, and what it is not.
---

eventd is the observability daemon: the single persistent sink for
everything a Peios system records about itself. Events, logs and metrics
all end in eventd, and every query for any of them is answered by it.

It is one of the platform daemons the service manager starts at boot,
signed at TCB level, and it is Critical — a system that loses it loses
its audit trail.

The three data types are genuinely different and eventd treats them
differently at every layer.

**Events** are structured, typed records carrying identity stamps the
kernel applied and an emitter could not influence. They arrive through
KMES, in per-CPU shared-memory ring buffers, and eventd is their primary
consumer. They are the audit and security telemetry, and losing one is a
real failure — so the event path is the one with sequence numbers, gap
detection, per-transaction durability, and a synthetic record written
whenever anything is lost.

**Logs** are text: a line a program wrote, with light metadata attached.
They arrive on a datagram socket, mostly from the service manager
forwarding what it read from a service's standard output and standard
error. Losing one is an inconvenience, and the ingestion path is
designed around that tolerance rather than against it.

**Metrics** are numeric measurements over time — dense series rather
than discrete occurrences. They arrive on a second datagram socket,
pushed by whatever is doing the measuring. eventd is a sink, not a
collector: it scrapes nothing and polls nothing.

## The shape of the daemon

Three ingestion paths, three storage engines, one query surface.

The event path runs one drain thread per CPU, each attached to one ring
buffer, handing events over a bounded channel to a writer thread that
batches them into a SQLite shard. Shards are independent — separate
files, separate write-ahead logs, separate writer threads, no shared
write-path state — so write throughput scales with the shard count
(§2.3).

The log and metric paths each run a single thread that reads datagrams
and writes them, to one database each. Neither contends with the event
path.

Underneath all three sits a decision that shapes the event pipeline
entirely: **the KMES ring buffers are the only buffer.** eventd holds no
large intermediate queue. Events move from the ring buffer through a
small bounded handoff straight into a transaction, and when the writer
falls behind, backpressure propagates backwards until the ring buffer
absorbs it — and when the ring buffer cannot, the loss is detected and
recorded rather than hidden (§2.5).

Adaptive indexing watches which fields event queries filter on and
maintains indexes for them, shedding those indexes under write pressure
because ingestion throughput outranks query latency (§3.4). Metric
queries read raw samples in v0.23; adaptive rollups are deferred until a
later schema can prove cached aggregates current (§5.6).

Everything eventd holds is readable only through access checks that KACS
performs, per event type, per log origin, per metric name, and per field
within a record (§7).

## What eventd is not

**It is not a log framework.** eventd stores lines; it does not parse
them, does not understand severity beyond a single error flag, and does
not care whether the text happens to be JSON.

**It is not a metric collector.** Nothing in eventd reads `/proc`,
scrapes an endpoint, or polls a service. Something else measures and
pushes.

**It is not a tracing system.** Distributed tracing is out of scope
entirely.

**It is not the low-latency path to events.** A consumer that needs
events in microseconds attaches to the KMES ring buffers directly, as
`revstrm` does. eventd sits above that transport, adds persistence and
access control, and costs a batch commit interval in latency.

**It is not the only KMES consumer**, and holds no privileged position
among them.
