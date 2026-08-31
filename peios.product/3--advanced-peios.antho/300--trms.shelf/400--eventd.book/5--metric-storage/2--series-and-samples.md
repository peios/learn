---
title: Series and Samples
description: The metric store is organised around series rather than records — the series table, the canonical label string and the boundaries blob.
---

The metric store is a single SQLite database, and unlike the event and
log stores it is organised around **series** rather than records.
Individual samples are appended to a series that already has an
identity.

## The series table

| Column | Type | Contents |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Series identifier; the foreign key `samples` uses. |
| `name` | TEXT NOT NULL | The metric name. |
| `labels` | TEXT NOT NULL | Canonical label representation. Empty string for no labels. |
| `type` | INTEGER NOT NULL | 0 counter, 1 gauge, 2 histogram. |
| `label_hash` | INTEGER NOT NULL | Hash of the canonical label string. |
| `boundaries_hash` | INTEGER | Hash of the canonical boundary blob. Null for counters and gauges. |
| `boundaries` | BLOB | Canonical boundary blob. Null for counters and gauges. |

### The canonical label string

Labels are sorted by key in unsigned UTF-8 byte order, each pair written
`key=value`, and the pairs joined with commas: `core=0,host=server1`.
The empty label set is the empty string.

No escaping is performed and none is needed, because ingestion rejects
`=` and `,` inside a key or a value (PSPU §3.10). That prohibition
exists precisely to make this encoding unambiguous, and it is the reason
the constraint binds the producer rather than being handled internally.

### The boundaries blob

A fixed binary encoding, not MessagePack:

1. `boundary_count`, `u32` little-endian
2. that many IEEE-754 `f64` values, each little-endian, in the validated
   order the producer sent

It exists only to identify histogram series and to resolve hash
collisions, and is never returned in a query result.

### Hashes narrow, they do not decide

`label_hash` and `boundaries_hash` are 64-bit FNV-1a over the exact
bytes of the canonical string or blob, with offset basis
`0xcbf29ce484222325` and prime `0x100000001b3`. The high bit is cleared
before storage, `hash & 0x7fff_ffff_ffff_ffff`, so the value always fits
SQLite's signed `INTEGER`.

A lookup always verifies the full `labels` string, and for a histogram
the full `boundaries` blob, after narrowing by hash. A hash is an index
key, never an identity: two label sets that collide are still two
series.

### Uniqueness

The table carries `UNIQUE(name, labels, boundaries_hash)`.

For counters and gauges `boundaries_hash` is null, and SQLite treats
nulls as distinct in a unique constraint — so the constraint does not
enforce uniqueness for them. What does is the single-writer resolution
logic (§5.3), which checks before inserting. The constraint is a
defensive backstop against a future change that introduces a second
write path, not the primary mechanism.

`type` is **not** part of the identity. A record resolving to an
existing series with a different type resolves successfully and is then
dropped for the mismatch (§5.1).

## The samples table

| Column | Type | Contents |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Internal row identifier; the tiebreaker for samples sharing a series and timestamp. |
| `series_id` | INTEGER NOT NULL | References `series(id)`. |
| `boot_id` | BLOB NOT NULL | 16-byte boot ID GUID. |
| `timestamp` | INTEGER NOT NULL | Nanoseconds since the Unix epoch. |
| `value` | REAL NOT NULL | The raw value for counters and gauges. Stores 0 for histograms. |
| `histogram_data` | BLOB | Canonical MessagePack histogram sample map. Null for counters and gauges. |

For a histogram, `histogram_data` is a canonical MessagePack map
(PSPU §3.5) with exactly four keys: `boundaries`, an array of `float64`
in the producer's order; `counts`, an array of unsigned integers;
`total_count`; and `sum`, a finite `float64`.

`value` is a placeholder for histogram rows and is never returned as a
metric query value. Storing 0 rather than null keeps the column
`NOT NULL` and keeps the row layout uniform.

Canonical encoding is required here because a stored sample map must be
byte-stable: two equal histograms encode identically, which is what
makes them comparable without decoding.

`boot_id` is per sample and is not part of the series identity, so a
series stays continuous across a reboot (§3.7).

## Ordering

Query execution order within a series is always `(timestamp, id)`
ascending, never insertion order alone. Duplicate timestamps are
permitted and `id` gives them a stable order.

`id` is internal. It is never exposed as a query field, a result field,
an access-control field, or a reserved label key (PSPU §3.28).

## Write-time indexes

- `idx_samples_series_timestamp` on `samples(series_id, timestamp, id)`
  — the dominant pattern is "samples for series X over range Y in
  deterministic order", and this one composite index serves the series
  lookup, the range filter and the `(timestamp, id)` ordering in a
  single scan.
- `idx_series_name` on `series(name)` — name lookups.
- `idx_series_label_hash` on `series(label_hash)` — series resolution on
  the ingestion path.

## Schema version

A `metadata` table with the same structure as the other stores' (§3.1).
Version 1 comprises `series`, `samples` and `metadata`. Version 2 adds the
disposable `rollups` query cache (§5.6); it does not change raw series or sample
storage. The current value is in §B. eventd checks it at startup and applies the
lifecycle and migration rules of §5.4.
