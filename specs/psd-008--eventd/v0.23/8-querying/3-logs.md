---
title: Log Queries
---

## Syntax

```
LOGS [FROM origin[, origin...]] [ERROR ONLY] [CONTAINING "text"] [clauses...]
```

The primary selectors are FROM (service name), ERROR ONLY (stderr filter), and CONTAINING (text search). All are optional. All other clauses may appear in any order.

## FROM

Filters logs by origin (service name). Multiple origins may be comma-separated.

```
LOGS FROM loregd                    -- logs from loregd
LOGS FROM loregd, peinit            -- logs from loregd or peinit
LOGS                                -- all logs
```

FROM is syntactic sugar for `WHERE origin == "..."` (single) or `WHERE origin IN ("...", "...")` (multiple).

Origins may be unquoted identifiers when they match the lexical rules in §8.1. Origins containing other characters MUST be quoted strings.

## ERROR ONLY

Filters to log lines from stderr (is_error == true).

```
LOGS ERROR ONLY                     -- all stderr output
LOGS FROM loregd ERROR ONLY         -- stderr from loregd
```

ERROR ONLY may appear anywhere after LOGS:

```
LOGS FROM loregd SINCE 1h ago ERROR ONLY    -- same result regardless of position
```

## CONTAINING

Filters to log lines whose message contains the specified text. Substring match, case-insensitive (consistent with all string comparisons in the query language).

```
LOGS CONTAINING "connection refused"
LOGS FROM loregd CONTAINING "failed to open"
```

CONTAINING is a log-specific keyword because text search is the primary operation on log data. It is syntactic sugar for `WHERE message CONTAINS "..."`:

```
LOGS WHERE message CONTAINS "error"         -- equivalent to CONTAINING "error"
```

> [!INFORMATIVE]
> CONTAINING performs a substring scan, not a full-text search. When combined with SINCE, the scan is limited to the matching time range (the timestamp index narrows the scan). Full-text indexing (FTS) is a candidate for future versions.

## Projection

SELECT controls which fixed log fields appear in non-aggregation log result
records. Multiple SELECT clauses are additive, as for event queries. If no
SELECT is present, all fixed log fields are included.

## Aggregation

COUNT BY and TOP N BY work the same as for events:

```
LOGS SINCE 1h ago COUNT BY origin           -- log volume per service
LOGS SINCE 1h ago TOP 5 BY origin           -- most verbose services
```

Grouping equality and deterministic tie ordering are defined in §8.1.
Aggregation result types are the same as for event queries (§8.2).
Aggregation queries have fixed output schemas as defined for event queries.
SELECT MUST NOT be combined with `COUNT BY`, `TOP N BY`, `DISTINCT`, or `GROUP`.
`DISTINCT ... STREAM` is permitted and uses the distinct-value streaming
semantics defined in §8.7.

## Sorting

If no SORT is present, results are ordered by timestamp descending (most recent first).
Ties are resolved by the deterministic ordering rules in §8.1.

## Examples

Recent logs from loregd:
```
LOGS FROM loregd TAKE 100
```

Errors from any service in the last 30 minutes:
```
LOGS ERROR ONLY SINCE 30m ago
```

Search for a string in loregd logs:
```
LOGS FROM loregd CONTAINING "connection refused" SINCE 1d ago
```

Most verbose services in the last hour:
```
LOGS SINCE 1h ago TOP 5 BY origin
```

Live tail of loregd logs:
```
LOGS FROM loregd STREAM
```

Loregd logs during high memory usage:
```
LOGS FROM loregd SINCE 1h ago WHERE METRIC mem.usage[service="loregd"] > 90
```
