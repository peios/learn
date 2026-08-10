---
title: Batch Writer
---

## Transaction model

Each writer thread writes events to its shard's SQLite database using explicit transactions. A transaction consists of a BEGIN, one or more INSERT statements (one per event), and a COMMIT. The COMMIT is the durability boundary -- events in a committed transaction are guaranteed to survive process crashes and power loss.

The database MUST be opened in WAL (Write-Ahead Logging) mode. The `synchronous` pragma MUST be set to FULL. This ensures that every COMMIT fsyncs the WAL, providing per-transaction durability.

## Adaptive batch sizing

The writer thread MUST adapt its batch size to balance throughput against power-loss resilience. The goal is to commit as frequently as throughput allows, minimising the number of events in an uncommitted transaction at any given time.

Throughput is always the top priority. eventd MUST NOT fall behind the ingestion rate -- if it does, KMES ring buffers fill and kernel events are overwritten, which is irrecoverable data loss. Power-loss resilience is maximised within the constraint that throughput is maintained.

The adaptive algorithm operates as follows:

1. When the first event for a batch is available, the writer thread begins a
   transaction and records the batch start time.
2. The writer thread reads available events from its assigned drain threads and
   inserts them into the transaction.
3. After each insert group, the writer commits the transaction if any of these
   conditions is true:
   - No assigned drain thread currently has an event available for this writer.
   - The batch contains `MaxBatchSize` events.
   - `MaxBatchLatencyMs` has elapsed since the first event entered the batch.
4. If none of those conditions is true, the writer continues reading and
   inserting available events.
5. If no events are available and the current batch is empty, the writer thread
   waits for producers to wake it.

The writer MAY choose any internal insert-group size, but the group size MUST
NOT allow a batch to exceed `MaxBatchSize` or stay open past
`MaxBatchLatencyMs`. A batch with fewer than `MaxBatchSize` events is committed
immediately when the input queues are drained, which minimises the power-loss
window under low load. Under sustained load, batches naturally grow to
`MaxBatchSize` or the latency cap, whichever comes first.

## Configuration

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| MaxBatchSize | REG_DWORD | 10000 | 100--100000 | Maximum number of events in a single transaction. |
| MaxBatchLatencyMs | REG_DWORD | 100 | 10--5000 | Maximum time in milliseconds between the first event entering a batch and the batch being committed. |

These parameters bound the adaptive algorithm. `MaxBatchSize` caps the throughput-optimised case. `MaxBatchLatencyMs` caps the latency in the resilience-optimised case. The adaptive algorithm operates freely within these bounds.

## WAL checkpointing

WAL mode accumulates write-ahead log data until a checkpoint copies it back to the main database file. Under sustained write load, the WAL can grow large.

Each writer thread MUST trigger a WAL checkpoint when the WAL reaches or
exceeds `WalCheckpointPages` pages. The checkpoint MUST use
`SQLITE_CHECKPOINT_PASSIVE` mode, which checkpoints as much as possible without
blocking readers. If a passive checkpoint cannot make progress (active readers
hold pages), the writer MUST NOT block -- it continues writing and retries the
checkpoint after later commits.

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| WalCheckpointPages | REG_DWORD | 1000 | 100--100000 | SQLite WAL page threshold that triggers a passive checkpoint. |

> [!INFORMATIVE]
> PASSIVE checkpointing runs on the writer thread and briefly serialises with INSERT work. This is inherent to SQLite's architecture -- checkpointing and writing cannot run concurrently on the same database. PASSIVE mode is the lightest option (it yields immediately if readers hold pages) and the per-checkpoint cost is bounded by the threshold size. No alternative design avoids this cost within SQLite's concurrency model.

## Prepared statements

Writer threads MUST use prepared statements for INSERT operations. The prepared statement is created once per writer thread at startup and reused for every INSERT. This eliminates SQL parsing overhead from the hot path.
