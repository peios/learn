---
title: Metric Writer
---

## Ingestion thread

eventd MUST run a dedicated metric ingestion thread that reads datagrams from the metric socket and writes data points to the metric store. The metric ingestion thread is independent of the event and log ingestion paths.

## Processing

For each received metric record, the ingestion thread:

1. Resolves the time series by name and labels using the in-memory series cache (§7.1). If the series does not exist, a new row is inserted into the `series` table with the type from the record, and the cache is updated.
2. Validates that the record's type matches the series type. If the type does not match (e.g., a gauge sample for a series registered as a counter), the record MUST be dropped silently. The series type is set at creation time and is immutable -- a series cannot change type.
3. Inserts a row into the `samples` table with the resolved `series_id`, timestamp, and value. For histogram-type metrics, the histogram data is encoded as msgpack and stored in the `histogram_data` column.

## Batched writes

The metric writer uses the same adaptive batch sizing approach as the event and log writers. Metric data points are accumulated into a transaction and committed when either the batch size or latency threshold is reached.

The metric writer's batch parameters are configured independently:

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| MetricMaxBatchSize | REG_DWORD | 5000 | 100--100000 | Maximum metric samples per transaction. |
| MetricMaxBatchLatencyMs | REG_DWORD | 1000 | 10--5000 | Maximum ms before a metric batch is committed. |

> [!INFORMATIVE]
> The default metric batch latency (1000ms) is higher than both the event and log defaults. Metrics are typically sampled at 15-second intervals, so a 1-second commit window accumulates multiple samples efficiently without meaningful latency impact. Under burst conditions (many metrics arriving simultaneously from a collection sweep), the batch size limit ensures timely commits.

## SQLite configuration

The metric store database MUST be opened in WAL mode. The `synchronous` pragma SHOULD be set to NORMAL. Per-transaction fsync is not required for metrics because metric loss on power failure is acceptable.

## Series cache

The in-memory series cache maps (name, canonical labels, boundaries hash) to `series_id`. For counter and gauge series, the boundaries hash component is absent. The cache is bounded by `MetricSeriesCacheSize` (default 50,000 entries) and uses LRU eviction. Cache hits resolve series in a hash table lookup. Cache misses fall back to a SQLite SELECT and insert the result into the cache, evicting the least recently used entry if full. See §7.1 for details.
