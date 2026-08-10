---
title: Schema
---

## Storage model

The metric store uses a single SQLite database. Unlike event and log storage which store individual records as rows, the metric store is organised around time series. A time series is identified by metric name, labels, and (for histograms) bucket boundaries. Individual data points (samples) are appended to their time series over time.

## Series table

The `series` table maintains the registry of known time series:

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Series identifier. Auto-assigned. Used as a foreign key in the samples table. |
| `name` | TEXT NOT NULL | Metric name (e.g., `cpu.usage`). |
| `labels` | TEXT NOT NULL | Canonical label representation. Labels are sorted by key using unsigned UTF-8 byte order and encoded as a comma-separated `key=value` string (e.g., `core=0,host=server1`). The empty string represents no labels. |
| `type` | INTEGER NOT NULL | Metric type: 0 = counter, 1 = gauge, 2 = histogram. |
| `label_hash` | INTEGER NOT NULL | Hash of the canonical label string. Used for fast lookup. |
| `boundaries_hash` | INTEGER | Hash of the canonical bucket boundary representation. NULL for counter and gauge series. Non-NULL for histogram series. |
| `boundaries` | BLOB | Canonical bucket boundary representation. NULL for counter and gauge series. Non-NULL for histogram series. |

The table MUST have a `UNIQUE(name, labels, boundaries_hash)` constraint. For counter and gauge series, `boundaries_hash` is NULL and uniqueness is enforced by the application-level single-writer series resolution logic before insertion, because SQLite treats NULL values as distinct for UNIQUE constraints. The `type` column is immutable metadata for the resolved series, not part of the series identity. A later record with the same identity but a different type MUST be dropped silently.

The `label_hash` and `boundaries_hash` columns accelerate lookups but are not
sufficient by themselves to prove identity -- label hash collisions are resolved
by comparing the full `labels` string, and boundary hash collisions are resolved
by comparing the `boundaries` blob. Hashes use 64-bit FNV-1a over the exact
bytes of the canonical label string or boundary blob, with offset basis
`0xcbf29ce484222325` and prime `0x100000001b3`. After hashing, eventd clears
the high bit before storage (`hash & 0x7fff_ffff_ffff_ffff`) so the value always
fits in SQLite's signed `INTEGER` range. Lookups MUST always verify against the
full string/blob after hash narrowing.

The `boundaries` blob is a fixed binary representation, not msgpack. It is encoded as:

1. `boundary_count`: u32 little-endian.
2. `boundary_count` IEEE-754 f64 values, each encoded as its little-endian 8-byte representation, in the validated sender-provided order.

This representation exists only to identify histogram series and resolve `boundaries_hash` collisions. It is not returned in normal metric query results.

> [!INFORMATIVE]
> The UNIQUE constraint is enforced by SQLite as a defensive measure; the
> single-writer design prevents duplicates at the application level, but the
> constraint protects against future changes that introduce additional write
> paths.

## Samples table

The `samples` table stores individual data points:

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Internal sample row identifier. Used as a deterministic tiebreaker for samples with the same `series_id` and `timestamp`. |
| `series_id` | INTEGER NOT NULL | Foreign key referencing `series(id)`. |
| `boot_id` | BLOB NOT NULL | 16-byte boot ID GUID in PSD-002 binary format identifying which boot produced this sample. |
| `timestamp` | INTEGER NOT NULL | Wall clock time in nanoseconds since Unix epoch. |
| `value` | REAL NOT NULL | The numeric value. For counters and gauges, this is the raw value. For histograms, this column stores 0 and the histogram data is stored in `histogram_data`. |
| `histogram_data` | BLOB | Canonical msgpack-encoded histogram sample map. NULL for counter and gauge samples. |

For histogram samples, `histogram_data` MUST be a canonical msgpack map with
exactly these keys:

| Field | Type | Description |
|---|---|---|
| `boundaries` | array of float64 | Validated bucket boundaries in sender-provided order. |
| `counts` | array of unsigned integer | Validated cumulative bucket counts. |
| `total_count` | unsigned integer | Total number of observations. |
| `sum` | float64 | Finite sum of observed values. |

The boot ID is recorded per sample for tracking and filtering. It is not part of the series identity: a time series remains continuous across boot boundaries unless the query filters by `boot_id`.

Metric samples MAY arrive out of timestamp order. Query execution order within a
series is always `(timestamp, id)` ascending, not insertion order alone.
Duplicate timestamps are allowed; `id` provides a stable order among duplicates.
The `id` column is internal and MUST NOT be exposed as a metric query field,
metric result field, access-control field, or reserved label key.

