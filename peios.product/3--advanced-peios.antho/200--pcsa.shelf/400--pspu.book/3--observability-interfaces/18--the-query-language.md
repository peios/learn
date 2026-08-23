---
title: The Query Language
description: One string that names a mode, narrows to some data and says what to do with it — the three modes, the clauses, and their execution order.
---

A query is one string. It names a mode, narrows to some data, and says
what to do with it.

```text
EVENTS kacs.* SINCE 1h ago WHERE process_guid == "550e8400-e29b-41d4-a716-446655440000" TAKE 100
LOGS FROM loregd ERROR ONLY CONTAINING "connection refused" SINCE 1d ago
METRIC cpu.usage[core="0"] SINCE 1h ago AVG_OVER 5m
```

## Three modes

The first token selects the mode, and a collector MUST reject a query
whose first token is not one of them.

- **`EVENTS`** searches structured event records, primarily by event
  type (§3.23).
- **`LOGS`** searches log output, primarily by origin (§3.24).
- **`METRIC`** evaluates measurements, primarily by name and labels
  (§3.25).

Events and logs are *record-oriented*: collections you search, returning
the records that matched. Metrics are *value-oriented*: measurements you
evaluate, returning numbers computed from samples. The modes differ
because the data differs, and forcing all three through one shape would
serve none of them.

## The primary selector

Immediately after the mode comes an optional **primary selector**,
specific to the mode: an event type pattern, `FROM` with one or more log
origins, or a metric name with an optional label selector. It narrows
the data before anything else runs.

A primary selector MUST NOT be repeated unless its mode defines a list
form — `LOGS FROM a, b` is one selector naming two origins, not two
selectors.

## Clauses

Everything after the primary selector is a **clause**, and clauses MAY
appear in any order. `EVENTS SINCE 1h ago TAKE 10` and
`EVENTS TAKE 10 SINCE 1h ago` are the same query.

Order of appearance never affects meaning. Execution follows the fixed
sequence below regardless of how the string was written, so a collector
MUST NOT derive semantics from clause position.

These clauses work identically in all three modes:

| Clause | Meaning |
|---|---|
| `SINCE t` | Lower time bound, inclusive. |
| `UNTIL t` | Upper time bound, exclusive. Defaults to the evaluation time. |
| `WHERE p` | Filter by a predicate (§3.20). |
| `WHERE METRIC …` / `WHERE EVENT …` / `WHERE LOG …` | Filter by a condition on another data type (§3.26). |
| `SORT f [ASC\|DESC], …` | Order the results (§3.21). |
| `TAKE n` | Return at most `n`. |
| `SKIP n` | Discard the first `n` after ordering. |
| `STREAM` | Deliver matching records as they arrive (§3.27). |

## Execution order

Whatever order the clauses were written in, a collector MUST evaluate
them in this sequence:

| | Phase |
|---|---|
| 1 | Cross-type conditions, producing time ranges (§3.26) |
| 2 | The primary selector |
| 3 | Access control on the primary and cross-type sources (§3.28) |
| 4 | `SINCE` and `UNTIL` |
| 5 | `WHERE`, including the ranges from phase 1 |
| 6 | `ERROR ONLY` and `CONTAINING`, as `WHERE` predicates (§3.24) |
| 7 | Metric transforms (§3.25) |
| 8 | `GROUP` |
| 9 | `COUNT BY`, `TOP N BY`, `DISTINCT`, and the aggregation functions |
| 10 | Metric window aggregations (§3.25) |
| 11 | `SORT` (§3.21) |
| 12 | `SKIP` and `TAKE` |
| 13 | `SELECT` (§3.22) |

Two positions in that list are load-bearing.

**Access control is third**, before every filter, aggregate, sort and
limit. It is part of the query's logical execution and not a filter
applied to the output (§3.28).

**`SELECT` is last.** It shapes the output and nothing else; a field it
omits is still available to every earlier phase (§3.22).

## Repetition

A clause MUST appear at most once, and a collector MUST reject a repeat
as a parse error, with two exceptions:

- **`WHERE` is repeatable.** Multiple `WHERE` clauses are combined with
  `AND`, each treated as a parenthesised group: `WHERE a == 1 OR b == 2`
  followed by `WHERE c == 3` means `(a == 1 OR b == 2) AND c == 3`.
- **`SELECT` is repeatable** where it is valid at all, and is additive:
  `SELECT timestamp SELECT event_type` names both fields.

Both exist so that a query can be built up in pieces — by a tool
appending a filter, or by a person adding one to a query they already
have — without rewriting what is already there.

## Counts

`TAKE`, `SKIP` and the `N` of `TOP N BY` are unsigned decimal integers
that MUST fit in 64 bits. A negative, hexadecimal, floating-point or
missing count is a parse error.

`SKIP` defaults to 0. `TAKE` omitted means no limit. `TAKE 0` and
`TOP 0 BY` are valid, and return no records after every earlier phase
has run — which is not the same as not running the query, because a
`TOP 0 BY` still counts and a `TAKE 0` still enforces access control.

> [!NOTE]
> A non-aggregating query without `TAKE` has no implicit limit, and a
> broad one over a long range may match millions of records. The timeout
> (§3.16) is the only backstop.

## Case

Keywords are matched case-insensitively, using ASCII case folding, in
grammar positions where a keyword is expected. This document writes them
in uppercase by convention only.

Identifiers are case-sensitive, except where the language defines a
named alias for a value (§3.23).

A word spelled like a keyword MAY be used where the grammar expects an
identifier or a value: `LOGS FROM stream` selects the origin `stream`,
while `LOGS STREAM` enables streaming. A collector MUST resolve the
ambiguity by grammar position and MUST NOT reserve keywords globally.
