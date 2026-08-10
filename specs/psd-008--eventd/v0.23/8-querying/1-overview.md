---
title: Overview
---

eventd exposes a unified query language for retrieving events, logs, and metrics. The language has three modes -- one per data type -- sharing common syntax for time ranges, filtering, limiting, streaming, and cross-type correlation. Each mode has type-specific syntax that reflects the natural access patterns of that data type.

The three modes:

- **EVENTS** -- search through structured event records. Primary access by event type. Returns collections of records.
- **LOGS** -- search through service log output. Primary access by service name. Returns collections of records.
- **METRIC** -- evaluate numeric measurements. Primary access by metric name and labels. Returns values or time series.

Events and logs are record-oriented (collections you search). Metrics are value-oriented (measurements you evaluate). The syntax reflects this distinction rather than forcing all three through a single pattern.

## Common elements

The following constructs work identically across all three modes:

| Element | Syntax | Description |
|---|---|---|
| Time start | `SINCE 1h ago` | Filter to records/samples after a point in time. |
| Time end | `UNTIL 30m ago` | Optional upper bound. Defaults to now. |
| Additional filter | `WHERE field == value` | Filter by any field. |
| Cross-type filter | `WHERE METRIC name[labels] > N` | Filter by a condition on another data type. |
| Sort | `SORT timestamp DESC` | Order result records. |
| Limit | `TAKE N` | Limit result count. |
| Offset | `SKIP N` | Skip first N results after sorting (pagination). Applies to both raw and aggregated results. |
| Streaming | `STREAM` | Live tail. May appear anywhere. |

All keywords are case-insensitive. Documentation uses uppercase by convention.

Clauses after the primary selector may appear in any order. Execution semantics are fixed regardless of clause order.

Unless a clause explicitly says it is repeatable, it MUST appear at most once in
a query. Repeating a non-repeatable clause is a parse error. `WHERE` is
repeatable and multiple WHERE clauses are ANDed as described below. `SELECT` is
repeatable and multiple SELECT clauses are additive. Mode-specific primary
selectors (`FROM`, `ERROR ONLY`, `CONTAINING`, metric label selectors, and event
type patterns) are not repeatable unless that mode explicitly defines a list
syntax, such as `LOGS FROM a, b`.

`TAKE`, `SKIP`, and `TOP N BY` counts are unsigned decimal integers that MUST fit
in the unsigned 64-bit range. A negative value, hexadecimal value, float value,
or missing value is a parse error. If `SKIP` is omitted it defaults to 0. If
`TAKE` is omitted there is no row-count limit. `TAKE 0` and `TOP 0 BY` are valid
and return no records after earlier query phases have been evaluated.

## Lexical rules

Query strings are UTF-8. Whitespace separates tokens outside quoted strings.

Keywords are matched case-insensitively using ASCII-only case folding when they appear in a grammar position where that keyword is expected. Identifiers are case-sensitive unless they are one of the named aliases explicitly defined by the query language (for example origin class aliases). An unquoted identifier with the same spelling as a keyword MAY be used in positions where the grammar expects an identifier or value rather than a keyword. For example, `LOGS FROM stream` selects origin `stream`, while `LOGS STREAM` enables streaming.

Unquoted identifiers are ASCII strings matching:

```text
[A-Za-z_][A-Za-z0-9_.-]*
```

Unquoted identifiers are used for field names, payload paths, metric names, metric label keys, event type patterns, log origins, and symbolic aliases. The characters `.`, `_`, and `-` are allowed inside identifiers; `/`, `:`, whitespace, quotes, brackets, parentheses, commas, and comparison operators are not. Values containing those characters MUST be written as quoted strings.

String literals are double-quoted UTF-8 strings. The following escapes are supported: `\"`, `\\`, `\n`, `\r`, `\t`, and `\uXXXX` for a Unicode scalar value in the range U+0000 through U+FFFF encoded as four hexadecimal digits. Code points in the UTF-16 surrogate range U+D800 through U+DFFF are invalid and MUST produce a parse error. Surrogate-pair decoding is not supported; non-BMP characters MUST be written directly as UTF-8. Other backslash escapes are invalid and MUST produce a parse error.

Metric label values in label selectors may be quoted strings or unquoted identifiers. `LOGS FROM` origins and event/metric primary patterns may be quoted strings when they contain characters not permitted in unquoted identifiers. A quoted primary pattern still uses the same `*` wildcard rules as an unquoted pattern.

