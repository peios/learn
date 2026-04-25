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

Event queries execute against all databases in the event store directory. Results from individual shards are merged using an N-way merge on the sort key (defaulting to timestamp). For TAKE N queries, each shard executes with LIMIT N and the merge selects the top N across all shards.

Log and metric queries operate on single databases (one log store, one metric store) and do not require fan-out.

## Adaptive indexing integration

Every query MUST be recorded by the adaptive indexing system (§3.3). For each WHERE predicate:

- Header column references increment that column's query frequency counter.
- Payload field references increment that field path's query frequency counter.

This applies to event queries only. Log and metric stores have fixed indexes.

## Read connections

Query execution uses read-only SQLite connections. Read-only connections in WAL mode do not block writer threads. eventd SHOULD support multiple concurrent queries.

## Timeouts

Queries MUST have a maximum execution time.

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| QueryTimeoutMs | REG_DWORD | 30000 | 1000--300000 | Maximum query execution time in milliseconds. |
