---
title: Query Language Reference
description: An index of the query language and where each construct is valid — shape, clause validity, rejected combinations, functions, operators and fields.
---

An index of the language, and of where each construct is valid. The
normative definitions are in §3.18 to §3.27; nothing here adds a rule.

## Shape

```text
EVENTS [type_pattern]                             [clauses…]
LOGS   [FROM o[, o…]] [ERROR ONLY] [CONTAINING s] [clauses…]
METRIC name[label_selector] [transform] [aggregation] [clauses…]
```

## Clause validity

| Clause | EVENTS | LOGS | METRIC | Section |
|---|---|---|---|---|
| `SINCE` / `UNTIL` | yes | yes | yes | §3.19 |
| `WHERE` | yes | yes | yes | §3.20 |
| `WHERE METRIC` | yes | yes | no | §3.26 |
| `WHERE EVENT … EXISTS` | no | yes | yes | §3.26 |
| `WHERE LOG … EXISTS` | yes | no | yes | §3.26 |
| `SORT` | yes | yes | yes | §3.21 |
| `TAKE` / `SKIP` | yes | yes | yes | §3.18 |
| `SELECT` | non-aggregating only | non-aggregating only | no | §3.22 |
| `COUNT BY` / `TOP N BY` | yes | yes | no | §3.23 |
| `DISTINCT` | yes | yes | no | §3.23 |
| `GROUP` + function | yes | yes | no | §3.23 |
| `STREAM` | yes | yes | no | §3.27 |
| `ERROR ONLY` / `CONTAINING` | no | yes | no | §3.24 |
| `INDEX` | yes | no | no | §3.23 |

`WHERE` and `SELECT` are the only repeatable clauses (§3.18).

## Combinations that are rejected

| Combination | Rejected at | Section |
|---|---|---|
| `SELECT` with `COUNT BY`, `TOP N BY`, `DISTINCT` or `GROUP` | parse | §3.22 |
| `SELECT` in metric mode | parse | §3.22 |
| `STREAM` with `COUNT BY`, `TOP N BY` or `GROUP` | parse | §3.27 |
| `STREAM` with `UNTIL` | parse | §3.27 |
| `DISTINCT … STREAM` with `SORT`, `TAKE` or `SKIP` | parse | §3.27 |
| Window aggregation without `SINCE` | parse | §3.25 |
| Scalar and window aggregation together | parse | §3.25 |
| Two transforms | parse | §3.25 |
| Cross-type filter without `SINCE` | parse | §3.26 |
| `=` outside a label selector | parse | §3.20 |
| `== NULL` or `!= NULL` | parse | §3.19 |
| Ordering operator on a binary literal | parse | §3.20 |
| Ordering operator on a fixed field that cannot be ordered | parse or planning | §3.20 |
| Unknown log field name | parse | §3.24 |
| Effective range beyond the lookback limit | planning | §3.26 |
| Selected metric series spanning more than one type | execution | §3.25 |
| `RATE` or `DELTA` on a gauge or histogram | execution | §3.25 |
| Percentile on a counter or gauge | execution | §3.25 |
| Histogram series with no percentile function | execution | §3.25 |
| Unbracketed metric query with `SINCE` resolving to several series | execution | §3.25 |
| Cross-type metric selector resolving to several series | execution | §3.26 |
| Aggregation producing a non-finite value | execution | §3.23, §3.25 |

"Parse" failures need no data. "Execution" failures depend on what the
store holds, so the same query string may succeed on one system and fail
on another.

## Metric functions

| Keyword | Stage | Valid on | Produces |
|---|---|---|---|
| `RATE` | transform | counter | per-second change |
| `DELTA` | transform | counter | absolute change |
| `P50` `P95` `P99` | transform | histogram | one value per sample |
| `AVG` `MIN` `MAX` `SUM` | scalar aggregation | counter, gauge | one value |
| `AVG_OVER` `MIN_OVER` `MAX_OVER` `SUM_OVER` | window aggregation | counter, gauge | one value per window |

Transforms feed aggregations; a query may have at most one of each
(§3.25).

## Operators

`==` `!=` `>` `>=` `<` `<=` `STARTS_WITH` `ENDS_WITH` `CONTAINS` `IN`
`NOT_IN` `IS NULL` `IS NOT NULL`, combined with `AND` and `OR` (§3.20).

There is no `NOT` and no `=`.

## Literals

| Kind | Form | Section |
|---|---|---|
| Identifier | `[A-Za-z_][A-Za-z0-9_.-]*` | §3.19 |
| String | `"…"` with `\"` `\\` `\n` `\r` `\t` `\uXXXX` | §3.19 |
| Binary | `x"0a1b…"`, even digit count | §3.19 |
| Integer | decimal or `0x…` | §3.19 |
| Float | finite, with a fraction or exponent | §3.19 |
| Boolean | `true`, `false` | §3.19 |
| Null | `NULL`, in `IS NULL` only | §3.19 |
| Duration | `<n>s` `<n>m` `<n>h` `<n>d`, non-zero | §3.19 |
| Time | `<duration> ago`, `<duration> hence`, `today`, `yesterday`, `YYYY-MM-DD`, `YYYY-MM-DDTHH:MM:SS` | §3.19 |
| GUID | `8-4-4-4-12`, braced or not | §3.19 |

## Fields

| Mode | Fixed fields | Everything else |
|---|---|---|
| EVENTS | `timestamp` `cpu_id` `sequence` `origin_class` `event_type` `effective_token_guid` `true_token_guid` `process_guid` `boot_id` | a flattened payload path, or null |
| LOGS | `timestamp` `origin` `is_error` `message` `boot_id` `job_id` | a parse error |
| METRIC | `timestamp` `boot_id` `name` `type` `value` `overflow` | a label, or null |

## Aliases

`origin_class` accepts `userspace` (0), `kmes` (1), `kacs` (2), `lcs`
(3). These are the only aliased values in the language (§3.23).

## Default ordering

| Mode | Without `SORT` |
|---|---|
| EVENTS, LOGS | timestamp descending |
| METRIC | timestamp ascending |
| `COUNT BY`, `TOP N BY` | count descending |
| `DISTINCT` | by the distinct value |

All ties are broken to a total order (§3.21).
