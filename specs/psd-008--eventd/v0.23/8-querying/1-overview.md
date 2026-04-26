---
title: Overview
---

eventd exposes a unified query language for retrieving events, logs, and metrics. The language has three modes -- one per data type -- sharing common syntax for time ranges, filtering, limiting, streaming, and cross-type correlation. Each mode has type-specific syntax that reflects the natural access patterns of that data type.

The three modes:

- **EVENTS** -- search through structured event records. Primary access by event type. Returns collections of records.
- **LOGS** -- search through service log output. Primary access by service name. Returns collections of records.
- **METRIC** -- evaluate numeric measurements. Primary access by metric name and labels. Returns values or time series.

Events and logs are record-oriented (collections you search). Metrics are value-oriented (measurements you evaluate). The syntax reflects this distinction rather than forcing all three through a single pattern.

## Common elements

The following constructs work identically across all three modes:

| Element | Syntax | Description |
|---|---|---|
| Time start | `SINCE 1h ago` | Filter to records/samples after a point in time. |
| Time end | `UNTIL 30m ago` | Optional upper bound. Defaults to now. |
| Additional filter | `WHERE field == value` | Filter by any field. |
| Cross-type filter | `WHERE METRIC name[labels] > N` | Filter by a condition on another data type. |
| Limit | `TAKE N` | Limit result count. |
| Offset | `SKIP N` | Skip first N results after sorting (pagination). Applies to both raw and aggregated results. |
| Streaming | `STREAM` | Live tail. May appear anywhere. |

All keywords are case-insensitive. Documentation uses uppercase by convention.

Clauses after the primary selector may appear in any order. Execution semantics are fixed regardless of clause order.

## Time literals

| Literal | Meaning |
|---|---|
| `Ns ago` | N seconds before now. |
| `Nm ago` | N minutes ago. |
| `Nh ago` | N hours ago. |
| `Nd ago` | N days ago. |
| `Ns hence` | N seconds after now. |
| `Nm hence` | N minutes from now. |
| `Nh hence` | N hours from now. |
| `Nd hence` | N days from now. |
| `today` | Midnight of the current day (UTC). |
| `yesterday` | Midnight of the previous day (UTC). |
| `YYYY-MM-DD` | Midnight of the specified date (UTC). |
| `YYYY-MM-DDTHH:MM:SS` | Specific time (UTC). |

## GUID literals

Standard GUID string format, with or without braces:

```
WHERE process_guid == "550e8400-e29b-41d4-a716-446655440000"
WHERE process_guid == "{550e8400-e29b-41d4-a716-446655440000}"
```

## Integer literals

Decimal and hexadecimal:

```
WHERE origin_class == 2
WHERE granted_access == 0x1F01FF
```

## Comparison operators

| Operator | Meaning | Applicable types |
|---|---|---|
| `==` | Equals | All |
| `!=` | Not equals | All |
| `>` | Greater than | Integer, float, timestamp |
| `>=` | Greater than or equal | Integer, float, timestamp |
| `<` | Less than | Integer, float, timestamp |
| `<=` | Less than or equal | Integer, float, timestamp |
| `STARTS_WITH` | String prefix match | String |
| `ENDS_WITH` | String suffix match | String |
| `CONTAINS` | Substring match | String |
| `IN` | Value is in a set | All |
| `NOT_IN` | Value is not in a set | All |
| `IS NULL` | Value is NULL | Any |
| `IS NOT NULL` | Value is not NULL | Any |

All string comparisons (`==`, `!=`, `STARTS_WITH`, `ENDS_WITH`, `CONTAINS`, `IN`, `NOT_IN`) are case-insensitive by default. This applies to event fields, payload fields, log messages, and metric labels. Integer, float, GUID, and timestamp comparisons are unaffected.

## Logical operators

Predicates within a single WHERE clause may be combined with `AND` and `OR`. Parentheses control precedence. `AND` binds tighter than `OR`.

Multiple WHERE clauses are logically ANDed. Each WHERE clause is treated as a parenthesized group: `WHERE a == 1 OR b == 2` followed by `WHERE c == 3` is equivalent to `WHERE (a == 1 OR b == 2) AND c == 3`.

## Field resolution

For events: known header column names (`timestamp`, `cpu_id`, `sequence`, `origin_class`, `event_type`, `effective_token_guid`, `true_token_guid`, `process_guid`, `boot_id`) resolve to columns. All other names resolve to payload field lookups via msgpack extraction.

For logs: all field names resolve to log columns (`timestamp`, `origin`, `is_error`, `message`, `boot_id`). There are no payload fields.

For metrics: known metric fields (`timestamp`, `name`, `type`, `value`) resolve to columns. All other names resolve to label lookups.

## Result format

All three modes return results as arrays of flat msgpack maps. Each record is a self-describing map with field names as keys.

Event records contain header fields and extracted payload fields merged as top-level keys. Log records contain log columns as top-level keys. Metric records contain the metric name, labels as top-level keys, timestamp, and value.

If SELECT is present, only the named fields appear in each record.
