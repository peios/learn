---
title: Execution
---

## Query parsing

A query string is parsed into an abstract syntax tree (AST). The parser:

1. Identifies the mode (EVENTS, LOGS, METRIC) from the first token.
2. Extracts the primary selector (type pattern, FROM, metric name/labels).
3. Collects all clauses regardless of order.
4. Validates that the clauses are compatible with the mode (e.g., CONTAINING is only valid in LOGS mode, RATE is only valid in METRIC mode).

Parse errors are returned immediately without executing anything.

## Execution order

Regardless of clause order in the query string, execution follows a fixed sequence:

1. **Cross-type conditions** -- WHERE METRIC / WHERE EVENT / WHERE LOG conditions are evaluated first to produce time range filters.
2. **Primary selector** -- type pattern (events), FROM (logs), or metric name/labels (metrics) narrows the data source.
3. **SINCE / UNTIL** -- time range filter applied.
4. **WHERE** -- all WHERE predicates are ANDed and evaluated. Cross-type time ranges from step 1 are included as additional timestamp filters.
5. **ERROR ONLY / CONTAINING** -- log-specific filters (evaluated as WHERE predicates internally).
6. **Value functions** -- RATE, DELTA, P95, etc. for metrics.
7. **GROUP** -- grouping for aggregation.
8. **Aggregation** -- COUNT BY, TOP N BY, COUNT, SUM, AVG, MIN, MAX, DISTINCT.
9. **Window functions** -- AVG_OVER, MIN_OVER, MAX_OVER for metrics.
10. **SORT** -- ordering.
11. **SKIP / TAKE** -- pagination and limiting.
12. **SELECT** -- result records narrowed to specified fields.

SELECT is applied last -- it controls the shape of output, not the visibility of fields to other clauses.

## SQL translation

For events and logs, the query is translated to SQL internally. Header field predicates translate to SQL WHERE clauses. Payload field predicates (events) translate to `msgpack_extract` function calls. Log fields translate directly to column references.

For metrics, the query is translated to SQL against the metric store's series and samples tables. The series table is used for name and label resolution (cached in memory). The samples table is queried for the time range.

The SQL translation is an implementation detail. Clients never see SQL.

## Cross-shard fan-out (events only)

Event queries execute against all databases in the event store directory. Results from individual shards are merged depending on the query type:

- **Non-aggregation queries** (with SORT and TAKE): each shard returns up to `SKIP + TAKE` rows sorted by the sort key (or TAKE rows if no SKIP is present). The merge is an N-way merge of sorted streams. SKIP and TAKE are applied after the merge by the coordinator. Total rows read: at most `(SKIP + TAKE) × shard_count`.
- **COUNT**: each shard returns its local count. The final result is the sum across all shards.
- **COUNT BY / TOP N BY / GROUP with COUNT**: each shard returns per-group counts. The merge sums counts for the same group key across shards, then sorts by count descending and applies TAKE if present.
- **GROUP with SUM**: each shard returns per-group sums. The merge sums per-group values across shards.
- **GROUP with AVG**: each shard returns per-group sum and count. The merge computes the average from the combined sum and count across shards.
- **GROUP with MIN / MAX**: each shard returns per-group min/max. The merge takes the min/max across shards.
- **DISTINCT**: each shard returns its local distinct values. The merge computes the distinct union across all shards.

Aggregation is pushed down to individual shards wherever possible. The merge operates on partial aggregates, not full row sets. This bounds memory usage to the cardinality of the group key × shard count, not the total row count.

Log and metric queries operate on single databases (one log store, one metric store) and do not require fan-out.

> [!INFORMATIVE]
> Non-aggregation queries without TAKE have no implicit row limit. A broad query such as `EVENTS SINCE 7d ago` may return millions of rows, consuming significant memory during the cross-shard merge. The query timeout (`QueryTimeoutMs`) is the primary backstop against runaway queries. Implementations SHOULD stream merged results to the client incrementally rather than materialising the full result set in memory.

## Adaptive indexing integration

Every query MUST be recorded by the adaptive indexing system (§3.3). For each WHERE predicate:

- Header column references increment that column's query frequency counter.
- Payload field references increment that field path's query frequency counter.

This applies to event queries only. Log and metric stores have fixed indexes.

## Payload extraction

> [!INFORMATIVE]
> Constructing flat-map results from event records requires decoding the msgpack payload for each returned row. At high result counts (thousands of events), this becomes the dominant query-path cost. Implementations SHOULD use partial/lazy extraction: when SELECT is present, only decode the named payload fields rather than the entire payload. When no SELECT is present, a streaming msgpack decoder that emits key-value pairs without building a full in-memory representation reduces allocation pressure.

## Read connections

Query execution uses read-only SQLite connections. Read-only connections in WAL mode do not block writer threads. eventd SHOULD support multiple concurrent queries.

## Concurrency limits

eventd MUST enforce a maximum number of concurrent queries (streaming and non-streaming combined) to prevent resource exhaustion.

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| MaxConcurrentQueries | REG_DWORD | 128 | 1--4096 | Maximum number of concurrent queries across all clients. Includes both streaming and non-streaming queries. |

When the limit is reached, new queries MUST be rejected with an error. The per-query resource cost includes read-only SQLite connections (one per shard for event queries), memory for result merging, and CPU for query execution. The `MaxStreamingQueries` limit (§8.7) is enforced separately and is typically lower because streaming queries hold resources indefinitely.

## Timeouts

Queries MUST have a maximum execution time.

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| QueryTimeoutMs | REG_DWORD | 30000 | 1000--300000 | Maximum query execution time in milliseconds. |
