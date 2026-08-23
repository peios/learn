---
title: Losing Events
description: The one failure that costs something unrecoverable, and why the whole ingestion pipeline is shaped around delaying it.
---

Every other failure in this chapter costs something recoverable. This
one does not, which is why the whole ingestion pipeline is shaped around
delaying it.

## Ring buffer overrun

When events are emitted faster than eventd drains them, the per-CPU ring
buffers fill and KMES overwrites its oldest entries.

- eventd sees it as a sequence gap on the affected CPU (§2.5).
- A `synthetic.gap` record is written, naming the missing range.
- Draining resumes from the oldest survivor at `tail_pos`.

The events are gone. No other copy exists, and a gap record is a
tombstone rather than a recovery — it records what was lost and when,
which is the most that can be offered.

Four mechanisms delay it:

| Mechanism | Effect |
|---|---|
| Adaptive batch sizing (§2.4) | Commits as often as throughput allows, so the writer stays close to the drain rate. |
| Index shedding (§3.4) | Drops per-insert index cost under pressure, including all of it at once in the emergency case. |
| Sharding (§2.3) | Scales write throughput with the shard count. |
| Ring buffer capacity | The absorption window, sized by an administrator. |

The first three are eventd's and operate automatically. The fourth is
KMES's and is the one an operator can enlarge for a workload that bursts
predictably.

## Query timeouts

A query exceeding `QueryTimeoutMs` is cancelled and the client receives
an error (§6.5). Read-only connections are released; nothing is lost,
and the query simply did not finish.

Streaming queries are bounded only up to `watch`; past that the watch
phase is not time-limited.

The main risk is a large scan over a field with no index, which adaptive
indexing reduces over time by indexing whatever keeps being filtered on
(§3.4). A timeout is therefore worth reading as a signal about the index
set rather than only as an error to retry.

## Ingestion backpressure

When a log or metric socket's receive queue is full, the kernel discards
the datagram. Neither the sender nor eventd is notified, and eventd does
not count it.

This is by design and is not a failure to be tuned away (PSPU §3.4). The
one operational note is that the queue is not being drained *while a
batch is committing*, because the same thread does both jobs (§4.1) —
so a burst arriving during a commit is the common case for log loss.
