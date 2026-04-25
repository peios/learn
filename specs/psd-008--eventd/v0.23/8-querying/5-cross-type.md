---
title: Cross-Type Filtering
---

## Overview

Cross-type filtering allows a query on one data type to be filtered by conditions on another data type. This is the primary mechanism for correlating events, logs, and metrics without explicit JOINs.

Cross-type filters appear as WHERE clauses with a type keyword (METRIC, EVENT, LOG) indicating the data source for the condition.

## WHERE METRIC

Filters records to time periods when a metric condition holds. Available in EVENTS and LOGS queries.

```
EVENTS kacs.* SINCE 1h ago WHERE METRIC cpu.usage > 80
LOGS FROM loregd WHERE METRIC mem.usage[service="loregd"] > 90
```

### Semantics

The query engine pre-computes the time ranges where the metric condition is true by scanning the metric store for matching samples. These time ranges are then applied as additional timestamp filters on the primary data source.

For each matching sample where the condition holds, a time range is constructed from that sample's timestamp to the next sample's timestamp (or the end of the query window, whichever is smaller). This interpolation assumes the metric condition holds between samples.

The metric condition uses the same comparison operators as standard WHERE clauses. The metric selector uses the same syntax as METRIC queries (name, brackets for labels):

```
WHERE METRIC cpu.usage > 80                     -- aggregated across all labels
WHERE METRIC cpu.usage[core="0"] > 90           -- specific series
WHERE METRIC disk.io.utilisation[device="sda"] > 95
```

## WHERE EVENT

Filters records to time periods when events of a specified type exist. Available in LOGS and METRIC queries.

```
LOGS FROM loregd WHERE EVENT kacs.access_denied EXISTS
METRIC cpu.usage[] SINCE 1h ago WHERE EVENT synthetic.storage_error EXISTS
```

The `EXISTS` keyword indicates that the condition is satisfied when at least one event of the specified type exists within the relevant time window. The event type supports glob patterns:

```
WHERE EVENT kacs.* EXISTS                       -- any KACS event
WHERE EVENT synthetic.gap EXISTS                -- gap records
```

## WHERE LOG

Filters records to time periods when matching log entries exist. Available in EVENTS and METRIC queries.

```
EVENTS kacs.* WHERE LOG loregd CONTAINING "error" EXISTS
```

The LOG condition specifies an origin and optionally a CONTAINING text filter.

## Time window resolution

Cross-type conditions are evaluated against the metric sample interval or event density, not per-row of the primary data source. The time ranges where the condition holds are computed once and applied as a filter.

For metric conditions, the resolution is the metric sample interval (typically 15 seconds). A metric condition like `WHERE METRIC cpu.usage > 80` means "during periods where the most recent cpu.usage sample exceeded 80."

For event conditions, `EXISTS` means "at least one matching event occurred within the sample interval surrounding the primary record's timestamp." The sample interval for event existence checks is configurable:

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| CrossTypeWindowMs | REG_DWORD | 15000 | 1000--300000 | Time window in milliseconds for cross-type event and log existence checks. |

## Performance

Cross-type filters require reading from multiple stores. The cross-type condition is evaluated first to produce time ranges, then the primary query is executed with additional timestamp filters. This is efficient when the cross-type condition is selective (narrow time ranges), and expensive when the condition is broadly true (e.g., CPU above 10% for the entire query window).

Cross-type WHERE predicates are tracked by the adaptive indexing system, same as standard WHERE predicates.
