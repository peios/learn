---
title: Fields and Results
description: Every result record is a flat map — the event, log and metric field sets, the reserved header names, and how nesting is flattened.
---

Every result record is a **flat** MessagePack map. There is no nesting
in a result, in any mode.

Flatness is what makes one set of rules — for access control, for
ordering, for grouping, for projection — apply uniformly to a header
field, a payload field and a metric label alike. A nested result would
need a path language, and a path language would need to be reproduced
identically by every SD author and every client.

## Event fields

These names resolve to header fields:

`timestamp`, `cpu_id`, `sequence`, `origin_class`, `event_type`,
`effective_token_guid`, `true_token_guid`, `process_guid`, `boot_id`

Every other name resolves to a payload field.

### Header names are reserved

Header field names are reserved in the query language and in result
maps. If a payload carries a top-level key with a header field's name,
**the header wins**.

The colliding payload value is stored unchanged, and is retrievable as
part of the raw payload by whatever holds it, but it is not exposed
through field resolution, `SELECT`, `WHERE`, aggregation, access control
or result maps. Suppression is applied *before* descendants are
flattened, so a payload key named `timestamp` removes its entire subtree
from the query surface, not just itself.

An emitter SHOULD avoid payload keys that collide with header names.

> [!NOTE]
> The header must win because header fields are the ones the kernel
> stamped and an emitter could not influence (PSPK §2). If a payload key
> could shadow `process_guid`, an emitter could choose what its own
> events appeared to come from, and every query filtering on identity
> would be answerable by the party being investigated.

### Flattening

Payload maps are flattened recursively, path segments joined with `.`:
a payload `{source: {name: "x"}}` exposes the field `source.name`.

Each map key on a queryable path MUST be a MessagePack string matching:

```text
[A-Za-z_][A-Za-z0-9_-]*
```

Note that `.` is **not** permitted in a segment, though it is permitted
in an identifier generally (§3.19) — a key containing a dot could not be
distinguished from a path through two maps.

A key that is not a string, contains `.`, or does not match the grammar
is stored unchanged and is **not queryable**: it does not resolve, does
not appear in a result map, and has no field identity for access
control. An empty map produces no field at all.

Maps are containers; every non-map value, arrays included, is emitted at
its flattened path (§3.17).

If two payload entries flatten to the same path, the **first in
MessagePack map order wins** and later duplicates are suppressed.

## Log fields

`timestamp`, `origin`, `is_error`, `message`, `boot_id`, `job_id`

The set is closed. There are no payload fields and no flattening, and a
collector MUST reject any other log field name as a parse error rather
than resolving it to null. A log record has a fixed shape, so a name
outside it is a mistake the collector can see — unlike an event payload
field, which may legitimately be absent from a given record.

`is_error` is a boolean in the query language, and compares against
`true`/`false` or against `1`/`0`.

## Metric fields

`timestamp`, `boot_id`, `name`, `type`, `value`, `overflow`

Every other name resolves to a label. Ingestion refuses labels colliding
with these six (§3.10), so the flat namespace is unambiguous by
construction rather than by a precedence rule.

`type` is the series type as a string: `"counter"`, `"gauge"` or
`"histogram"`.

`overflow` is an output-only boolean marker. It is present and true only
when a histogram percentile cannot be located below the series' highest
boundary (§3.25); otherwise it is absent. Predicates and label selectors
therefore see it as null, like any other output not yet computed.

## What a record contains

**Event records** carry the header fields plus every non-suppressed
flattened payload field, as top-level keys.

**Log records** carry the log fields.

**Raw metric sample records** carry `timestamp`, `boot_id`, `name`,
`type`, `value`, and the series' labels as top-level keys. A
percentile-overflow result additionally carries `overflow`.

**Aggregated metric results** carry `name`, `type` and `value`, plus
labels when the result belongs to one label set. They carry `boot_id`
only when the query restricted the samples to exactly one boot by a
`boot_id` equality predicate, in which case the value is that boot ID; a
result that could span boots omits it rather than picking one. An
aggregate tainted by a percentile overflow additionally carries
`overflow` (§3.25).

**Aggregation results** in event and log mode carry the group key fields
and the aggregate output, with the fixed schemas of §3.23.

## SELECT

`SELECT` narrows a result record to the named fields. It is valid only
for non-aggregating event and log queries.

A collector MUST reject `SELECT` combined with `COUNT BY`, `TOP N BY`,
`DISTINCT` or `GROUP`, and MUST reject it in metric mode: all of those
have fixed output schemas, and a clause that reshapes a fixed schema is
a contradiction rather than a refinement.

`SELECT` is applied **last**, after every other phase (§3.23). It
controls the shape of the output and nothing else: a field not selected
is still available to `WHERE`, to `SORT`, and to grouping. Narrowing
what is displayed MUST NOT narrow what is filtered on.
