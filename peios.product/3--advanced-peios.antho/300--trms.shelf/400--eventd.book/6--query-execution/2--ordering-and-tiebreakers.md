---
title: Ordering and Tiebreakers
description: Making every result order total and deterministic so paging works — the tiebreakers, and why insertion order is never the answer.
---

PSPU §3.21 requires every result order to be total and deterministic for
a fixed set of stored records, so that `SKIP` and `TAKE` page reliably.
This is how eventd achieves it.

## The tiebreakers

Where the query's explicit `SORT` keys — or the mode's default ordering
— do not uniquely order two records, eventd appends internal keys until
the order is total:

| Mode | Appended, in order |
|---|---|
| Events | `timestamp` descending, shard index ascending, `events.id` descending |
| Logs | `timestamp` descending, `logs.id` descending |
| Metrics | `timestamp` ascending, metric name ascending, canonical labels ascending, and `samples.id` ascending where the row corresponds to a raw sample or a derived sample pair |

These are not query-language fields. They never appear in a result
record, cannot be named in a `SORT` or a `SELECT`, and have no
access-control identity (PSPU §3.28).

The **shard index** is the numeric identifier from the `shard-NNNN.db`
filename. It appears in the event tiebreaker because rowids are
per-database: two events in different shards can share a rowid, and
without the shard index the pair would be genuinely unordered.

The metric tiebreaker includes name and labels because an unbracketed
query merges several series into one output stream, where the timestamp
alone does not separate rows from different series.

## Why insertion order is never the answer

`samples.id` and `events.id` break ties within one database, but neither
is a substitute for the timestamp ordering they follow.

Metric samples may arrive out of timestamp order (§5.1), so insertion
order and time order genuinely differ. Every metric computation —
`RATE`'s consecutive pairs, rollup window membership, cross-type
interval construction — is defined over `(timestamp, id)` ascending
precisely so that a late-arriving sample lands where its timestamp says
it belongs rather than where it happened to be written.

Events are less prone to it, since a drain thread reads one ring buffer
in order, but a shard receiving from several CPUs interleaves them
arbitrarily and a clock step can invert two events from the same CPU.

## Value ordering is not SQLite's

Sorting, grouping and equality all use the query language's semantics,
never the storage engine's dynamic-type rules (PSPU §3.20, §3.21).

The divergences are not edge cases. SQLite compares an integer and a
real by converting; the query language compares them mathematically and
exactly, including beyond binary64's exact integer range. SQLite orders
text by byte; the query language folds ASCII case and then falls back to
the original bytes only to break a fold-equal tie. SQLite has its own
type-affinity ordering across storage classes; the query language fixes
its own type order, nulls first, arrays last.

Where a SQL construct cannot reproduce those semantics, eventd uses it
only to narrow candidates and applies the real comparison after loading
the row (§6.3).

## Canonical representatives

A group whose members are equal under the language's rules but not
byte-identical emits the **smallest** member rather than the first
(PSPU §3.21).

Smallest rather than first is what makes the representative a property
of the set. An event query merges results from every shard in an order
that depends on which shard answered first, so "first" would be
nondeterministic across runs of the identical query — which is exactly
the property this chapter exists to prevent.
