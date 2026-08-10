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
3. **Access control** -- root-pattern access is applied to the primary data source and cross-type data sources. Unauthorized records are removed from the logical row set before predicates, metric transforms, aggregation, sorting, pagination, or result formatting that could reveal them.
4. **SINCE / UNTIL** -- time range filter applied.
5. **WHERE** -- all WHERE predicates are ANDed and evaluated. Cross-type time ranges from step 1 are included as additional timestamp filters. Predicates that reference fields the caller is not authorized to read are rejected as described in §9.2.
6. **ERROR ONLY / CONTAINING** -- log-specific filters (evaluated as WHERE predicates internally).
7. **Metric transforms** -- RATE, DELTA, P50/P95/P99 for metrics.
8. **GROUP** -- grouping for aggregation.
9. **Aggregation** -- COUNT BY, TOP N BY, COUNT, SUM, AVG, MIN, MAX, DISTINCT.
10. **Metric window aggregations** -- AVG_OVER, MIN_OVER, MAX_OVER, SUM_OVER for metrics.
11. **SORT** -- ordering.
12. **SKIP / TAKE** -- pagination and limiting.
13. **SELECT** -- non-aggregation event/log result records narrowed to specified fields.

SELECT is applied last for queries where it is valid -- it controls the shape of
output, not the visibility of fields to other clauses. Event and log aggregation
queries have fixed output schemas and reject SELECT during parsing. Metric
queries also have fixed output schemas and reject SELECT during parsing.

## SQL translation

For events and logs, the query is translated to SQL internally. Header field
predicates translate to SQL WHERE clauses. Payload field predicates (events)
translate to eventd-internal payload extraction predicates and may use adaptive
payload indexes (§3.3). Log fields translate directly to column references.
Payload SQL translation MUST preserve the query-language field resolution and
comparison semantics defined in §8.1; when SQLite is used only to narrow
candidate rows, eventd MUST apply the final query-language predicate evaluation
after loading the row.

For metrics, the query is translated to SQL against the metric store's series and samples tables. The series table is used for name and label resolution (cached in memory). The samples table is queried for the time range.

The SQL translation is an implementation detail. Clients never see SQL.

## Cross-shard fan-out (events only)

Event queries execute against all databases in the event store directory. Results from individual shards are merged depending on the query type:

- **Non-aggregation queries**: each shard produces rows sorted by the effective
  sort key, including deterministic tiebreakers. The coordinator performs an
  N-way merge of sorted shard streams. If `TAKE` is present, each shard returns
  at most `SKIP + TAKE` rows (or `TAKE` rows if no `SKIP` is present), and
  `SKIP`/`TAKE` are applied after the merge by the coordinator. Total rows read
  with `TAKE`: at most `(SKIP + TAKE) × shard_count`. If `TAKE` is absent, each
  shard streams all matching rows until the query completes or times out.
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
> Constructing flat-map results from event records requires decoding the msgpack payload for each returned row and applying the flattening rules in §8.1. At high result counts (thousands of events), this becomes the dominant query-path cost. Implementations SHOULD use partial/lazy extraction: when SELECT is present, only decode the named payload paths rather than the entire payload. When no SELECT is present, a streaming msgpack decoder that emits flattened key-value pairs without building a full in-memory representation reduces allocation pressure.

## Read connections

Query execution uses read-only SQLite connections. Read-only connections in WAL mode do not block writer threads. eventd MUST support concurrent query execution up to the configured `MaxConcurrentQueries` admission-control limit, subject to OS resource availability. If eventd cannot allocate the resources needed for an admitted query, it MUST return an error for that query rather than blocking writers or exceeding the configured limit.

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

The timeout clock starts after the request message has been fully decoded and
the caller token has been obtained. It covers parsing, planning, access checks,
cross-type pre-computation, SQL execution, result merging, aggregation,
pagination, projection, and transmission of the initial result set. For
non-streaming queries, eventd MUST send the `end` message before the timeout
expires. For streaming queries, eventd MUST send the `watch` message before the
timeout expires. `QueryTimeoutMs` applies only to the initial result set; the
streaming watch phase is not time-limited by `QueryTimeoutMs` and is instead
bounded by `MaxStreamingQueries`, `MaxDistinctStreamValues`, and backpressure
handling.

If the timeout expires before the relevant phase completes, eventd MUST cancel
the query and send an error response. If any `ok` result messages were already
sent for that query and no `end` or `watch` message was sent, the client MUST
discard those partial results as specified in §8.8. SQLite work MUST be interrupted using
`sqlite3_interrupt()` or an equivalent progress-handler cancellation mechanism,
and non-SQL CPU work such as msgpack flattening or cross-shard merging MUST
check the same deadline periodically.
