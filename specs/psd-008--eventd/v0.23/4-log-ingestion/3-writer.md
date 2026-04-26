---
title: Log Writer
---

## Ingestion thread

eventd MUST run a dedicated log ingestion thread that reads datagrams from the log socket and writes log records to the log store. The log ingestion thread is independent of the event drain threads and event writer threads -- log ingestion does not contend with event ingestion.

> [!INFORMATIVE]
> The log ingestion thread performs both socket reads and SQLite writes on a single thread. During a batch commit, the socket is not being drained and datagrams may be dropped. Splitting into separate reader and writer threads (with a bounded handoff channel, as the event path uses) would decouple these operations. The single-thread model is a deliberate simplification for v0.23: log loss is tolerable, log volumes are typically lower than event volumes, and the single-thread model avoids handoff channel complexity. If log throughput becomes a bottleneck, log store sharding (analogous to event store sharding) is a more impactful improvement than thread splitting.

## Batched writes

The log writer uses the same adaptive batch sizing approach as the event writer (§2.4). Log records are accumulated into a transaction and committed when either the batch size or latency threshold is reached.

The log writer's batch parameters are configured independently from the event writer:

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| LogMaxBatchSize | REG_DWORD | 5000 | 100--100000 | Maximum number of log records in a single transaction. |
| LogMaxBatchLatencyMs | REG_DWORD | 500 | 10--5000 | Maximum time in milliseconds between the first log record entering a batch and the batch being committed. |

> [!INFORMATIVE]
> The default log batch latency (500ms) is higher than the event batch latency (100ms) because log loss is tolerable and power-loss resilience is less critical for logs than for events. Larger, less frequent batches improve throughput efficiency for the common case where log volume is moderate.

## SQLite configuration

The log store database MUST be opened in WAL mode. The `synchronous` pragma SHOULD be set to NORMAL rather than FULL. Per-transaction fsync is not required for logs because log loss on power failure is acceptable. NORMAL mode syncs at checkpoint time, providing durability against process crashes without the per-commit fsync overhead.

This is a deliberate divergence from the event store, which uses `synchronous = FULL` for per-transaction durability. The different durability requirements of events and logs justify different SQLite configurations.
