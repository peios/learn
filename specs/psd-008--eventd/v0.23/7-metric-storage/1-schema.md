---
title: Schema
---

## Storage model

The metric store uses a single SQLite database. Unlike event and log storage which store individual records as rows, the metric store is organised around time series. A time series is a unique combination of metric name, labels, and type. Individual data points (samples) are appended to their time series over time.

## Series table

The `series` table maintains the registry of known time series:

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Series identifier. Auto-assigned. Used as a foreign key in the samples table. |
| `name` | TEXT NOT NULL | Metric name (e.g., `cpu.usage`). |
| `labels` | TEXT NOT NULL | Canonical label representation. Labels are sorted by key and encoded as a comma-separated `key=value` string (e.g., `core=0,host=server1`). The empty string represents no labels. |
| `type` | INTEGER NOT NULL | Metric type: 0 = counter, 1 = gauge, 2 = histogram. |
| `label_hash` | INTEGER NOT NULL | Hash of the canonical label string. Used for fast lookup. |
| `boundaries_hash` | INTEGER | Hash of the canonical bucket boundary representation. NULL for counter and gauge series. Non-NULL for histogram series. |

The table MUST have a `UNIQUE(name, labels, boundaries_hash)` constraint. For counter and gauge series, `boundaries_hash` is NULL and the uniqueness is effectively `(name, labels)` since all NULLs are distinct in SQLite — the application-level single-writer design prevents duplicates, and the series resolution logic (below) enforces uniqueness before insertion. The `label_hash` and `boundaries_hash` columns accelerate lookups but are not uniqueness constraints -- collisions are resolved by comparing the full `labels` string. The hash algorithm is implementation-defined. Lookups MUST always verify against the full string after hash narrowing. Hash values are not portable across implementations -- a database restored from backup on a different implementation will produce correct results (hash misses fall through to full string comparison) but may have degraded lookup performance until series are re-inserted.

> [!INFORMATIVE]
> FNV-1a (32-bit or 64-bit) is a good default choice for `label_hash` and `boundaries_hash`. It is simple, fast, well-distributed for short strings, and has no external dependencies. The UNIQUE constraint is enforced by SQLite as a defensive measure; the single-writer design prevents duplicates at the application level, but the constraint protects against future changes that introduce additional write paths.

## Samples table

The `samples` table stores individual data points:

| Column | Type | Description |
|---|---|---|
| `series_id` | INTEGER NOT NULL | Foreign key referencing `series(id)`. |
| `timestamp` | INTEGER NOT NULL | Wall clock time in nanoseconds since Unix epoch. |
| `value` | REAL NOT NULL | The numeric value. For counters and gauges, this is the raw value. For histograms, this column stores 0 and the histogram data is stored in `histogram_data`. |
| `histogram_data` | BLOB | Msgpack-encoded histogram value (boundaries, counts, total_count, sum). NULL for counter and gauge samples. |

## Write-time indexes

At database creation, eventd MUST create the following indexes:

- `idx_samples_series_timestamp` on `samples(series_id, timestamp)` -- the primary query pattern is "give me samples for series X in time range Y." This composite index supports both series lookup and time range filtering in a single index scan.
- `idx_series_name` on `series(name)` -- required for metric name lookups.
- `idx_series_label_hash` on `series(label_hash)` -- required for fast series resolution when ingesting data points.

## Series resolution

When a data point arrives, eventd MUST resolve it to a series ID:

1. Compute the canonical label string (sort labels by key, encode as `key=value` pairs).
2. Hash the canonical label string.
3. For histogram samples, compute the boundaries hash from the canonical boundary representation (sorted array of boundary values). For counter and gauge samples, the boundaries hash is NULL.
4. Look up the `series` table by `name`, `label_hash`, and (for histograms) `boundaries_hash`.
5. If a match is found, verify the full `labels` string matches (hash collision check). Use the existing `series_id`.
6. If no match is found, insert a new row into the `series` table and use the new `series_id`.

For histogram series, a change in bucket boundaries results in a new series row, as required by §6.1. The old series remains in the database with its historical samples. The new series begins accumulating samples with the new boundaries.

Series resolution MUST be cached in a bounded in-memory cache. The cache maps (name, canonical labels, boundaries hash) to series_id. For counter and gauge series, the boundaries hash component is absent. Cache hits resolve in a hash table lookup with no SQLite query. Cache misses fall back to a SQLite SELECT by `name` and `label_hash`, then the result is inserted into the cache (evicting the least recently used entry if the cache is full).

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

The metric store database MUST contain a `metadata` table with the same structure as the event and log stores. The `schema_version` for the metric store is `1`.
