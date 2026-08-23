---
title: Event Queries
description: EVENTS mode — the type pattern, origin class aliases, and the aggregations available over events.
---

```text
EVENTS [type_pattern] [clauses…]
```

## The type pattern

The primary selector is an optional event type pattern, placed
immediately after `EVENTS`.

```text
EVENTS kacs.access_denied      -- exactly that type
EVENTS kacs.*                  -- every type beginning "kacs."
EVENTS *.denied                -- every type ending ".denied"
EVENTS kacs.*.denied           -- kacs.access.denied, kacs.token.denied, …
EVENTS                         -- every type
```

`*` is the **only** metacharacter, and matches zero or more of any
character, dots included. `?`, `[` and `{` have no special meaning and a
collector MUST NOT treat them as any. Matching folds case, like every
string comparison (§3.20).

A pattern with no `*` is exactly `WHERE event_type == "…"`. A pattern
whose only `*` is trailing is exactly
`WHERE event_type STARTS_WITH "…"`. Anything else is a glob.

## Origin class aliases

`origin_class` accepts named aliases as well as its integer values:

| Alias | Value |
|---|---|
| `userspace` | 0 |
| `kmes` | 1 |
| `kacs` | 2 |
| `lcs` | 3 |

```text
EVENTS WHERE origin_class == kacs SINCE 1h ago
```

These are the only aliased values in the language. A collector MUST
accept both forms and MUST treat them as identical.

## Aggregation

Grouping equality, canonical representatives and tie ordering are
defined in §3.21. Every aggregation below has a **fixed output schema**,
and rejects `SELECT` (§3.22).

### COUNT BY

Counts records grouped by one field, ordered by count descending.

```text
EVENTS SINCE 24h ago COUNT BY event_type
```

Output: `{<field>: representative, count: <unsigned integer>}`.

### TOP N BY

`COUNT BY` with a limit — the `N` most frequent values.

```text
EVENTS SINCE 1h ago TOP 10 BY process_guid
```

Output: the `COUNT BY` schema.

### DISTINCT

The distinct values of one field.

```text
EVENTS SINCE 24h ago DISTINCT event_type
```

Output: `{<field>: representative}`.

### GROUP

Groups by one or more fields, followed by an aggregation function:
`COUNT`, or `SUM`, `AVG`, `MIN`, `MAX` with a field argument.

```text
EVENTS SINCE 1h ago GROUP origin_class COUNT
EVENTS SINCE 1h ago GROUP origin_class, event_type COUNT
EVENTS SINCE 1h ago GROUP event_type AVG queue_depth
```

Output, for `GROUP a, b`:

| Query | Record |
|---|---|
| `COUNT` | `{a, b, count}` |
| `SUM x` | `{a, b, sum}` |
| `AVG x` | `{a, b, avg}` |
| `MIN x` | `{a, b, min}` |
| `MAX x` | `{a, b, max}` |

Group-key fields carry canonical representatives (§3.21).

### What is aggregated

For `SUM`, `AVG`, `MIN` and `MAX`, records whose field is null or
non-numeric are **excluded** from the aggregate — not treated as zero.
`COUNT` counts every record regardless. If no record in a group
contributes a numeric value, the group's aggregate is null and the group
is still present, because `COUNT` of it is still meaningful.

### Result types

- `COUNT` returns an unsigned integer.
- `SUM` over integers returns an integer when the exact mathematical sum
  fits in signed or unsigned 64 bits. If it does not, or if any input
  was a float, it returns a `float64`. If that would be non-finite, the
  query MUST fail with an error rather than returning an infinity.
- `AVG` returns a `float64` whenever at least one numeric value
  contributed.
- `MIN` and `MAX` return the winning value itself, under exact numeric
  comparison. When an integer and a float tie, the integer wins.

## Ordering

Without `SORT`, results are ordered by timestamp descending, ties broken
as §3.21 requires.

## INDEX

```text
EVENTS INDEX target_sid
```

`INDEX` asks the collector to prioritise a field for query
acceleration immediately, rather than waiting for it to be observed
often enough to be prioritised automatically. It exists for incident
response, where the field that suddenly matters has never been queried
before.

`INDEX` is an **administrative operation**, not a query. It returns no
records. A collector MUST check the caller's token against a Security
Descriptor governing administration of the collector — one distinct from
the read-path descriptors of §3.28 — and MUST refuse a caller that does
not hold it. A collector without such a descriptor MUST refuse `INDEX`
outright.

A collector MAY treat `INDEX` as advisory and MAY decline the request,
shed the acceleration later, or do nothing at all. It is a hint about
priority; the accelerations a collector maintains are its own business,
and a conforming collector that maintains none accepts `INDEX` and has
nothing to do.

There is no command to undo it, because there is nothing to undo: a
collector reconsiders its own accelerations continuously and the hint
decays with disuse.

> [!NOTE]
> The right to issue `INDEX` MUST NOT be the read right. Accelerating a
> field costs write throughput on every record thereafter, so `INDEX` is
> a way for a caller to degrade the system for everyone, and a caller
> permitted only to read data has not been permitted to do that.
