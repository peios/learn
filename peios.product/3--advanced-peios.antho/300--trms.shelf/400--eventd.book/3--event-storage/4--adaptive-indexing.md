---
title: Adaptive Indexing
description: Which secondary indexes are worth their write cost depends on what a deployment queries — how eventd decides, converges and sheds.
---

Secondary indexes make queries fast and writes slow. Which indexes are
worth that trade depends on what a particular deployment actually
queries, which varies between systems and over time, and which nobody
wants to tune by hand.

eventd observes the queries and maintains the indexes they imply —
subject throughout to the rule that **throughput outranks query
latency**.

## Three decoupled parts

**Query frequency counters.** Query handlers increment a per-field
counter when a field appears in a `WHERE` predicate. This is the
write-heavy path — once per query, per predicate. Counters live in
memory and are flushed periodically to the metadata database (§3.5),
never to a shard, because they are global state that must survive shard
reconfiguration.

**Index policy.** A periodic process reads the counters, applies the
creation and removal thresholds, and computes the **desired index set**
— an ordered list of fields, highest priority first. It runs every
`AdaptiveIndexPolicyIntervalMinutes` (§A), and it is the only writer to
the desired set.

**Shard convergence.** Writer threads read the desired set and move
their material indexes toward it. They never read the counters and never
write the desired set.

The separation exists so that the high-frequency counter updates never
contend with the writer threads. The policy is the bridge between them
and runs on the order of once an hour, so it is never a contention
point.

The desired set is **global** — one list applying to every shard.
Individual shards do not make independent decisions; they differ only in
how far they have got.

## Convergence

A shard converges when it is quiet. When a writer thread has no pending
events and its material indexes do not match the desired set, it takes
**one** convergence action — creating the highest-priority missing
index, or dropping the lowest-priority material index no longer wanted —
then rechecks write pressure before considering another.

Creation uses `CREATE INDEX IF NOT EXISTS`; removal uses
`DROP INDEX IF EXISTS`. Both run on the shard's writer thread, which is
the only thread permitted to write that database (§2.3).

**Index creation is cancellable.** If drain threads detect rising write
pressure during a build, they signal the writer to abort; the writer
cancels the `CREATE INDEX`, SQLite rolls back the partial index cleanly,
and the writer returns to event batches immediately. The abandoned build
is retried at the next quiet period.

Cancellation responsiveness matters more than it looks. `sqlite3_interrupt`
sets a flag checked at SQL VM opcode boundaries, and during B-tree
construction for a large index the gap between checks can be tens of
milliseconds — long enough to overrun a ring buffer at a high event
rate. `sqlite3_progress_handler()`, registering a callback invoked every
thousand opcodes that checks a cancellation flag and returns non-zero to
abort, gives cancellation that tracks the pressure signal rather than
lagging it.

Shards converge at their own pace. One under sustained pressure may lag
the desired set indefinitely, and that is the correct outcome: it is
prioritising throughput.

## Shedding

Under sustained pressure a shard drops indexes to cut per-insert cost.

**Graduated shedding.** If more than `SheddingBatchPercent` of a shard's
batches within a `SheddingWindowSeconds` sliding window exceeded 75% of
`MaxBatchSize`, the shard drops its lowest-priority secondary index —
the one whose column has the lowest query frequency in the desired set.
If pressure persists, the next-lowest goes, and so on. The check runs
once per batch commit.

**Emergency shedding.** If a shard is at maximum batch size and its
drain thread signals rising ring buffer pressure, it drops **all**
secondary indexes at once. `DROP INDEX` is a metadata operation
measured in milliseconds, so it is safe to do under pressure in a way
that creation is not.

The pressure signal comes from the drain thread watching the gap between
`write_pos` and its own `read_pos`. Exceeding
`EmergencySheddingBufferPercent` of ring buffer capacity raises it. It
is a distinct signal from the index-build cancellation one: this
triggers shedding whether or not a build is in progress.

`idx_events_timestamp` is **exempt**. It is never shed at any pressure,
because time-range queries are the access pattern everything else is
built on and the store is unusable without it.

When pressure subsides, shedding reverses: the shard rebuilds toward the
desired set under the same quiet-period scheduling and the same
cancellability, highest priority first.

## Candidates

Any field that can appear in a `WHERE` predicate is a candidate.

**Header columns.** `event_type`, `origin_class`, `cpu_id`,
`effective_token_guid`, `true_token_guid`, `process_guid`, `boot_id`.
`timestamp` is always indexed and is not adaptively managed.

**Payload fields.** Any queryable flattened path that appears in a
predicate is a candidate for an expression index. A path suppressed by
the flattening rules of PSPU §3.22 — a top-level key colliding with a
header field, a key that is not a valid segment, a duplicate path —
never receives one, because it is not a query-language field at all.

The raw `payload` column never receives a plain column index. Indexing
an opaque blob accelerates nothing.

## Payload indexes are an optimisation, not an authority

An expression index extracts a field from the payload on every insert
and indexes a deterministic private key for it. The exact key bytes are
internal to eventd and are not part of the storage contract.

eventd may implement these as SQLite expression indexes with
deterministic extraction functions, as generated columns, or by any
equivalent SQLite-backed means. What every mechanism has in common is
that it implements the same field resolution and flattening as
PSPU §3.22 — and that where the index cannot reproduce the query
language's comparison semantics exactly, it is used only to **narrow
candidate rows**, with the real predicate applied after the row is
loaded (§6.3).

SQLite's native dynamic-type equality and ordering never substitute for
the query language's string case folding, numeric comparison, binary
comparison, array comparison, or null and missing-field handling.
Getting a smaller answer faster is worthless if it is a different
answer.

Rows where the field is absent, unqueryable or suppressed index as null,
or are otherwise excluded in a way that preserves those semantics.

Payload indexes are otherwise ordinary members of the desired set, with
the same priority ordering, shedding and convergence.

## Naming

Header column indexes are `idx_events_<column>` —
`idx_events_event_type`, `idx_events_process_guid`.

Payload expression indexes are named from the field GUID (§7.3), to
avoid both collisions and characters SQLite will not accept in an
identifier:

```text
idx_events_payload_<field_guid_hex>
```

where `field_guid_hex` is the UUID v5 field GUID for the flattened path,
as 32 lowercase hexadecimal digits with braces and hyphens stripped. The
path `source.name` yields
`idx_events_payload_` followed by the 32 hex digits of
`uuid_v5(EVENTD_FIELD_NAMESPACE, "source.name")`.

Deriving the name from the GUID rather than from the path means the same
path always produces the same index name, and no path — however it is
spelled — can produce a name that collides with another's or that
SQLite rejects.
