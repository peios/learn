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

The combination of `name` and `labels` MUST be unique. The `label_hash` accelerates lookup but is not a uniqueness constraint -- collisions are resolved by comparing the full `labels` string.

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
3. Look up the `series` table by `name` and `label_hash`.
4. If a match is found, verify the full `labels` string matches (hash collision check). Use the existing `series_id`.
5. If no match is found, insert a new row into the `series` table and use the new `series_id`.

Series resolution MUST be cached in memory for the lifetime of the eventd process. The series table is expected to be small (thousands to tens of thousands of time series on a typical system). After initial population, series resolution is a hash table lookup with no SQLite query on the hot path.

## Schema versioning

The metric store database MUST contain a `metadata` table with the same structure as the event and log stores. The `schema_version` for the metric store is `1`.
