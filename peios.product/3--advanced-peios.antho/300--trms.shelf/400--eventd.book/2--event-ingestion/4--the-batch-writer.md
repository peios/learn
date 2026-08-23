---
title: The Batch Writer
description: How each writer thread commits — explicit transactions, adaptive batch sizing, WAL checkpointing and prepared statements.
---

## Transactions

Each writer thread writes to its shard with explicit transactions: a
`BEGIN`, one `INSERT` per event, a `COMMIT`. The commit is the
durability boundary.

The database runs in WAL mode with `synchronous = FULL`, so every commit
fsyncs the write-ahead log. This is the strictest of the three stores'
settings, and the only one where per-transaction durability is bought at
per-transaction cost — because an event may be an audit record and
losing the last second of them to a power cut is a real loss.

## Adaptive batch sizing

The writer sizes each batch to balance throughput against how much sits
uncommitted at any moment.

**Throughput is always the priority.** If eventd falls behind the
emission rate, ring buffers fill and events are overwritten, which is
irrecoverable; a shorter power-loss window is not worth that trade. The
algorithm maximises resilience *within* the constraint that throughput
is maintained, never against it.

1. When the first event is available, the writer opens a transaction and
   records the start time.
2. It reads available events from its drain threads and inserts them.
3. After each group of inserts it commits if any of these holds:
   - no assigned drain thread currently has an event available
   - the batch holds `MaxBatchSize` events
   - `MaxBatchLatencyMs` has elapsed since the first event entered it
4. Otherwise it keeps reading and inserting.
5. With nothing available and an empty batch, it sleeps until a producer
   wakes it.

The first condition is what makes the algorithm adaptive. Under light
load the input drains immediately, so a batch of three events commits at
once and the exposure window is microseconds. Under sustained load
batches grow until they hit the size cap or the latency cap, whichever
comes first, and the per-commit fsync is amortised across thousands of
rows.

The writer chooses its own insert-group size, subject to a group never
letting a batch exceed the size cap or stay open past the latency cap.

Both bounds are configuration (§A). The defaults are 10000 events and
100 milliseconds — the tightest latency of the three stores, for the
same reason the durability setting is the strictest.

## WAL checkpointing

WAL mode accumulates log data until a checkpoint copies it back into the
main database file. Under sustained writes the log grows.

Each writer triggers a checkpoint when its write-ahead log reaches
`WalCheckpointPages` (§A), in `SQLITE_CHECKPOINT_PASSIVE` mode —
checkpointing as much as it can without blocking readers. If a passive
checkpoint cannot make progress because readers hold pages, the writer
does not block: it keeps writing and retries after a later commit.

Checkpointing runs on the writer thread and briefly serialises with
insert work, which is inherent to SQLite rather than a choice — a
database cannot be checkpointed and written concurrently. Passive mode
is the lightest option available, yielding immediately when readers hold
pages, and the per-checkpoint cost is bounded by the threshold.

## Prepared statements

Each writer prepares its `INSERT` once at startup and reuses it for
every row, which keeps SQL parsing and planning off the hot path
entirely.
