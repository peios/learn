---
title: Log Queries
description: LOGS mode — its three optional primary selectors, projection and aggregation, and why there are no payload fields.
---

```text
LOGS [FROM origin[, origin…]] [ERROR ONLY] [CONTAINING "text"] [clauses…]
```

Log mode has three primary selectors rather than one, all optional and
all combinable. Each is sugar for a `WHERE` predicate, and each exists
because it is the thing a person actually types.

## FROM

Selects by origin. Several may be listed, comma-separated.

```text
LOGS FROM loregd
LOGS FROM loregd, peinit
LOGS
```

`FROM` is exactly `WHERE origin == "…"` for one origin and
`WHERE origin IN ("…", "…")` for several.

Origins are written as identifiers (§3.19) or as quoted strings.
A conforming origin is always an identifier (§3.7).

## ERROR ONLY

Selects lines that came from standard error.

```text
LOGS ERROR ONLY
LOGS FROM loregd SINCE 1h ago ERROR ONLY
```

It is exactly `WHERE is_error == true`, and like every clause it may
appear anywhere after `LOGS` without changing the meaning (§3.18).

## CONTAINING

Selects lines whose message contains the given text — a substring match,
folding case like every string comparison (§3.20).

```text
LOGS CONTAINING "connection refused"
LOGS FROM loregd CONTAINING "failed to open"
```

It is exactly `WHERE message CONTAINS "…"`.

`CONTAINING` is a log-specific keyword because searching text is the
primary operation on log data, and the primary operation deserves the
shortest spelling. It is a substring scan, not an indexed text search: a
collector MUST NOT restrict what it matches, and combining it with
`SINCE` is what keeps it affordable.

## Projection and aggregation

`SELECT` narrows non-aggregating results to named log fields, and is
additive across clauses (§3.22).

`COUNT BY`, `TOP N BY`, `DISTINCT` and `GROUP` work exactly as in event
mode (§3.23), with the same fixed output schemas, the same result types,
and the same prohibition on combining them with `SELECT`.

```text
LOGS SINCE 1h ago COUNT BY origin
LOGS SINCE 1h ago TOP 5 BY origin
```

## Ordering

Without `SORT`, results are ordered by timestamp descending, ties broken
as §3.21 requires.

## No payload fields

Log mode has a closed field set (§3.22). A collector MUST reject an
unknown log field name as a parse error, in a `WHERE`, a `SORT`, a
`SELECT` or a grouping clause alike.

This differs from event mode, where an unknown name is a payload field
that resolves to null. The difference is that a log record's shape is
fixed and known: a name outside it cannot be a field that this record
happens to lack, so treating it as null would answer a question the
client did not ask.
