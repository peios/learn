---
title: Limits
description: Every bound a collector must enforce, with the mainline collector's value and adjustable range, and the one relation that ties two of them together.
---

Every bound this chapter requires a collector to enforce, with the value
and adjustable range of the mainline collector. The mainline values are
**informative**: a conforming collector chooses its own, and a producer
or client MUST NOT depend on any of them (§3.29).

The mainline configuration key names are those of eventd, whose
configuration is catalogued in the eventd TRMP §A.

## Ingestion

| Bound | Mainline value | Mainline range | Key | Section |
|---|---|---|---|---|
| Log datagram ceiling | 262144 B | 4096 – 1048576 | `MaxLogDatagramBytes` | §3.6 |
| Metric datagram ceiling | 262144 B | 4096 – 1048576 | `MaxMetricDatagramBytes` | §3.9 |
| Receive queue, either socket | ≤ 4 × the ceiling | — | — | §3.6 |

## Queries

| Bound | Mainline value | Mainline range | Key | Section |
|---|---|---|---|---|
| Query message ceiling | 65536 B | 1024 – 16777216 | `MaxQueryMessageBytes` | §3.15 |
| Query timeout | 30000 ms | 1000 – 300000 | `QueryTimeoutMs` | §3.16 |
| Concurrent queries | 128 | 1 – 4096 | `MaxConcurrentQueries` | §3.14 |
| Concurrent streaming queries | 64 | 1 – 1024 | `MaxStreamingQueries` | §3.14 |
| Values per DISTINCT stream | 100000 | 1000 – 10000000 | `MaxDistinctStreamValues` | §3.27 |

## Cross-type filtering

| Bound | Mainline value | Mainline range | Key | Section |
|---|---|---|---|---|
| Existence window `W` | 15000 ms | 1000 – 300000 | `CrossTypeWindowMs` | §3.26 |
| Maximum lookback | 604800 s | 3600 – 2592000 | `CrossTypeMaxLookbackSeconds` | §3.26 |

## Fixed by this chapter

These are not configuration and a collector MUST NOT vary them.

| Quantity | Value | Section |
|---|---|---|
| Timestamp domain | `0` – `9223372036854775807` ns | §3.5 |
| GUID field width | 16 bytes | §3.7, §3.11 |
| Message length prefix | 4 bytes, little-endian | §3.15 |
| Transforms per query | at most 1 | §3.25 |
| Terminal aggregations per query | at most 1 | §3.25 |
| Queries per connection | exactly 1 | §3.14 |

## The relation between two of them

The query message ceiling MUST NOT be smaller than the largest record a
collector can store, because a record that will not fit in a response
fails every query that reaches it (§3.15). The ingestion ceilings bound
what a producer can deposit; the query message ceiling bounds what can
be handed back. Nothing enforces the relation automatically, and the
mainline defaults do not satisfy it.
