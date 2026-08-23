---
title: Enforcement
description: Access control is the third phase of query evaluation — which clauses count as referencing a field, and why denial is silent.
---

The order in which eventd evaluates a query is fixed (PSPU §3.18), and
access control is the third phase — before predicates, transforms,
grouping, aggregation, ordering and pagination. What follows is the
sequence within that phase.

1. **Obtain the caller's token** from the connection (§7.1). Failure
   denies the query.
2. **Parse** the query to establish its data sources and filters (§6.1).
3. **Discover the concrete identifiers** the query could touch — event
   type strings, log origin strings, metric name strings. A broad
   selector authorizes nothing by itself: `EVENTS`, `EVENTS kacs.*`,
   `LOGS` without `FROM` and `METRIC cpu.*` are each resolved identifier
   by identifier.
4. **Resolve and check** each discovered identifier: find its descriptor
   by hierarchical matching (§7.2), build the object type list for the
   fields the query references (§7.3), call `kacs_access_check_list`,
   and cache the verdicts for this `(token, identifier, field set)`
   (§7.5).
5. **Apply root verdicts.** An identifier whose root is denied is
   invisible: its records are excluded from the logical row set before
   aggregation, ordering, pagination and formatting. For a cross-type
   source, a denied identifier is treated as having no matching data.
6. **Apply field verdicts to predicates.** Where the query references a
   field in a predicate or shaping clause and a matching identifier does
   not grant it, that identifier's records contribute nothing — exactly
   as if its root had been denied. The query is **not** rejected.
7. **Cross-type sources** get the same treatment. A denied root, or a
   denied field needed to evaluate the condition, makes the condition
   evaluate as though no matching cross-source data existed.
8. **Execute**, with root filtering already part of the logical row set.
9. **Re-resolve per result identifier.** For each distinct concrete
   identifier in the resulting rows, resolve its descriptor, build the
   object type list with field GUIDs, call `kacs_access_check_list` with
   the token, the descriptor, `EVENTD_READ`, the list and an audit
   context naming the identifier, and cache the per-field results.
10. **Shape each record.** Look up the cached results for its
    identifier; exclude the record entirely if the root was denied;
    otherwise include it, and include each field only if its node was
    granted.

## Which clauses count as referencing a field

Step 6 applies to every clause that reads a value rather than merely
displaying one:

- ordinary `WHERE` predicates
- metric label filters in a primary selector
- `GROUP`, `COUNT BY`, `TOP N BY`, `SORT` and `DISTINCT` fields
- event and log aggregation arguments — `SUM`, `AVG`, `MIN`, `MAX`
- metric transforms and terminal aggregations, all of which read the
  fixed `value` field: `RATE`, `DELTA`, `P50`, `P95`, `P99`, `AVG`,
  `MIN`, `MAX`, `SUM`, `AVG_OVER`, `MIN_OVER`, `MAX_OVER`, `SUM_OVER`
- a metric boot filter, which reads `boot_id`; and an explicit metric
  type predicate, grouping, sort or distinct, which reads `type`

`SELECT` is not on this list. It shapes output and is applied last, so a
field it omits was still available to every earlier phase — and
conversely, selecting a field the caller may not read removes the field,
not the record.

## Denial is silent, not fatal

Step 6 excludes rather than rejects, and this is the decision most worth
being explicit about, because rejecting is the more informative
behaviour and that is exactly the objection to it.

A rejection would tell the caller that some identifier exists, matches
its query, and carries a field it may not read — three facts about data
it was not permitted to see, delivered by the mechanism meant to
withhold them, and enumerable by trying queries and watching which ones
fail. Excluding costs the caller a result narrower than it appears;
rejecting costs the model the property it rests on.

Cross-source fields already worked this way (step 7); primary-source
fields now match them.

## Field authorization does not depend on presence

A field's authorization is resolved from the name **as written**,
against each concrete identifier, whether or not any record of that
identifier actually carries it.

Payload fields vary between records of the same type, so a rule turning
on presence would require the scan that authorization is meant to
precede.

## Internal values are not fields

Row identifiers, series identifiers, ordering tiebreakers and series
type checks are not query-language source fields unless the mode exposes
them as fixed fields or the query names them (§6.2). Errors raised by
internal checks never carry a denied field's value.

A metric result's `value` **is** a source field, because it is either a
raw sample or a scalar derived from raw samples.

## Filtering is part of the logical result

Access filtering is not a presentation step. Aggregating, ordering or
paginating over unreadable records would leak them through counts,
through ordering, and through the gaps in pagination.

eventd may push authorization predicates into SQL when the identifier
set is known, or read candidates and filter them before aggregating
(§6.3). The externally visible result is identical to filtering first,
and `COUNT`, `COUNT BY`, `TOP N BY` and every other aggregate reflect
only what the caller may see.

## The audit trail

Every access check produces a KACS audit event through the SACL audit
walk in the AccessCheck pipeline.

eventd passes an `audit_context` blob naming the security pattern being
accessed — `"events:kacs.access_denied"`, `"logs:loregd"` — so the audit
trail records exactly which observability data was read, by whom, rather
than merely that eventd performed a check.

Those audit events are themselves KMES events, which eventd consumes and
stores, and which are governed by the `synthetic`-independent event
patterns like any other. Reading the audit store is auditable.
