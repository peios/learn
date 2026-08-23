---
title: The Logs Table
description: A single database rather than a directory of shards, its schema, its write-time indexes, and why there is no adaptive indexing here.
---

The log store is a single SQLite database — not a directory of shards.
There is no sharding here: one ingestion thread produces the writes, so
splitting the target would give a single writer several files to switch
between rather than several writers working in parallel.

It holds one `logs` table.

| Column | Type | Contents |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | SQLite rowid, monotonic. |
| `boot_id` | BLOB NOT NULL | 16-byte boot ID GUID in PCDS binary layout. |
| `timestamp` | INTEGER NOT NULL | Nanoseconds since the Unix epoch — the producer's value if it supplied one, otherwise eventd's clock at receipt. |
| `origin` | TEXT NOT NULL | The producing program's name, as the producer declared it. |
| `is_error` | INTEGER NOT NULL | 1 for standard error or an explicitly marked error, 0 otherwise. |
| `message` | TEXT NOT NULL | The log text. |
| `job_id` | BLOB | 16-byte correlation GUID when the producer supplied one; null otherwise. |

The schema is deliberately narrow. A log record is text with light
metadata: what produced it, whether it was an error, when, and
optionally which execution it belongs to. There is no payload blob and
no origin class, and the only identity-like field is the optional
correlation key — which is not an identity at all, since `origin` is
self-asserted and unverified (PSPU §3.28).

A program needing more structure than this emits events.

## `is_error` is an integer here and a boolean there

The column stores 0 or 1; the query language exposes a boolean, and
accepts either `WHERE is_error == true` or `WHERE is_error == 1`
(PSPU §3.22). `ERROR ONLY` is sugar for the first.

## Write-time indexes

Three indexes are created with the table:

- `idx_logs_timestamp` on `logs(timestamp)` — time-range filtering, as
  everywhere.
- `idx_logs_origin` on `logs(origin)` — "show me logs from X", which is
  the dominant log query.
- `idx_logs_job_id` on `logs(job_id) WHERE job_id IS NOT NULL` — a
  partial index for "show me logs for job X". Partial because
  directly-submitted lines carry no correlation key, so only correlated
  lines are worth indexing.

The origin index costs write amplification beyond the timestamp index,
and the cost is modest in practice: `origin` has low cardinality, tens
of distinct names on a normal system, so its index pages stay in
SQLite's page cache and insertion stays cheap. The trade is accepted
deliberately — the two dominant log queries must not become full table
scans.

## No adaptive indexing

The log store does not participate in adaptive indexing (§3.4). Its
field set is closed and small, and the three write-time indexes already
cover the access patterns; there is no space of candidate fields for a
policy to discover.

The same follows for query frequency counters: log queries do not
increment them (§6.5).

## Schema version

The log store holds a `metadata` table with the same two-column
structure as a shard's (§3.1). Its version is in §B.

eventd checks it at startup and applies the lifecycle rules of §4.3,
and does not migrate.
