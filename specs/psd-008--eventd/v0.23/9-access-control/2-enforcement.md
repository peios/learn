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
3. Execute the query against the database(s).
4. For each unique pattern in the result set (distinct event type, log origin, or metric name):
   a. Resolve the SD for that pattern using hierarchical matching (§9.1).
   b. Construct the object type list with field GUIDs.
   c. Call `kacs_access_check_list` (PSD-004 syscall 1024) with the caller's token, the resolved SD, `EVENTD_READ`, the object type list, and an audit context identifying the pattern.
   d. Cache the per-field results for this (token, pattern) pair.
5. For each record in the result set:
   a. Look up the cached per-field results for the record's pattern.
   b. If the root node was denied, exclude the entire record.
   c. If the root node was granted, include the record. For each field, include it only if the corresponding field node was granted.

## Caching

Access check results MUST be cached to avoid redundant syscalls. The caching strategy has two levels:

**Record-level caching.** If the SD for a pattern contains no object ACEs (no per-field restrictions), the access check result is a simple grant/deny on the root. This result is cached per (token, pattern) pair. A query returning 10,000 events across 20 distinct event types performs at most 20 access checks.

**Field-level caching.** If the SD contains object ACEs, the result depends on which fields are present in the record (different event types have different payload fields and thus different object type lists). The result is cached per (token, pattern, field set) tuple. Events of the same type have the same field set, so in practice this means one access check per (token, event type) pair.

**SD caching.** The SD resolution (pattern to SD lookup) SHOULD be cached across queries. eventd SHOULD watch the security registry subtree for changes and invalidate the SD cache when SDs are modified.

## Filtered results

Records and fields filtered by access control are silently excluded. The query response does not indicate that records or fields were filtered. The caller sees a result set that appears complete for their access level.

COUNT, COUNT BY, TOP N BY, and other aggregation queries MUST reflect only the records the caller is authorized to see.

## Streaming enforcement

For streaming queries, per-field access check results are cached from the initial query. If an SD changes during a streaming query, the SD cache is invalidated and subsequent batches are re-checked. Token changes (e.g., group membership changes) are not reflected during a streaming query -- the token is a snapshot captured at connection time.

## Cross-type filter enforcement

Cross-type filters (WHERE METRIC, WHERE EVENT, WHERE LOG) are subject to access control on both the primary data source and the cross-referenced data source. If the caller does not have EVENTD_READ on the cross-referenced pattern, the cross-type condition evaluates as if no matching data exists.

This ensures that cross-type filtering cannot be used to infer data the caller is not authorized to see.

## Audit trail

Every access check performed by eventd produces a KACS audit event via the SACL audit walk in the AccessCheck pipeline. eventd MUST pass an `audit_context` blob identifying the security pattern being accessed (e.g., `"events:kacs.access_denied"` or `"logs:loregd"`). This context appears in the emitted audit events, allowing the audit trail to identify exactly which observability data was accessed and by whom.

## Write-path access control

### Events

Event emission is controlled by KMES (PSD-003). The `kmes_emit` and `kmes_emit_batch` syscalls require SeAuditPrivilege. eventd is not involved in write-path access control for events.

### Logs and metrics

The log and metric ingestion sockets use filesystem permissions. The socket files SHOULD be created with permissions that allow all services managed by peinit to write.

> [!INFORMATIVE]
> Socket-level file permissions are a v0.23 simplification for write-path access control on logs and metrics. Future versions may introduce SD-based write access control per origin or metric name.