## Binary literals

Binary literals are exact byte strings written as lowercase `x`, a double quote,
an even number of hexadecimal digits, and a closing double quote:

```text
WHERE target_sid == x"010500000000000515000000"
```

Hex digits inside the literal are parsed case-insensitively. The empty binary
literal `x""` is valid. Whitespace is not allowed inside the hex payload. A
binary literal with an odd number of hex digits or any non-hex digit MUST
produce a parse error. Binary literals compare only to msgpack `bin` values and
are never coerced to strings.

## Time literals

| Literal | Meaning |
|---|---|
| `Ns ago` | N seconds before now. |
| `Nm ago` | N minutes ago. |
| `Nh ago` | N hours ago. |
| `Nd ago` | N days ago. |
| `Ns hence` | N seconds after now. |
| `Nm hence` | N minutes from now. |
| `Nh hence` | N hours from now. |
| `Nd hence` | N days from now. |
| `today` | Midnight of the current day (UTC). |
| `yesterday` | Midnight of the previous day (UTC). |
| `YYYY-MM-DD` | Midnight of the specified date (UTC). |
| `YYYY-MM-DDTHH:MM:SS` | Specific time (UTC). |

Relative time literals use the duration syntax defined below. The query evaluation time is captured once before execution begins and is used consistently for every `ago`, `hence`, and omitted-`UNTIL` calculation in that query. `SINCE` is inclusive (`timestamp >= start`). `UNTIL` is exclusive (`timestamp < end`). If `UNTIL` is omitted, the end bound is the query evaluation time. If both bounds are present and `SINCE` is greater than or equal to `UNTIL`, the query returns no records.

Absolute date/time literals use a fixed UTC subset. Components MUST be
zero-padded exactly as shown (`YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`). The date
MUST be a valid Gregorian calendar date. Hours are `00`--`23`, minutes are
`00`--`59`, and seconds are `00`--`59`; leap seconds are not accepted. Timezone
suffixes and fractional seconds are not part of v0.23 and MUST produce a parse
error.

## GUID literals

GUID literals use the standard 8-4-4-4-12 hexadecimal form, with or without
braces. Hex digits are parsed case-insensitively:

```
WHERE process_guid == "550e8400-e29b-41d4-a716-446655440000"
WHERE process_guid == "{550e8400-e29b-41d4-a716-446655440000}"
```

GUID values in result records are emitted using the PSD-002 canonical string
form: lowercase 8-4-4-4-12 hexadecimal groups with braces.

## Integer literals

Integer literals are decimal or hexadecimal:

```
WHERE origin_class == 2
WHERE granted_access == 0x1F01FF
```

Decimal integers MAY have a leading `-`. A negative decimal integer MUST fit in
the signed 64-bit range. A non-negative decimal integer MUST fit in the unsigned
64-bit range. Hexadecimal integers use `0x` followed by one or more hexadecimal
digits, are always non-negative, and MUST fit in the unsigned 64-bit range. A
leading `+` is not valid. Out-of-range integer literals MUST produce a parse
error.

## Float literals

Float literals are decimal finite numbers with an optional leading `-` and
either a fractional part or an exponent, for example `42.0`, `42.5`, `0.001`,
`1e6`, and `-1.25e-3`. An integer-looking token such as `42` is an integer
literal, not a float literal. A leading `+` is not valid. Float literals are
parsed as IEEE-754 binary64 (`f64`) values and MUST be finite. `NaN`,
`Infinity`, `-Infinity`, and literals that overflow to infinity MUST produce a
parse error.

## Boolean and NULL literals

Boolean literals are `true` and `false`, matched case-insensitively using ASCII-only case folding. Boolean fields may be compared either to boolean literals or to integers `1` and `0` when a field explicitly defines that compatibility.

`NULL` is matched case-insensitively using ASCII-only case folding and is only valid in `IS NULL` and `IS NOT NULL` predicates. Equality comparisons to NULL (`field == NULL`, `field != NULL`) are invalid and MUST produce a parse error.

## Duration literals

Durations used in relative time literals and metric window aggregations use an unsigned decimal integer followed immediately by a unit: `s`, `m`, `h`, or `d`. Units mean seconds, minutes, hours, and days respectively. Zero-duration values are invalid and MUST produce a parse error.

## Comparison operators

