---
title: Log Writer
---

## Ingestion thread

eventd MUST run a dedicated log ingestion thread that reads datagrams from the log socket and writes log records to the log store. The log ingestion thread is independent of the event drain threads and event writer threads -- log ingestion does not contend with event ingestion.

> [!INFORMATIVE]
> The log ingestion thread performs both socket reads and SQLite writes on a single thread. During a batch commit, the socket is not being drained and datagrams may be dropped. Splitting into separate reader and writer threads (with a bounded handoff channel, as the event path uses) would decouple these operations. The single-thread model is a deliberate simplification for v0.23: log loss is tolerable, log volumes are typically lower than event volumes, and the single-thread model avoids handoff channel complexity. If log throughput becomes a bottleneck, log store sharding (analogous to event store sharding) is a more impactful improvement than thread splitting.

## Batched writes

The log writer uses the same adaptive batch sizing approach as the event writer
(§2.4), with the log socket receive queue as its input source. A transaction
begins when the first valid log record for a batch is available. The writer
commits the transaction when any of these conditions is true:

- No additional datagram is immediately available in the socket receive queue.
- The batch contains `LogMaxBatchSize` records.
- `LogMaxBatchLatencyMs` has elapsed since the first record entered the batch.

If a received datagram contains more valid records than can fit in the remaining
space in the current transaction, the writer MUST commit the current transaction
before inserting the next record and then continue processing the same datagram
in a new transaction. A transaction MUST NOT exceed `LogMaxBatchSize` records or
remain open past `LogMaxBatchLatencyMs`.

The log writer's batch parameters are configured independently from the event writer:

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| LogMaxBatchSize | REG_DWORD | 5000 | 100--100000 | Maximum number of log records in a single transaction. |
| LogMaxBatchLatencyMs | REG_DWORD | 500 | 10--5000 | Maximum time in milliseconds between the first log record entering a batch and the batch being committed. |

> [!INFORMATIVE]
> The default log batch latency (500ms) is higher than the event batch latency (100ms) because log loss is tolerable and power-loss resilience is less critical for logs than for events. Larger, less frequent batches improve throughput efficiency for the common case where log volume is moderate.

## SQLite configuration

The log store database MUST be opened in WAL mode. The `synchronous` pragma
MUST be set to NORMAL rather than FULL. Per-transaction fsync is not required
for logs because log loss on power failure is acceptable. NORMAL mode syncs at
checkpoint time, providing durability against process crashes without the
per-commit fsync overhead.

This is a deliberate divergence from the event store, which uses `synchronous = FULL` for per-transaction durability. The different durability requirements of events and logs justify different SQLite configurations.
