---
title: The Streaming Machinery
description: How a live watch is implemented — commit generations, latency, the DISTINCT seen set, cross-type re-evaluation and backpressure.
---

The externally visible behaviour of a streaming query — what may be
streamed, what applies during the watch phase, how `DISTINCT` streams
behave, and when a slow client is dropped — is PSPU §3.27. This is the
machinery underneath.

## Commit generations

eventd keeps a monotonic `u64` commit generation counter for each
streamable store: one for the event store **as a whole**, and one for
the log store. Metric queries do not stream, so the metric store has
none.

After a writer commits a batch it increments the counter for its store
and wakes the streaming handlers waiting on it. A handler records the
last generation it processed and waits until the counter exceeds it.

The event counter covers the whole store rather than one per shard.
Several writer threads increment it, so a wake is "something committed
somewhere" and a handler re-examines every shard it cares about — which
is what it would have to do anyway, since a shard means nothing to the
query path (§6.4).

The counter is process-local and never persisted; it has no meaning
across a restart, and a streaming query does not survive one. On
wraparound the next increment is treated as a wake for every handler and
operation continues. At any commit rate a machine can sustain,
wraparound of a 64-bit counter is not reachable.

## Latency

Delivery latency is bounded below by the commit interval of the store
concerned, because a record is not streamable until it is committed.

| Store | Approximate floor | From |
|---|---|---|
| Events | `MaxBatchLatencyMs`, default 100 ms | §2.4 |
| Logs | `LogMaxBatchLatencyMs`, default 500 ms | §4.1 |

Under light load the actual latency is lower, because the adaptive
batcher commits as soon as its input drains rather than waiting out the
cap (§2.4). Under sustained load it converges on the cap.

A consumer needing better than this is not served by eventd at all: the
KMES ring buffers are the low-latency path, they are specified in PSPK,
and attaching to them directly costs the per-event access control that
eventd exists to apply (§7).

## The DISTINCT seen set

A `DISTINCT` stream holds a per-query set of the values it has already
emitted, initialised from the initial result set and added to as new
values appear (PSPU §3.27).

It is bounded by `MaxDistinctStreamValues` (§A), and exceeding the bound
terminates the query with an error rather than evicting. Eviction would
make the output wrong rather than merely truncated: a forgotten value
would be re-emitted as newly seen, and "newly seen" is the entire
meaning of the result.

The set is per query and in memory, which is why the bound exists and
why it is separate from the general query concurrency limit — sixty-four
streams each holding a hundred thousand values is a different memory
profile from sixty-four ordinary queries.

## Cross-type re-evaluation

Pre-computed cross-type ranges describe the past and are discarded when
the watch phase begins (PSPU §3.27).

A **metric** condition costs one index seek per batch: the selector has
already been constrained to exactly one series, so finding the active
sample at the batch's latest candidate timestamp is a single lookup on
`idx_samples_series_timestamp` (§5.2).

An **existence** condition is evaluated per candidate record rather than
per batch, because the centred window is relative to each record's own
timestamp and a matching record may be near some of a batch and not the
rest.

The per-batch metric evaluation is an approximation, and the reason it
is acceptable is the ratio between the two intervals: a commit batch
spans a fraction of a second and a metric sample fifteen, so every
record in a batch normally maps to the same sample. At sub-second metric
resolution it filters more coarsely, and records near a threshold
crossing are included or excluded as a group.

## Backpressure

Backpressure is detected on the socket send buffer. When a result
message cannot be sent because the buffer is full, the query is
terminated immediately; eventd never blocks on the send.

Blocking would put a slow reader in the path of eventd's own work, and
the write path is what would suffer. A streaming client is the
lowest-priority consumer of eventd's time, and dropping it is the same
principle as dropping an ingestion datagram (PSPU §3.4), applied on the
way out.
