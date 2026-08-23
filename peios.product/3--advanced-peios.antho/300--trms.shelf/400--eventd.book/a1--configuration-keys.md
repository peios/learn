---
title: Configuration Keys
description: Every configuration key under the eventd registry subtree, its type and default, and how an invalid value is treated.
---

Every key lives under `Machine\System\eventd\`. eventd ignores unknown
keys in the subtree. An invalid value is ignored and the value already
in use is retained, and eventd emits a `synthetic.config_change` event
for every change actually applied (§8.3).

## Required

No compiled-in defaults. A missing or invalid value fails startup
(§8.2).

| Key | Type | Description |
|---|---|---|
| `EventStorePath` | REG_SZ | Directory for the event shard databases and `eventd-meta.db`. |
| `LogStorePath` | REG_SZ | File path for the log store database. |
| `MetricStorePath` | REG_SZ | File path for the metric store database. |
| `QuerySocketPath` | REG_SZ | Unix socket path for queries. |
| `LogSocketPath` | REG_SZ | Unix socket path for log ingestion. |
| `MetricSocketPath` | REG_SZ | Unix socket path for metric ingestion. |

## SQLite storage

| Key | Type | Default | Range | Description |
|---|---|---|---|---|
| `WalCheckpointPages` | REG_DWORD | 1000 | 100–100000 | WAL page threshold triggering a passive checkpoint, on shard, log, metric and metadata databases alike. |

## Event ingestion

| Key | Type | Default | Range | Description |
|---|---|---|---|---|
| `StorageShards` | REG_DWORD | 0 | 0–256 | Number of event shards. 0 means the CPU count. |
| `MaxBatchSize` | REG_DWORD | 10000 | 100–100000 | Maximum events per writer transaction. |
| `MaxBatchLatencyMs` | REG_DWORD | 100 | 10–5000 | Maximum ms before an event batch commits. |

## Log ingestion

| Key | Type | Default | Range | Description |
|---|---|---|---|---|
| `LogMaxBatchSize` | REG_DWORD | 5000 | 100–100000 | Maximum log records per transaction. |
| `LogMaxBatchLatencyMs` | REG_DWORD | 500 | 10–5000 | Maximum ms before a log batch commits. |
| `MaxLogDatagramBytes` | REG_DWORD | 262144 | 4096–1048576 | Maximum accepted log datagram size. |

## Metric ingestion

| Key | Type | Default | Range | Description |
|---|---|---|---|---|
| `MetricMaxBatchSize` | REG_DWORD | 5000 | 100–100000 | Maximum metric samples per transaction. |
| `MetricMaxBatchLatencyMs` | REG_DWORD | 1000 | 10–5000 | Maximum ms before a metric batch commits. |
| `MaxMetricDatagramBytes` | REG_DWORD | 262144 | 4096–1048576 | Maximum accepted metric datagram size. |
| `MetricSeriesCacheSize` | REG_DWORD | 50000 | 1000–1000000 | Entries in the LRU series resolution cache. |

## Adaptive indexing

| Key | Type | Default | Range | Description |
|---|---|---|---|---|
| `AdaptiveIndexWindowHours` | REG_DWORD | 24 | 1–168 | Rolling window over which query frequency is measured. |
| `AdaptiveIndexPolicyIntervalMinutes` | REG_DWORD | 60 | 60–1440 | How often the desired index set is recomputed. The minimum of 60 prevents index churn. |
| `AdaptiveIndexCreateThreshold` | REG_DWORD | 100 | 10–10000 | Queries on a field within the window needed to add it. |
| `AdaptiveIndexDropThreshold` | REG_DWORD | 10 | 1–1000 | Queries below which it is removed. Less than the create threshold, which is what supplies the hysteresis. |

## Index shedding

| Key | Type | Default | Range | Description |
|---|---|---|---|---|
| `SheddingWindowSeconds` | REG_DWORD | 30 | 10–300 | Sliding window for graduated shedding. |
| `SheddingBatchPercent` | REG_DWORD | 75 | 50–100 | Percentage of batches in the window exceeding 75% of `MaxBatchSize` that triggers graduated shedding. |
| `EmergencySheddingBufferPercent` | REG_DWORD | 75 | 50–95 | Ring buffer fill percentage triggering emergency shedding. |

## Adaptive rollups

| Key | Type | Default | Range | Description |
|---|---|---|---|---|
| `AdaptiveRollupWindowHours` | REG_DWORD | 48 | 1–168 | Rolling window for rollup query frequency. |
| `AdaptiveRollupScalarWindowSeconds` | REG_DWORD | 300 | 60–86400 | Base window used when a scalar range query triggers rollup creation. |
| `AdaptiveRollupCreateThreshold` | REG_DWORD | 50 | 10–10000 | Queries needed to trigger rollup computation. |
| `AdaptiveRollupDropThreshold` | REG_DWORD | 5 | 1–1000 | Frequency below which a pair leaves the registry. Less than the create threshold. |

## Retention

| Key | Type | Default | Range | Description |
|---|---|---|---|---|
| `EventRetentionDays` | REG_DWORD | 30 | 1–3650 | Maximum age of events. |
| `EventRetentionMaxBytes` | REG_QWORD | 0 | 0–2^64−1 | Maximum total logical live size of the event shards. 0 means no limit. |
| `LogRetentionDays` | REG_DWORD | 14 | 1–3650 | Maximum age of log entries. |
| `LogRetentionMaxBytes` | REG_QWORD | 0 | 0–2^64−1 | Maximum logical live size of the log store. 0 means no limit. |
| `MetricRetentionDays` | REG_DWORD | 90 | 1–3650 | Maximum age of metric samples. |
| `MetricRetentionMaxBytes` | REG_QWORD | 0 | 0–2^64−1 | Maximum logical live size of the metric store. 0 means no limit. |
| `RetentionCheckIntervalMinutes` | REG_DWORD | 60 | 1–1440 | How often the retention thread runs. |
| `RetentionDeleteBatchRows` | REG_DWORD | 10000 | 100–100000 | Maximum rows deleted in one retention transaction. |

## Querying

| Key | Type | Default | Range | Description |
|---|---|---|---|---|
| `QueryTimeoutMs` | REG_DWORD | 30000 | 1000–300000 | Maximum query execution time. |
| `MaxConcurrentQueries` | REG_DWORD | 128 | 1–4096 | Concurrent queries globally, streaming and non-streaming. |
| `MaxStreamingQueries` | REG_DWORD | 64 | 1–1024 | Concurrent streaming queries globally. |
| `MaxDistinctStreamValues` | REG_DWORD | 100000 | 1000–10000000 | Values tracked by one DISTINCT streaming query. |
| `MaxQueryMessageBytes` | REG_DWORD | 65536 | 1024–16777216 | Maximum query request or response payload. |

> [!NOTE]
> `MaxQueryMessageBytes` and the two datagram ceilings are related and
> nothing enforces the relation. A record larger than the query message
> ceiling cannot be returned and fails every query that reaches it
> (PSPU §3.15). At these defaults a producer can deposit a log line four
> times larger than any response that could carry it.

## Cross-type filtering

| Key | Type | Default | Range | Description |
|---|---|---|---|---|
| `CrossTypeWindowMs` | REG_DWORD | 15000 | 1000–300000 | Centred window for cross-type event and log existence checks. |
| `CrossTypeMaxLookbackSeconds` | REG_DWORD | 604800 | 3600–2592000 | Maximum range a cross-type filter may scan. |

## The security subtree

Read-path descriptors live under `Machine\System\eventd\Security\` and
are not configuration in the sense above (§7.2):

```text
Machine\System\eventd\Security\Events\*
Machine\System\eventd\Security\Events\<pattern>
Machine\System\eventd\Security\Logs\*
Machine\System\eventd\Security\Logs\<pattern>
Machine\System\eventd\Security\Metrics\*
Machine\System\eventd\Security\Metrics\<pattern>
```

The administrative descriptor is not here; it is `admin_sd` in
`eventd-meta.db` (§3.5).

## When a change takes effect

| Change | Effect |
|---|---|
| Every tuning parameter above | Applied immediately. |
| Socket paths | Restart. |
| Store paths | Restart. |
| `StorageShards` | Restart. |
| Security descriptors | Next query; the registry watch invalidates the cache. |
