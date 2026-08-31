---
title: The Metric Writer
description: One thread reads the metric socket and writes samples — processing a record, out-of-order samples, batching and durability.
---

One thread reads datagrams from the metric socket and writes samples to
the metric store, independent of both the event and log paths. It has
the same single-thread shape as the log writer, with the same
consequence during a commit (§4.1).

The wire contract is PSPU §3.9 to §3.13.

## Processing a record

For each valid record:

1. **Authorize the name.** The datagram's KACS token must hold
   `EVENTD_PUBLISH` on the resolved metric-name descriptor (§7.6).
2. **Resolve the series** from name and labels — and, for a histogram,
   bucket boundaries — through the in-memory series cache (§5.3). A
   series that does not exist is inserted into `series` with the
   record's type, and the cache is updated.
3. **Check the type.** If the record's type differs from the resolved
   series' type, the record is dropped without replying to the producer.
   The type is set at creation and is immutable; a series never changes
   type.
4. **Insert the sample** into `samples` with the resolved `series_id`,
   the timestamp and the value. SQLite assigns `samples.id`, which is
   the deterministic tiebreaker among samples sharing a timestamp
   (§5.2). A histogram's data is encoded as the canonical MessagePack
   sample map and stored in `histogram_data`.

The transaction result counts step-3 failures and carries the most recent
conflict's metric name and expected and received types. The metric thread
adds the count to an in-memory diagnostic total, retains that conflict,
and emits a coalesced standard-error warning at most once per minute.
`SIGQUIT` includes both the total and latest conflict (§8.5).

There is still no response to the producer and no event per failure.
Authentication identifies the producer; it does not make reactions
proportional to its bad input safe. The one-minute global bound is what
keeps the warning from becoming the amplification vector PSPU §3.4
forbids. A valid transaction takes only the existing zero-mismatch branch
and performs no diagnostic allocation or synchronization.

## Out-of-order samples

The writer stores a valid sample whose timestamp precedes samples
already held for that series.

Producers batch, clocks step, and sweeps get retried. Refusing late
samples would convert any of those into silent loss, so eventd accepts
them and defines every ordering it performs over `(timestamp, id)`
rather than over insertion order. That makes raw `RATE` and `DELTA`
evaluation deterministic regardless of arrival (§6.2).

## Batching

The same adaptive algorithm as the event and log writers (§2.4), with
the socket receive queue as input. A transaction opens at the first
valid sample and commits when any of these holds:

- no further datagram is immediately available
- the batch holds `MetricMaxBatchSize` samples
- `MetricMaxBatchLatencyMs` has elapsed since the first sample entered
  it

A datagram yielding more samples than fit is split across transactions,
the writer committing before continuing with the same datagram. Neither
cap is ever exceeded.

The defaults (§A) are 5000 samples and 1000 milliseconds — the longest
latency of the three writers. Metrics are typically sampled every
fifteen seconds, so a one-second commit window accumulates a whole
sweep's worth without any latency that a dashboard could notice. Under a
burst, where a collection agent submits every core, disk and interface
at once, the size cap is what forces a timely commit.

## Durability

WAL mode with `synchronous=NORMAL`, as the log store (§4.1). Metric loss
on power failure is acceptable, so per-transaction fsync buys nothing.
