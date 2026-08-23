---
title: Parsing and Planning
description: The four phases between a query string and an answer, what can only fail after planning, and when payloads are decoded.
---

A query arrives as one string (PSPU §3.15). Turning it into an answer
has four phases before any data is read: parse, plan, authorize,
execute.

## Parsing

The string is parsed into a syntax tree. The parser:

1. Identifies the mode from the first token — `EVENTS`, `LOGS` or
   `METRIC`.
2. Extracts the primary selector: a type pattern, a `FROM` list, or a
   metric name with an optional label selector.
3. Collects every clause, in whatever order they appear.
4. Validates that the clauses suit the mode — `CONTAINING` only in log
   mode, `RATE` only in metric mode, `SELECT` only where a result schema
   is not fixed.

Parse errors are returned immediately, before anything is opened, read
or authorized. A malformed query costs a decode and a parse.

## What can only fail later

Some failures need data. The parser cannot know whether a metric name
resolves to a counter or a histogram, how many series a selector
matches, or whether the effective range exceeds the cross-type lookback
limit — those depend on the store, so they surface at planning or
execution time (PSPU §3.B).

The practical consequence is that the same query string can parse
everywhere and fail on one machine: a metric selector matching one
series on a two-core box matches two on a four-core one.

## Planning

Planning resolves what the query will actually touch:

- which concrete identifiers the data could carry — event types, log
  origins, metric names — because access control resolves per identifier
  and a broad selector authorizes nothing by itself (§7.4)
- which series a metric selector matches, and whether they are
  type-homogeneous
- which fields the query references, for both authorization and
  frequency accounting (§6.5)
- which stores are involved, including any cross-type source

The identifier discovery step is the expensive one and its cost is not
bounded by the query. `EVENTS SINCE 30d ago` with no type pattern has to
establish every distinct event type in that range before it can
authorize anything, and whether that is an index scan or a table scan
depends on whether `event_type` currently has an index — which is an
adaptive decision that pressure may have reversed (§3.4).

## When payloads are decoded

Event payloads are stored as opaque MessagePack and are never decoded on
the write path (§3.1). Decoding happens here, on the read path, and only
where a query needs it: to evaluate a payload predicate, to build a flat
result record, or to compute a payload expression index's key on insert.

At high result counts this dominates the query path. Constructing flat
maps from thousands of events means decoding thousands of payloads and
applying the flattening rules of PSPU §3.22 to each. Partial extraction
is the lever: with a `SELECT` present, only the named paths need
decoding, and without one a streaming decoder that emits flattened pairs
avoids materialising the payload at all (§C).

## Read connections

Execution uses read-only SQLite connections, which in WAL mode do not
block writer threads.

An event query opens one connection per shard database in the directory
(§6.4). A log or metric query opens one. eventd supports concurrent
queries up to its admission limit (§6.5), subject to the operating
system actually having the descriptors and memory; where it cannot
allocate what an admitted query needs, it fails that query rather than
blocking a writer or exceeding the limit.
