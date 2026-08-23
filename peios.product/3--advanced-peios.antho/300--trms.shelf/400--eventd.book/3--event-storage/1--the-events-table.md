---
title: The Events Table
description: One table per shard with every KMES header field as its own column, the untouched payload blob, and the write-time indexes.
---

Every shard database holds one `events` table.

| Column | Type | Contents |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | SQLite rowid, monotonic within the shard. |
| `boot_id` | BLOB NOT NULL | 16-byte boot ID GUID in PCDS binary layout. |
| `timestamp` | INTEGER NOT NULL | Nanoseconds since the Unix epoch. From the KMES header for a real event; eventd's clock at generation for a synthetic one. |
| `cpu_id` | INTEGER | From the KMES header. Null for daemon-wide synthetic events; populated for gap records (§2.5). |
| `sequence` | INTEGER | Per-CPU, per-boot sequence from the KMES header. Null for every synthetic event. |
| `origin_class` | INTEGER | 0 userspace, 1 KMES, 2 KACS, 3 LCS. From the header. Null for synthetic events. |
| `event_type` | TEXT NOT NULL | From the header; or a `synthetic.`-prefixed string. |
| `effective_token_guid` | BLOB | 16-byte GUID for the effective token at emission. Null for synthetic events; the null GUID when identity was unavailable at emission. |
| `true_token_guid` | BLOB | 16-byte GUID for the process's primary token. Null for synthetic events. |
| `process_guid` | BLOB | 16-byte GUID for the emitting process. Null for synthetic events. |
| `payload` | BLOB | MessagePack. For a KMES event, the raw payload bytes exactly as received. For a synthetic event, a map (§3.2). Null when the event carries none. |

## Header fields are columns

Every KMES header field is extracted into its own column rather than
left inside the payload blob. That is what lets a predicate on
`process_guid` or `event_type` become a SQL comparison rather than a
decode of every candidate row, and it is what makes those fields
indexable by ordinary column indexes (§3.4).

`event_type` is the sole discriminator between real and synthetic
records. No record-type column exists, because the `synthetic.` prefix
already partitions the type namespace and a second column would be a
second thing to keep consistent.

## The payload is not touched

For a KMES event the payload column holds the bytes KMES delivered,
unmodified. eventd does not decode them on the write path, does not
re-encode them, and does not validate them beyond what the ring-buffer
protocol already checked.

The payload is a MessagePack value whose schema belongs to the emitting
subsystem, and eventd has no catalogue of those schemas. It decodes on
the *read* path when a query needs a payload field (§6.1), which is also
the only point at which the flattening rules of PSPU §3.22 apply.

Storing the bytes verbatim is also what keeps a payload field that
collides with a header name recoverable: the value is suppressed from
the query surface but remains in the blob.

## Identity may be absent two ways

`effective_token_guid` distinguishes two cases that would otherwise
look alike. **Null** means the record is synthetic and never had an
identity. The **null GUID** — sixteen zero bytes — means the record is a
real KMES event whose identity was not available at emission time,
because it was emitted before or outside a context that had one.

The distinction matters for audit: "eventd wrote this" and "the kernel
emitted this and could not attribute it" are different facts.

## Write-time indexes

One index is created with the table:

- `idx_events_timestamp` on `events(timestamp)`

Time-range filtering is the foundational access pattern — nearly every
query carries a `SINCE` — and it is the one index eventd never sheds,
whatever the write pressure (§3.4). Every other index is the adaptive
system's business.

## Schema version

Each shard holds a `metadata` table:

| Column | Type | Contents |
|---|---|---|
| `key` | TEXT PRIMARY KEY | Metadata key. |
| `value` | TEXT NOT NULL | Metadata value. |

with two required entries: `schema_version`, and `created_at` as a UTC
timestamp formatted `YYYY-MM-DDTHH:MM:SSZ`. The current version is in
§B.

eventd checks the version at startup and applies the lifecycle rules of
§3.3. It does not migrate: an unrecognised version is a startup failure
for an active shard and an exclusion for a historical one. Migration is
an administrative operation, deliberately not an automatic one — a
daemon that silently rewrote an audit store's schema on first start
after an upgrade would be doing the one thing an audit store must not do
unattended.
