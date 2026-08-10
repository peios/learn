---
title: Enforcement
---

## Caller identification

When a client connects to the query socket, eventd MUST obtain the caller's token by calling `kacs_open_peer_token` (PSD-004 syscall 1010) on the connected socket file descriptor. This returns a token fd representing the peer's identity, captured at connection time.

If `kacs_open_peer_token` fails, eventd MUST deny the query entirely (fail-closed).

## Query-time enforcement

Access control is enforced at query time, not at storage time. All events, logs, and metrics are stored regardless of who will eventually query them. Different callers querying the same data see different results based on their token.

This design is correct because:

- Audit events MUST be stored regardless of who can read them. Filtering at storage time would violate audit integrity.
- SDs can change over time. An administrator can grant or revoke access retroactively.
- Multiple users with different access levels query the same event store.

## Access check flow

For each query:

1. Obtain the caller's token via `kacs_open_peer_token`.
2. Parse the query to determine the data source and filters.
3. Determine or discover the concrete data identifiers that may be touched by the query. These identifiers are event type strings, log origin strings, and metric name strings. Broad selectors such as `EVENTS`, `EVENTS kacs.*`, `LOGS` without `FROM`, or `METRIC cpu.*` do not authorize through the wildcard SD alone; each concrete identifier that appears in matching data is resolved independently through the hierarchy in §9.1.
4. For each concrete identifier discovered for the primary source or a cross-type source, resolve the SD using hierarchical matching (§9.1), construct the object type list for the fields referenced by the query, call `kacs_access_check_list`, and cache the result for this (token, identifier, field set) tuple.
5. If the root node for a concrete identifier is denied, data matching that identifier is invisible to the query. For primary-source data, records with that identifier MUST be excluded before aggregation, sorting, pagination, or result formatting. For cross-type data, denied identifiers are treated as having no matching data.
6. If the query references a primary-source field in a predicate or shaping
   clause, verify that the caller has `EVENTD_READ` on that field's GUID for
   every concrete primary-source identifier where that field could be
   evaluated. If any matching identifier denies that field, the query MUST be
   rejected with an error. Predicate and shaping clauses include:
   a. Standard `WHERE` predicates.
   b. Primary-selector label filters for metrics.
   c. `GROUP`, `COUNT BY`, `TOP N BY`, `SORT`, and `DISTINCT` fields.
   d. Event and log aggregation function arguments (`SUM`, `AVG`, `MIN`, `MAX`).
   e. Metric transforms and terminal aggregations. `RATE`, `DELTA`, `P50`,
      `P95`, `P99`, `AVG`, `MIN`, `MAX`, `SUM`, `AVG_OVER`, `MIN_OVER`,
      `MAX_OVER`, and `SUM_OVER` all read the fixed metric `value` field.
      Metric boot filters read `boot_id`; explicit metric type predicates,
      grouping, sorting, or distinct clauses read `type`.
   Derived aggregate output fields such as `count`, `sum`, `avg`, `min`, and
   `max` are not source fields and do not have field GUIDs. Metric result
   `value` is a source field because it represents a raw sample value or a
   scalar derived from raw sample values. Derived outputs are visible when the
   caller is authorized for the rows and source fields used to compute them.
   Internal fields and metadata that are required to preserve query semantics,
   such as row identifiers, series identifiers, and series type checks, are not
   query-language source fields unless exposed as fixed fields or explicitly
   referenced by the query. Error messages caused by internal checks MUST NOT
   include denied field values.
7. If a cross-type condition references fields on the cross-referenced source,
   perform the same field authorization check for those concrete cross-source
   identifiers. If the root is denied, or if any cross-source field needed to
   evaluate the condition is denied, that cross-type condition MUST evaluate as
   if there were no matching cross-source data for the denied identifier. The
   query is not rejected solely because a cross-source field is denied.
8. Execute the query against the database(s), applying root access filtering as part of the logical row set before aggregation.
9. For each unique concrete identifier in the resulting rows (distinct event type, log origin, or metric name):
   a. Resolve the SD for that identifier using hierarchical matching (§9.1).
   b. Construct the object type list with field GUIDs.
   c. Call `kacs_access_check_list` (PSD-004 syscall 1024) with the caller's token, the resolved SD, `EVENTD_READ`, the object type list, and an audit context identifying the concrete identifier.
   d. Cache the per-field results for this (token, identifier) pair.
   Derived aggregate output fields are omitted from the object type list because
   they are not query-language source fields.