## Rollups table

The metric store database MUST contain a `rollups` table as defined in §7.4. Rollups are boot-agnostic scalar aggregates and do not carry `boot_id`. Queries that filter metric samples by `boot_id` MUST NOT be served from rollups.

## Write-time indexes

At database creation, eventd MUST create the following indexes:

- `idx_samples_series_timestamp` on `samples(series_id, timestamp, id)` -- the primary query pattern is "give me samples for series X in time range Y in deterministic order." This composite index supports series lookup, time range filtering, and `(timestamp, id)` ordering in a single index scan.
- `idx_series_name` on `series(name)` -- required for metric name lookups.
- `idx_series_label_hash` on `series(label_hash)` -- required for fast series resolution when ingesting data points.
- `idx_rollups_series_function_window` on `rollups(series_id, function, window_seconds, window_start)` -- required for efficient rollup lookups.

## Series resolution

When a data point arrives, eventd MUST resolve it to a series ID:

1. Compute the canonical label string by sorting labels by key using unsigned
   UTF-8 byte order, encoding each pair as `key=value`, and joining pairs with
   comma. The empty label set is encoded as the empty string. Label keys and
   values cannot contain `=` or `,`, so no escaping is performed.
2. Hash the canonical label string.
3. For histogram samples, compute the canonical boundary blob and its boundaries hash from the validated sender-provided boundary order. eventd MUST NOT sort bucket boundaries. For counter and gauge samples, the boundaries blob and boundaries hash are NULL.
4. Look up the `series` table by `name`, `label_hash`, and (for histograms) `boundaries_hash`.
5. If a match is found, verify the full `labels` string matches (hash collision check), and for histograms verify the full boundary blob matches. If the record's type differs from the existing series type, drop the record silently. Otherwise use the existing `series_id`.
6. If no match is found, insert a new row into the `series` table and use the new `series_id`.

For histogram series, a change in bucket boundaries results in a new series row, as required by §6.1. The old series remains in the database with its historical samples. The new series begins accumulating samples with the new boundaries.

Series resolution MUST be cached in a bounded in-memory cache. The cache maps (name, canonical labels, boundaries hash, boundaries blob) to series_id. For counter and gauge series, the boundaries components are absent. Cache hits resolve in a hash table lookup with no SQLite query. Cache misses fall back to a SQLite SELECT by `name` and `label_hash`, then the result is inserted into the cache (evicting the least recently used entry if the cache is full).

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| MetricSeriesCacheSize | REG_DWORD | 50000 | 1000--1000000 | Maximum number of entries in the series resolution cache. |

The cache uses a least-recently-used (LRU) eviction policy. Series that receive frequent samples stay cached. Series that are rarely updated are evicted and resolved via SQLite on their next sample. A cache miss costs one SQLite SELECT -- fast with the existing `idx_series_name` and `idx_series_label_hash` indexes, but slower than a hash table hit.

The cache bounds memory usage regardless of how many distinct series exist in the database. A system with 1 million series but a 50K cache uses memory proportional to the cache size, not the series count. At typical entry sizes (~200-300 bytes), the default 50K cache uses approximately 10-15 MB.

> [!INFORMATIVE]
> Histogram bucket boundary changes create new series rows. An emitter that drifts its boundaries frequently (e.g., an auto-tuning histogram that adjusts buckets every collection cycle) will create a new series per boundary set, causing series table growth and cache churn. This is a misconfiguration -- emitters SHOULD use fixed boundaries for a given metric. eventd does not defend against this; the series table and cache behave correctly, but the proliferation of near-identical series degrades query performance and wastes storage.

The total number of distinct series in the `series` table is not capped. New series are always created in the database. The cache only bounds how many are held in memory simultaneously.

> [!INFORMATIVE]
> `MetricSeriesCacheSize` SHOULD be configured above the number of actively reporting series. If the cache is smaller than the active set, every collection cycle evicts and reloads the overflow, causing a fixed number of SQLite SELECTs per cycle permanently. For example, 55K active series with a 50K cache incurs ~5K cache misses every 15 seconds indefinitely. LRU cannot help when all series are equally hot.

## Schema versioning

The metric store database MUST contain a `metadata` table with the same structure as the event and log stores. The `schema_version` for the metric store is `1`. Schema version 1 includes the `series`, `samples`, `rollups`, and `metadata` tables. eventd MUST check the schema version on startup and apply the lifecycle rules in §7.2. Migration is a separate administrative operation, not an automatic startup behavior.
