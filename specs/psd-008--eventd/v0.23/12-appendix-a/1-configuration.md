---
title: Configuration Keys
---

All configuration keys live under `Machine\System\eventd\`. eventd ignores unknown keys in this subtree. Invalid values are ignored and the compiled-in default is retained. eventd MUST emit a synthetic `eventd.config_change` event when a valid configuration change is applied.

## Required keys

These keys MUST exist for eventd to start. There are no compiled-in defaults.

| Key | Type | Description |
|---|---|---|
| EventStorePath | REG_SZ | Directory path for event shard databases. |
| LogStorePath | REG_SZ | File path for the log store database. |
| MetricStorePath | REG_SZ | File path for the metric store database. |
| QuerySocketPath | REG_SZ | Unix socket path for query access. |
| LogSocketPath | REG_SZ | Unix socket path for log ingestion. |
| MetricSocketPath | REG_SZ | Unix socket path for metric ingestion. |

## Event ingestion

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| StorageShards | REG_DWORD | 0 | 0--256 | Number of event shard databases. 0 = CPU count. |
| MaxBatchSize | REG_DWORD | 10000 | 100--100000 | Maximum events per event writer transaction. |
| MaxBatchLatencyMs | REG_DWORD | 100 | 10--5000 | Maximum ms before an event batch is committed. |

## Log ingestion

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| LogMaxBatchSize | REG_DWORD | 5000 | 100--100000 | Maximum log records per transaction. |
| LogMaxBatchLatencyMs | REG_DWORD | 500 | 10--5000 | Maximum ms before a log batch is committed. |

## Adaptive indexing (events)

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| AdaptiveIndexWindowHours | REG_DWORD | 24 | 1--168 | Rolling window for query frequency measurement. |
| AdaptiveIndexCreateThreshold | REG_DWORD | 100 | 10--10000 | Queries on a field required to trigger index creation. |
| AdaptiveIndexDropThreshold | REG_DWORD | 10 | 1--1000 | Queries below which an index is removed from the desired set. MUST be less than create threshold. |

## Adaptive rollups (metrics)

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| AdaptiveRollupWindowHours | REG_DWORD | 48 | 1--168 | Rolling window for rollup query frequency measurement. |
| AdaptiveRollupCreateThreshold | REG_DWORD | 50 | 10--10000 | Queries required to trigger rollup computation. |
| AdaptiveRollupDropThreshold | REG_DWORD | 5 | 1--1000 | Queries below which a rollup pair is removed. MUST be less than create threshold. |

## Retention

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| EventRetentionDays | REG_DWORD | 30 | 1--3650 | Maximum age of events in days. |
| EventRetentionMaxBytes | REG_QWORD | 0 | 0--2^64-1 | Maximum total size of event shard databases. 0 = no limit. |
| LogRetentionDays | REG_DWORD | 14 | 1--3650 | Maximum age of log entries in days. |
| LogRetentionMaxBytes | REG_QWORD | 0 | 0--2^64-1 | Maximum size of log store database. 0 = no limit. |
| MetricRetentionDays | REG_DWORD | 90 | 1--3650 | Maximum age of metric samples in days. |
| MetricRetentionMaxBytes | REG_QWORD | 0 | 0--2^64-1 | Maximum size of metric store database. 0 = no limit. |
| RetentionCheckIntervalMinutes | REG_DWORD | 60 | 1--1440 | How often the retention process runs. |

## Querying

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| QueryTimeoutMs | REG_DWORD | 30000 | 1000--300000 | Maximum query execution time in ms. |

## Cross-type filtering

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| CrossTypeWindowMs | REG_DWORD | 15000 | 1000--300000 | Time window for cross-type event/log existence checks. |

## Security subtree

SDs for read-path access control are stored under `Machine\System\eventd\Security\`:

```
Machine\System\eventd\Security\Events\*
Machine\System\eventd\Security\Events\<pattern>
Machine\System\eventd\Security\Logs\*
Machine\System\eventd\Security\Logs\<pattern>
Machine\System\eventd\Security\Metrics\*
Machine\System\eventd\Security\Metrics\<pattern>
```

See §9.1 for SD structure and default values.

## Runtime vs restart

| Change | Effect |
|---|---|
| Tuning parameters (batch sizes, latencies, retention, adaptive thresholds, query timeout, cross-type window) | Applied immediately. |
| Socket paths | Requires restart. |
| Store paths | Requires restart. |
| StorageShards | Requires restart. |
| Security SDs | Applied on next query (SD cache invalidated by registry watch). |
