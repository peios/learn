---
title: Ordering, Grouping and Distinct
description: "SORT, GROUP and DISTINCT — and the two rules that make paging a query safe: one query, one order."
---

Two rules govern this article, and both exist for the same reason.

**Ordering MUST be total and deterministic.** For a fixed set of stored
records, one query MUST produce one order. Without that, `SKIP` and
`TAKE` are meaningless: a client paging through results would see
records twice and never see others, and would have no way to tell.

**Equality here MUST be the query language's, not the storage
engine's.** A collector that grouped by whatever its database considers
equal would group differently depending on how it was built.

## SORT

`SORT` orders by one or more fields. Each defaults to ascending; `ASC`
may be written, `DESC` reverses that field.

```text
SORT timestamp DESC
SORT origin ASC, timestamp DESC
```

If the named fields do not uniquely order two records, a collector MUST
append internal tiebreakers until the order is total. The tiebreakers
are not query-language fields, are never emitted in a result record, and
a client MUST NOT depend on their identity — only on their effect, which
is that the order is stable.

When no `SORT` is present:

- **Events and logs** are ordered by timestamp descending, most recent
  first — the order a person reading a log wants.
- **Metrics** are ordered by timestamp ascending, the order a chart
  wants.

## Value ordering

`SORT` uses the query language's ordering, not the storage engine's.
Missing fields and explicit nulls are equivalent. Ascending order sorts
by type first, in this order:

1. Null
2. Boolean, `false` before `true`
3. Numeric, integers and floats compared mathematically (§3.20)
4. String and GUID, ASCII-folded
5. Binary, unsigned lexicographic
6. Array

`DESC` reverses the whole ordering, type order included.

Strings and GUIDs compare with the same ASCII folding as predicates. Two
strings equal under folding are ordered by their original UTF-8 bytes,
so that folding never costs totality. Binary values compare as unsigned
bytes. Arrays compare by their canonical MessagePack encoding (§3.5).

Maps do not appear as result values (§3.17) and MUST NOT appear as sort
keys.

## Grouping

`COUNT BY`, `TOP N BY`, `GROUP` and `DISTINCT` use query-language
equality:

- missing and null are one group
- integers and floats that are numerically equal are one group
- strings and GUIDs group under ASCII folding
- binary values group by exact bytes

## The canonical representative

When a group's members are equal under those rules but not
byte-identical — `"Loregd"` and `"loregd"`, or `1` and `1.0` — the value
emitted for the group MUST be its **canonical representative**:

| Group | Representative |
|---|---|
| Null | nil |
| Boolean | the boolean |
| Numeric | an integer if every contributing value was an integer; otherwise a `float64` |
| String or GUID | the smallest original UTF-8 byte sequence among the members |
| Binary | the exact value |
| Array | the member with the smallest canonical MessagePack encoding |

Choosing the smallest rather than the first makes the representative a
property of the *set*, independent of the order records were read in —
which matters because a collector may read them from several places at
once and merge (eventd TRMP §6.4).

## Ordering of aggregates

`COUNT BY` results are ordered by `count` descending. Ties are broken by
the group key under the value ordering above, then by the
representative's encoded bytes.

`TOP N BY` is exactly `COUNT BY` with `TAKE N` applied after that
ordering.

`DISTINCT` results are ordered by the distinct value under the value
ordering, unless an explicit `SORT` overrides it.
