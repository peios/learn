---
title: Series Resolution
description: Turning each arriving sample into a series_id once, on the single ingestion thread — the cache, and how to size it.
---

Every arriving sample must be turned into a `series_id` before it can be
inserted. This happens once per sample on the single metric ingestion
thread, so it is the hottest lookup in the daemon and the reason a cache
exists at all.

## Resolving

1. Compute the canonical label string: sort by key in unsigned UTF-8
   byte order, encode each pair `key=value`, join with commas. The empty
   label set encodes as the empty string. No escaping — ingestion has
   already rejected the delimiters (§5.2).
2. Hash it.
3. For a histogram, compute the canonical boundary blob and its hash
   from the **validated, producer-supplied order**. eventd never sorts
   boundaries. For counters and gauges both are null.
4. Look up `series` by `name`, `label_hash`, and for histograms
   `boundaries_hash`.
5. On a match, verify the full `labels` string, and for histograms the
   full boundary blob. If the record's type differs from the existing
   series' type, drop the record (§5.1). Otherwise use the existing
   `series_id`.
6. On no match, insert a new `series` row and use the new identifier.

A histogram whose boundaries changed takes step 6: it is a new series
(PSPU §3.13). The old one keeps its historical samples and the new one
starts accumulating.

## The cache

Resolution runs through a bounded in-memory cache mapping
`(name, canonical labels, boundaries hash, boundaries blob)` to
`series_id`. For counters and gauges the boundary components are absent.

A hit is a hash table lookup with no SQLite involvement. A miss costs
one `SELECT` on `name` and `label_hash`, after which the result is
inserted, evicting the least recently used entry if the cache is full.

The bound is `MetricSeriesCacheSize` (§A), default 50000, with LRU
eviction. It bounds **memory**, not the number of series: the `series`
table is uncapped and a new series is always created in the database.
A system with a million series and a 50000-entry cache uses memory
proportional to the cache, and at roughly 200 to 300 bytes an entry the
default costs 10 to 15 MB.

The cache starts empty after a restart and is warmed on demand — within
one collection cycle, typically fifteen seconds, every active series is
cached. There is no pre-warming pass, because reading a million-row
`series` table at startup to populate a 50000-entry cache would be work
spent to discard most of its result.

## Sizing it

The cache is sized for the set of actively reporting series, and
behaves badly below it.

Below that, LRU does not help, because every series is equally hot: each
collection cycle evicts the overflow and reloads it, producing a fixed
number of `SELECT`s every cycle, permanently. A system with 55000 active
series and a 50000-entry cache incurs about 5000 cache misses every
fifteen seconds, indefinitely.

This interacts badly with label cardinality (PSPU §3.10). Labels with
unbounded values — request identifiers, user-supplied strings — grow the
series table without limit, and once the active set exceeds the cache
every cycle pays the eviction cost on the one thread that also drains
the metric socket. The failure presents as metric loss, because the
thread stops reading while it queries.

eventd does not defend against this and cannot: at the interface, a
producer creating a genuinely new series is indistinguishable from one
creating garbage, and every available defence would break a correct
producer to inconvenience an incorrect one (PSPU §3.13).