10. For each record in the result set:
   a. Look up the cached per-field results for the record's concrete identifier.
   b. If the root node was denied, exclude the entire record.
   c. If the root node was granted, include the record. For each field, include it only if the corresponding field node was granted.

Access control is part of the query's logical execution, not merely a final presentation filter. Aggregating, sorting, paginating, or applying predicates over data the caller cannot read would leak information through counts, ordering, or record presence. Implementations MAY push access predicates down into SQL when the concrete identifier set is known, or MAY read candidate rows and filter them before aggregation, but the externally visible result MUST be identical to filtering unauthorized rows first.

## Caching

Access check results MUST be cached to avoid redundant syscalls. The caching strategy has two levels:

**Record-level caching.** If the SD for a pattern contains no object ACEs (no per-field restrictions), the access check result is a simple grant/deny on the root. This result is cached per (token, pattern) pair. A query returning 10,000 events across 20 distinct event types performs at most 20 access checks.

**Field-level caching.** If the SD contains object ACEs, the result depends on which fields are present in the record (different event types have different payload fields and thus different object type lists). The result is cached per (token, pattern, field set) tuple. Events of the same type have the same field set, so in practice this means one access check per (token, event type) pair.

**SD caching.** The SD resolution (pattern to SD lookup) MUST be cached across
queries. eventd MUST watch the security registry subtree for changes and
invalidate cached SD resolutions and access-check results when SDs are
modified. If the registry watch fails after startup, eventd MUST discard the SD
cache and operate fail-closed for new SD resolutions until the watch is
re-established.

## Filtered results

Records and fields filtered by access control are silently excluded. The query response does not indicate that records or fields were filtered. The caller sees a result set that appears complete for their access level.

COUNT, COUNT BY, TOP N BY, and other aggregation queries MUST reflect only the records the caller is authorized to see.

## Streaming enforcement

For streaming queries, per-field access check results discovered during the
initial query are cached. If a later streamed batch contains a concrete
identifier that was not present in the initial result set (for example a new
event type or log origin), eventd MUST resolve that identifier's SD and perform
the same root and field access checks before using the record or its DISTINCT
field value. If an SD changes during a streaming query, the SD cache is
invalidated and subsequent batches are re-checked. Token changes (e.g., group
membership changes) are not reflected during a streaming query -- the token is a
snapshot captured at connection time.

## Cross-type filter enforcement

Cross-type filters (WHERE METRIC, WHERE EVENT, WHERE LOG) are subject to access control on both the primary data source and the cross-referenced data source. If the caller does not have EVENTD_READ on the cross-referenced pattern, the cross-type condition evaluates as if no matching data exists.

This ensures that cross-type filtering cannot be used to infer data the caller is not authorized to see.

## Audit trail

Every access check performed by eventd produces a KACS audit event via the SACL audit walk in the AccessCheck pipeline. eventd MUST pass an `audit_context` blob identifying the security pattern being accessed (e.g., `"events:kacs.access_denied"` or `"logs:loregd"`). This context appears in the emitted audit events, allowing the audit trail to identify exactly which observability data was accessed and by whom.

## Write-path access control

### Events

Event emission is controlled by KMES (PSD-003). The `kmes_emit` and `kmes_emit_batch` syscalls require SeAuditPrivilege. eventd is not involved in write-path access control for events.

### Logs and metrics

The log and metric ingestion sockets use filesystem permissions as a coarse
local reachability gate. v0.23 creates both socket pathnames with mode `0666` as
defined in §4.2 and §6.2, so any local process that can traverse the containing
directory can send log or metric datagrams.

> [!INFORMATIVE]
> **Origin spoofing is a known gap in v0.23.** The `origin` field in log records and the `name` field in metric records are self-reported by the sender. Any process with filesystem write access to the datagram sockets can claim any origin or metric name. A compromised service can inject logs or metrics under another service's identity, creating false operational narratives or masking real incidents.
>
> The correct fix is SD-based write access control that validates the sender's KACS token against an SD governing which origins/metric names the sender is authorized to write. This requires a KACS primitive for identifying the peer token on datagram socket messages (analogous to `kacs_open_peer_token` for stream sockets, which is not currently defined for datagrams). Until this primitive exists, write-path identity validation for logs and metrics is not possible. This is a priority item for KACS and eventd coordination in a future version.
>
> In the interim, containing-directory permissions limit which processes can reach the sockets, and the read-path access control model (SDs on origins and metric names) prevents unauthorized users from querying spoofed data if the SDs are configured to restrict access to the legitimate origin.
