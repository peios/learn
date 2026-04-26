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

1. The writer thread begins a transaction.
2. The writer thread reads available events from its assigned drain threads.
3. If no events are available and the current batch is non-empty, the writer SHOULD commit immediately. There is no throughput pressure, so committing minimises the power-loss window.
4. If no events are available and the current batch is empty, the writer thread waits for events (the drain threads will wake it via the handoff mechanism when events arrive).
5. If events are available, they are added to the current transaction (INSERT statements executed).
6. After each INSERT (or group of INSERTs), the writer evaluates whether to commit now or continue batching. The decision is based on the observed ratio between event arrival rate and commit throughput: if arrivals are slow relative to commit cost, commit now (resilience). If arrivals are fast relative to commit cost, continue batching (throughput).
7. The batch MUST NOT exceed `MaxBatchSize` events. When the limit is reached, the writer MUST commit regardless of throughput conditions.

The specific heuristics for step 6 are implementation-defined. The normative requirements are:

- Under low load, the writer MUST commit within `MaxBatchLatencyMs` of the first event in the batch.
- Under high load, the writer MUST NOT produce batches larger than `MaxBatchSize`.
- The writer MUST NOT hold an open transaction indefinitely.
- The adaptive algorithm SHOULD NOT oscillate between extreme batch sizes under bursty workloads. Rapid alternation between very small commits (high fsync overhead) and very large commits (high latency) degrades both throughput and power-loss resilience. The implementation SHOULD apply smoothing or hysteresis to the arrival rate estimate.

## Configuration

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| MaxBatchSize | REG_DWORD | 10000 | 100--100000 | Maximum number of events in a single transaction. |
| MaxBatchLatencyMs | REG_DWORD | 100 | 10--5000 | Maximum time in milliseconds between the first event entering a batch and the batch being committed. |

These parameters bound the adaptive algorithm. `MaxBatchSize` caps the throughput-optimised case. `MaxBatchLatencyMs` caps the latency in the resilience-optimised case. The adaptive algorithm operates freely within these bounds.

## WAL checkpointing

WAL mode accumulates write-ahead log data until a checkpoint copies it back to the main database file. Under sustained write load, the WAL can grow large.

Each writer thread MUST trigger a WAL checkpoint when the WAL exceeds a size threshold. The checkpoint SHOULD use `SQLITE_CHECKPOINT_PASSIVE` mode, which checkpoints as much as possible without blocking readers. If a passive checkpoint cannot make progress (active readers hold pages), the writer MUST NOT block -- it continues writing and retries the checkpoint later.

The checkpoint threshold is implementation-defined. A reasonable default is 1000 pages (4 MB with the default 4 KB page size).

> [!INFORMATIVE]
> PASSIVE checkpointing runs on the writer thread and briefly serialises with INSERT work. This is inherent to SQLite's architecture -- checkpointing and writing cannot run concurrently on the same database. PASSIVE mode is the lightest option (it yields immediately if readers hold pages) and the per-checkpoint cost is bounded by the threshold size. No alternative design avoids this cost within SQLite's concurrency model.

## Prepared statements

Writer threads MUST use prepared statements for INSERT operations. The prepared statement is created once per writer thread at startup and reused for every INSERT. This eliminates SQL parsing overhead from the hot path.
