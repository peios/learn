---
title: Comparison and Logic
description: The operators, case-folding on strings, why types never coerce, how absent fields behave, and how predicates combine.
---

## Operators

| Operator | Meaning | Operand types |
|---|---|---|
| `==` | Equal | any |
| `!=` | Not equal | any |
| `>` `>=` `<` `<=` | Ordering | integer, float, timestamp |
| `STARTS_WITH` | Prefix | string |
| `ENDS_WITH` | Suffix | string |
| `CONTAINS` | Substring | string |
| `HAS` | Array contains an element | array |
| `IN` | Member of a set | any |
| `NOT_IN` | Not a member | any |
| `IS NULL` | Absent or null | any |
| `IS NOT NULL` | Present and not null | any |

`IN` and `NOT_IN` take a non-empty parenthesised, comma-separated list
of literals. An empty list is a parse error.

```text
WHERE origin IN ("loregd", "peinit")
WHERE emitter.class NOT_IN (kacs, lcs)
```

`=` is not a comparison operator and MUST produce a parse error, with
one exception: inside a metric label selector, where `=` and `==` are
both equality (§3.25).

## HAS asks about an array

`HAS` is true when the field holds an array one of whose elements equals
the value, compared as `==` compares it, so a binary literal matches a
binary element exactly and a string element folds case.

```text
EVENTS WHERE subject.token.groups HAS x"010200000000000520000000200200"
```

A payload field MAY hold an array — a token's group SIDs are the
canonical example — and `==` against an array is whole-value equality:
an array equals only an array of the same length whose elements are
equal in order. That is what an operand of a different type compares
against, so `==` between an array field and a single element is a type
mismatch and evaluates false, exactly as §3.20's "types do not coerce"
says. `HAS` is the operator that asks the other question.

`HAS` applied to a field that is not an array evaluates **false** for
that record, for the same reason an ordering operator applied to a
non-numeric value does: a payload field's type varies from record to
record. Elements are compared one level deep — an element that is itself
an array is compared whole, not searched.

`HAS` is not a set operator and MUST NOT be confused with `IN`. `IN`
asks whether a scalar field equals one of several literals; `HAS` asks
whether one array field holds one literal. `CONTAINS` is substring
matching on a string and has nothing to do with either.

A collector MAY evaluate `HAS` by scanning: array containment need not
be indexable, and answering correctly without an index is required where
answering quickly is not.

## Strings fold case

Every string comparison — `==`, `!=`, `STARTS_WITH`, `ENDS_WITH`,
`CONTAINS`, `HAS`, `IN`, `NOT_IN` — is **case-insensitive**, using
ASCII-only folding: bytes `A`–`Z` compare equal to `a`–`z`, and every non-ASCII
byte compares exactly.

This applies uniformly: to event header fields, to payload fields, to
log messages, to metric label values, and to the pattern matching of
primary selectors. Integers, floats, GUIDs, timestamps and binary values
are unaffected.

> [!NOTE]
> Folding is ASCII-only rather than Unicode because full case folding is
> locale-dependent, version-dependent and expensive, and because the data
> it would be applied to — identifiers, service names, event types — is
> ASCII by construction (§3.19). A collector that folded Turkish dotless
> `ı` would have to fold it the same way as every other collector, for
> every Unicode version, forever.

## Numbers compare mathematically

Integers and floats compare by mathematical value, not by casting both
to one storage type.

An integer equals a finite float only when the float represents exactly
that value. Ordering between an integer and a float MUST be exact,
including for integers outside the range binary64 can represent exactly.
A collector MUST NOT resolve `9007199254740993 > 9007199254740992.0` by
converting the left operand to a float, which would make it false.

### NaN

An event payload may carry a NaN (§3.5), though a literal never can
(§3.19). Every NaN is one value: it equals every other NaN and nothing
else, so `x == 5` is false and `x != 5` is true for a record whose `x`
is a NaN.

An ordering operator with a NaN on either side evaluates **false**, as
IEEE 754 has it. `x < 5` and `x >= 5` are both false for that record.
Sorting and grouping still need a place for a NaN, and §3.21 gives it
one.

## Types do not coerce

Values of different non-numeric types are never equal. The string `"1"`
is not the integer `1`, and `!=` between them is true.

An ordering operator applied to a field whose runtime value is
non-numeric evaluates **false** for that record — not an error, because
a payload field's type varies from record to record and a query cannot
know in advance.

An ordering operator applied to a *known fixed field* whose declared
type cannot be ordered is different: a collector MUST reject the query
during parsing or planning rather than executing a predicate that can
never match. `WHERE message > 5` is a mistake the collector can see, and
returning zero records for it would be a wrong answer that looks like a
right one.

Binary values compare by exact byte equality under `==`, `!=`, `HAS`,
`IN` and `NOT_IN`. Ordering is **not defined** for binary values, and a
predicate applying an ordering operator to a binary literal MUST produce
a parse error.

## Absent fields

A field absent from an event payload or from a metric's label set
resolves to null (§3.17).

Every comparison against null evaluates false, except `IS NULL`, which
is true, and `IS NOT NULL`, which is false. In particular
`WHERE field != "x"` does **not** match records lacking the field: a
record with no opinion is not a record with a different opinion.

## Combining predicates

Predicates within one `WHERE` combine with `AND` and `OR`. `AND` binds
tighter than `OR`. Parentheses override.

Multiple `WHERE` clauses combine with `AND`, each parenthesised as a
group (§3.18).

There is no `NOT`. Negation is written with the negative operators —
`!=`, `NOT_IN`, `IS NOT NULL` — and a collector MUST reject `NOT` as a
parse error rather than silently treating it as an identifier.