| Operator | Meaning | Applicable types |
|---|---|---|
| `==` | Equals | All |
| `!=` | Not equals | All |
| `>` | Greater than | Integer, float, timestamp |
| `>=` | Greater than or equal | Integer, float, timestamp |
| `<` | Less than | Integer, float, timestamp |
| `<=` | Less than or equal | Integer, float, timestamp |
| `STARTS_WITH` | String prefix match | String |
| `ENDS_WITH` | String suffix match | String |
| `CONTAINS` | Substring match | String |
| `IN` | Value is in a set | All |
| `NOT_IN` | Value is not in a set | All |
| `IS NULL` | Value is NULL | Any |
| `IS NOT NULL` | Value is not NULL | Any |

All string comparisons (`==`, `!=`, `STARTS_WITH`, `ENDS_WITH`, `CONTAINS`, `IN`, `NOT_IN`) are case-insensitive by default using ASCII-only case folding. Bytes for ASCII `A`--`Z` compare equal to the corresponding `a`--`z`; all non-ASCII UTF-8 bytes compare exactly. This applies to event fields, payload fields, log messages, metric labels, and query-language pattern matching. Integer, float, GUID, timestamp, and binary comparisons are unaffected.

Integer and float values compare using mathematical numeric comparison, not by
casting both operands to SQLite or `f64` storage classes. Equality between an
integer and a finite float is true only when the float exactly represents the
same mathematical value. Ordering comparisons between integers and floats MUST
be exact for the represented values, including integers outside the exact
integer range of binary64.

Values of different non-numeric types are not equal. For example, string `"1"`
is not equal to integer `1`; `!=` is true for those two values. Numeric ordering
operators (`>`, `>=`, `<`, `<=`) applied to a dynamic field whose runtime value
is non-numeric evaluate false for that record. If a predicate applies an operator
to a known fixed field whose type is incompatible with that operator, eventd MUST
reject the query during parsing or planning instead of executing a predicate that
can never match.

Binary values compare by exact byte equality for `==`, `!=`, `IN`, and
`NOT_IN`. Ordering predicates (`>`, `>=`, `<`, `<=`) are not defined for binary
values; a predicate that uses a binary literal with an ordering operator MUST
produce a parse error.

`IN` and `NOT_IN` take a non-empty parenthesized, comma-separated list of literals:

```text
WHERE origin IN ("loregd", "peinit")
WHERE origin_class NOT_IN (kacs, lcs)
```

A field that is absent from an event payload or metric label set resolves to NULL. Comparisons against NULL or absent fields evaluate false except for `IS NULL`, which evaluates true, and `IS NOT NULL`, which evaluates false.

## Logical operators

Predicates within a single WHERE clause may be combined with `AND` and `OR`. Parentheses control precedence. `AND` binds tighter than `OR`.

Multiple WHERE clauses are logically ANDed. Each WHERE clause is treated as a parenthesized group: `WHERE a == 1 OR b == 2` followed by `WHERE c == 3` is equivalent to `WHERE (a == 1 OR b == 2) AND c == 3`.

## Sorting

SORT orders results by one or more query-language fields. The default direction
for each SORT field is ascending. `ASC` may be written explicitly; `DESC`
reverses that field's order.

```text
SORT timestamp DESC
SORT origin ASC, timestamp DESC
```

All result ordering MUST be total and deterministic so that `SKIP` and `TAKE`
are stable for a fixed database snapshot. If explicit SORT keys do not uniquely
order two records, eventd appends internal mode-specific tiebreakers:

- Events: `timestamp DESC`, shard index ascending, `events.id DESC`.
- Logs: `timestamp DESC`, `logs.id DESC`.
- Metrics: `timestamp ASC`, metric name ascending, canonical labels ascending,
  and `samples.id ASC` when the result row corresponds to a raw sample or
  derived sample pair.

Internal tiebreakers are not query-language fields and are not emitted in result
records. The event shard index is the numeric shard identifier from the
`shard-NNNN.db` filename.

### Sort value ordering

SORT uses query-language value ordering, not SQLite's native dynamic-type
ordering. Missing fields and explicit NULL values are equivalent for sorting.
For ascending order, values sort by type in this order:

1. NULL
2. Boolean (`false` before `true`)
3. Numeric (integers and floats compared numerically)
4. String and GUID (ASCII-only case-folded comparison)
5. Binary (unsigned lexicographic byte ordering)
6. Array

Descending order reverses the complete ordering, including type order.

