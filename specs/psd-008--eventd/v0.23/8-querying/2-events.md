---
title: Event Queries
---

## Syntax

```
EVENTS [type_pattern] [clauses...]
```

The primary selector is an optional event type pattern, placed immediately after `EVENTS`. All other clauses may appear in any order.

## Type pattern

If present, the type pattern filters events by their `event_type` field. Exact match by default. The `*` wildcard matches zero or more of any character, including dots:

```
EVENTS kacs.access_denied           -- exact match
EVENTS kacs.*                       -- all event types starting with "kacs."
EVENTS synthetic.*                  -- all eventd synthetic events
EVENTS *.denied                     -- all event types ending with ".denied"
EVENTS kacs.*.denied                -- e.g., matches kacs.access.denied, kacs.token.denied
EVENTS                              -- all events (no type filter)
```

The type pattern is syntactic sugar for `WHERE event_type == "..."` (exact) or `WHERE event_type STARTS_WITH "..."` (trailing `*`). A pattern with `*` in other positions is a glob match. The only wildcard character is `*`. There are no other glob metacharacters (`?`, `[`, `{` have no special meaning). Matching is case-insensitive, consistent with all string comparisons in the query language.

## Origin class aliases

The origin class field accepts named aliases in WHERE clauses:

| Alias | Value |
|---|---|
| `userspace` | 0 |
| `kmes` | 1 |
| `kacs` | 2 |
| `lcs` | 3 |

```
EVENTS WHERE origin_class == kacs SINCE 1h ago
```

## Projection

SELECT controls which fields appear in result records. Multiple SELECT clauses are additive.

```
EVENTS kacs.* SINCE 1h ago SELECT timestamp, event_type, granted_access
EVENTS SELECT timestamp SELECT event_type    -- same as SELECT timestamp, event_type
```

If no SELECT is present, all header fields are included plus all payload fields are extracted and included as top-level keys.

## Aggregation

### COUNT BY

Counts records grouped by a field. Results are sorted by count descending.

```
EVENTS SINCE 24h ago COUNT BY event_type
-- returns: [{event_type: "kacs.access_check", count: 4523}, {event_type: "lcs.key_set", count: 891}, ...]
```

### TOP N BY

Shorthand for COUNT BY with a limit. Returns the N most frequent values.

```
EVENTS SINCE 1h ago TOP 10 BY process_guid
-- returns: [{process_guid: "...", count: 892}, {process_guid: "...", count: 445}, ...] (10 records)
```

### DISTINCT

Returns the distinct values of a field.

```
EVENTS SINCE 24h ago DISTINCT event_type
-- returns: [{event_type: "kacs.access_check"}, {event_type: "kacs.token_create"}, ...]
```

### GROUP with aggregation functions

For more complex aggregations, GROUP groups records by one or more fields, followed by an aggregation function:

```
EVENTS SINCE 1h ago GROUP origin_class COUNT
EVENTS SINCE 1h ago GROUP origin_class, event_type COUNT
```

Aggregation functions: COUNT, SUM, AVG, MIN, MAX. SUM, AVG, MIN, and MAX take a field argument:

```
EVENTS SINCE 1h ago GROUP event_type AVG some_numeric_field
```

For SUM, AVG, MIN, and MAX, records where the field is NULL or non-numeric are excluded from the aggregate. COUNT counts all records regardless of field values. If all records in a group have NULL or non-numeric values for the aggregated field, the group's aggregate value is NULL.

## Sorting

SORT orders results by one or more fields. Default direction is ascending. DESC reverses.

```
EVENTS kacs.* SINCE 1h ago SORT timestamp DESC TAKE 100
```

If no SORT is present, results are ordered by timestamp descending (most recent first).

## Manual indexing

The INDEX command adds a field to the global desired index set immediately, bypassing the adaptive frequency threshold and the policy recomputation interval. This is intended for incident response and ad-hoc investigation where waiting for the adaptive system is not acceptable.

```
EVENTS INDEX target_sid
EVENTS INDEX granted_access
```

INDEX triggers an immediate policy recomputation with the named field added at highest priority. The shard writer threads begin converging toward the updated desired set at their next quiet period. The index is subject to the same pressure-based shedding rules as any other adaptive index -- if the system is under heavy write pressure, the index may be shed.

Manually indexed fields remain in the desired set until they fall below the adaptive drop threshold over the rolling window (same as adaptively created indexes). There is no manual "unindex" command -- if the field stops being queried, the adaptive system removes it.

INDEX is an administrative operation. The caller's token is checked against an SD stored in the `eventd-meta.db` metadata database (§3.3), separate from the read-path SDs in the registry security subtree (§9.1). The default SD grants INDEX access to SYSTEM and Administrators only. This prevents unprivileged users from manipulating the indexing policy to degrade write throughput for other users.

## Examples

Last 50 events:
```
EVENTS TAKE 50
```

KACS access denied events from the last hour with specific fields:
```
EVENTS kacs.access_denied SINCE 1h ago SELECT timestamp, event_type, granted_access, target_sid
```

Events from a specific process:
```
EVENTS WHERE process_guid == "550e8400-e29b-41d4-a716-446655440000" SINCE 1d ago
```

Event type breakdown for the last 24 hours:
```
EVENTS SINCE 24h ago COUNT BY event_type
```

Top 10 noisiest processes in the last hour:
```
EVENTS SINCE 1h ago TOP 10 BY process_guid
```

Events during high CPU:
```
EVENTS kacs.* SINCE 1h ago WHERE METRIC cpu.usage > 80
```

Live tail of all KACS events:
```
EVENTS kacs.* STREAM
```
