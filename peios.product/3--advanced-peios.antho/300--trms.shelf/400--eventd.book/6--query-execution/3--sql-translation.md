---
title: SQL Translation
description: What the query language translates to directly, what does not translate, where access control sits, and how aggregation is handled.
---

Events and logs are translated to SQL. Metrics are translated to SQL
against `series` and `samples`. Clients never see any of it — the
translation is entirely internal and carries no guarantees.

## What translates directly

**Event header fields** are columns, so a predicate on `event_type`,
`process_guid` or `cpu_id` becomes a SQL `WHERE` comparison over an
indexable column (§3.1).

**Log fields** are all columns; log mode has no payload and its field
set is closed (§4.2).

**Metric selection** resolves names and labels through `series` — from
the in-memory cache where possible — and reads `samples` for the range,
ordered by the composite index that already provides `(timestamp, id)`
(§5.2).

## What does not

**Event payload predicates** have no column. They become eventd-internal
payload extraction predicates, and may use an adaptive payload
expression index to narrow candidates (§3.4).

The rule governing every such translation is that **SQL narrows, the
query language decides**. Where a SQL construct cannot reproduce a
predicate's comparison semantics exactly, eventd uses it only to reduce
the candidate set and then applies the real predicate after loading the
row.

SQLite's native dynamic-type equality and ordering never substitute for
the query language's ASCII case folding, exact numeric comparison,
binary comparison, array comparison, or null and missing-field handling
(§6.2). An index that returns a smaller set faster is useful; one that
returns a *different* set is a wrong answer arriving quickly.

## Where access control sits

Access filtering is part of the logical execution, not a filter over the
output (PSPU §3.18, §3.28). eventd may push authorization predicates
down into SQL when the concrete identifier set is known at planning
time, or read candidate rows and discard them before aggregating.

Which it does is a performance decision. What is fixed is that the
externally visible result is identical to the one filtering-first would
produce — aggregates, ordering and pagination included, since all three
would otherwise leak the existence of rows the caller cannot read.

## Aggregation

Aggregation is pushed into SQL wherever the storage engine can express
it, which is most of the time for simple grouping over columns and none
of the time for grouping over payload paths whose comparison semantics
SQL cannot reproduce.

For an event query the push-down matters twice over, because it also
determines what crosses the shard boundary (§6.4): a shard returning
per-group partial aggregates sends a result proportional to the group
cardinality, where a shard returning rows sends a result proportional to
the row count.