Strings and GUIDs compare using the same ASCII-only case folding as string
predicates. If two strings compare equal under ASCII-only case folding, their
original UTF-8 byte sequences are used as a deterministic tiebreaker. Binary
values compare using unsigned lexicographic byte ordering. Arrays compare by
the canonical msgpack byte encoding of the array value. Msgpack maps are
containers for event payload flattening and MUST NOT appear as top-level
sortable result values in event records.

## Grouping and distinct values

`COUNT BY`, `TOP N BY`, `GROUP`, and `DISTINCT` use query-language value
equality, not SQLite's native dynamic-type equality. Missing fields and explicit
NULL values are one group. Integers and floats that compare numerically equal
are one group. Strings and GUIDs group using ASCII-only case folding. Binary
values group by exact byte equality.

When a group key has multiple concrete values that are equal under
query-language equality but not byte-identical (for example `"Loregd"` and
`"loregd"`, or integer `1` and float `1.0`), the value emitted in the result is
the canonical representative for the group:

- For NULL, emit msgpack nil.
- For boolean, emit the boolean value.
- For numeric groups, emit an integer if all contributing numeric values are
  integers; otherwise emit a float64.
- For string/GUID groups, emit the smallest original UTF-8 byte sequence among
  the contributing values after ASCII-only case-folded grouping.
- For binary groups, emit the exact binary value.
- For array groups, emit the array with the smallest canonical msgpack byte
  encoding among the contributing values.

`COUNT BY` results are ordered by `count` descending. Ties are ordered by the
group key using the SORT value ordering above, then by the canonical
representative's encoded bytes if needed. `TOP N BY` is exactly `COUNT BY` with
`TAKE N` applied after that deterministic ordering. `DISTINCT` results are
ordered by the distinct value using SORT value ordering unless an explicit SORT
clause is present.

## Field resolution

For events: known header column names (`timestamp`, `cpu_id`, `sequence`, `origin_class`, `event_type`, `effective_token_guid`, `true_token_guid`, `process_guid`, `boot_id`) resolve to columns. All other names resolve to payload field lookups via msgpack extraction.

Event header field names are reserved in the query language and in flat result maps. If an event payload contains a top-level key equal to a reserved header field name, the header field wins. The colliding payload value is stored unchanged in the raw `payload` column but is not exposed through field resolution, SELECT, WHERE, aggregation, adaptive indexing, access-control field GUIDs, or flat result maps. Event emitters SHOULD avoid payload field names that collide with event header fields.

Event payload fields are exposed through recursive dot-path flattening. eventd walks msgpack maps recursively and joins path segments with `.`. Each map key in a queryable path MUST be a msgpack string matching:

```text
[A-Za-z_][A-Za-z0-9_-]*
```

Keys that are not strings, contain `.`, or do not match this segment grammar are stored unchanged in the raw payload but are not queryable and are not emitted in flat result maps. Msgpack maps are containers; non-map values, including arrays, are emitted as the value at their flattened path. Nested maps inside arrays are not traversed. Empty maps produce no queryable field. If two payload entries produce the same flattened path, the first occurrence in msgpack map order wins and later duplicate paths are suppressed. Header-field collision suppression is applied before flattening descendants: a top-level payload key named `timestamp`, for example, suppresses that entire payload subtree from query-language exposure.

For logs: known log field names (`timestamp`, `origin`, `is_error`, `message`, `boot_id`, `job_id`) resolve to columns. Any other log field name is invalid and MUST produce a parse error. There are no payload fields.

For metrics: known metric fields (`timestamp`, `boot_id`, `name`, `type`, `value`) resolve to columns. All other names resolve to label lookups. Metric ingestion rejects labels whose keys collide with those fixed metric field names (§6.1).

## Result format

All three modes return results as arrays of flat msgpack maps. Each record is a self-describing map with field names as keys.

Event records contain header fields and non-colliding flattened payload fields
merged as top-level keys. Log records contain log columns as top-level keys. Raw
metric sample records contain the metric name, type, labels as top-level keys,
timestamp, boot_id, and value. Aggregated metric results contain the metric name,
type, and value, plus labels when the result corresponds to a specific label set.
Aggregated metric results include `boot_id` only when the query's metric sample
set is restricted to exactly one boot by a `boot_id` equality predicate; the
emitted value is that boot ID. Aggregated metric results that can include
multiple boots omit `boot_id`.

For event and log queries where SELECT is valid, only the named fields appear in
each result record.
