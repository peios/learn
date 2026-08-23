---
title: Cross-Type Filtering
description: The only correlation mechanism in the language — narrowing one data type by a condition on another, with a lookback limit and no join.
---

A cross-type filter narrows one data type by a condition on another. It
is the only correlation mechanism in the language; there is no join.

```text
EVENTS kacs.* SINCE 1h ago WHERE METRIC cpu.usage[core="0"] > 80
LOGS FROM loregd SINCE 1h ago WHERE EVENT kacs.access_denied EXISTS
METRIC cpu.usage[] SINCE 1h ago WHERE EVENT synthetic.storage_error EXISTS
EVENTS kacs.* SINCE 1h ago WHERE LOG loregd CONTAINING "error" EXISTS
```

| Form | Available in |
|---|---|
| `WHERE METRIC …` | events, logs |
| `WHERE EVENT … EXISTS` | logs, metrics |
| `WHERE LOG … EXISTS` | events, metrics |

## How it is evaluated

A collector MUST evaluate the cross-type condition **first**, producing
the set of time ranges over which it holds, and then apply those ranges
as additional timestamp bounds on the primary source.

The condition is evaluated against the referenced data's own resolution
— the metric's sample interval, or the density of matching events — and
**not** once per record of the primary source. It is computed once for
the query.

## Metric conditions

`WHERE METRIC` operates on **raw scalar samples of counter and gauge
series only**. Transform, scalar aggregation and window aggregation
keywords are not valid in one, and a condition resolving to a histogram
series MUST be rejected.

The selector MUST resolve to **zero or one** series. Zero produces no
true ranges. More than one MUST be rejected with an error asking for a
bracketed or narrower selector.

Within the effective query range, a sample's value is treated as active
over `[sample.timestamp, next_sample.timestamp)`, clipped to the range,
and the final sample stays active through the upper bound. A collector
MUST include the **latest sample before `SINCE`** as the initial state
when one exists; without it the condition would be false from the start
of every range until the first sample inside it, which for a
fifteen-second sampling interval is fifteen seconds of wrongly excluded
records. If no earlier sample exists, the condition is false until the
first in-range sample.

Samples sharing a timestamp are ordered deterministically; the earlier
ones create zero-width intervals and the last at that timestamp is the
active value.

This is interpolation of a kind, and it should be understood as such: it
assumes the condition held continuously between two samples. A metric
that crossed a threshold and crossed back between samples is invisible.

## Existence conditions

`WHERE EVENT … EXISTS` and `WHERE LOG … EXISTS` are true when at least
one matching record lies near the primary record in time. The event type
supports `*` globbing (§3.23); the log form names an origin and
optionally a `CONTAINING` text.

"Near" is a **centred half-open window** of a configured width `W`. With
`lower = floor(W / 2)` and `upper = W - lower`, the condition is true
for a primary timestamp `t` when a matching record exists with:

```text
timestamp >= t - lower
timestamp <  t + upper
```

Equivalently, a matching record at `e` contributes the true range
`[e - lower, e + upper)`. When `W` is odd the extra nanosecond falls on
the upper side, so the width is exactly `W` and never `W ± 1`.

> [!NOTE]
> §3.A gives the mainline width of the existence window and its
> adjustable range, alongside every other bound in this chapter.

## The lookback limit

A collector MUST bound how far back a cross-type filter may scan.

> [!NOTE]
> §3.A gives the mainline value and adjustable range
> for this bound and every other in this chapter.

If the effective query range exceeds the limit, a collector MUST reject
the cross-type filter with an error saying the range is too large, and
the error SHOULD suggest narrowing it with `SINCE` or `UNTIL`.

**A query with a cross-type filter and no `SINCE` MUST be rejected.** An
unbounded cross-type scan is never permitted, in any mode, at any
configured limit.

The reason is that a cross-type filter reads a second store in full
before the first query begins. Its cost is set by the *referenced*
data's density, which the client did not select and cannot see, so a
query that looks cheap can scan a hundred times more than it returns.

## Cost

A cross-type filter is efficient when it is selective — narrow true
ranges eliminating most of the primary source — and expensive when it is
broadly true, which is the case where it also eliminates nothing. A
condition that holds across the whole range costs the full scan of both
stores and returns exactly what the query would have returned without
it.
