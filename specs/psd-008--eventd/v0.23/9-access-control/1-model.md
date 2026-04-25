---
title: Access Control Model
---

## Overview

eventd enforces access control on the read path using KACS Security Descriptors and the KACS AccessCheck API (PSD-004). Every query is evaluated against SDs that determine which data -- and which fields within that data -- the caller is authorized to see. Unauthorized records and fields are silently filtered from the result set.

Access control on the write path is handled by other subsystems: KMES controls event emission (SeAuditPrivilege), and the log and metric ingestion sockets use filesystem permissions.

eventd does not implement its own access check logic. All access decisions are delegated to the KACS `kacs_access_check` (syscall 1023) and `kacs_access_check_list` (syscall 1024) syscalls, which run the full KACS AccessCheck pipeline including integrity checks, restricted token evaluation, confinement, conditional ACE evaluation, and SACL audit emission.

## Security objects

Access control is defined on named patterns. Each pattern represents a category of observability data and has an associated SD. The three data types have independent pattern namespaces:

- **Event patterns** control access to events by event type.
- **Log patterns** control access to logs by origin (service name).
- **Metric patterns** control access to metrics by metric name.

A pattern matches using prefix semantics. The pattern `kacs` matches all event types starting with `kacs.` (and the bare type `kacs` if it exists). The pattern `*` is the wildcard default that matches everything.

## Access rights

eventd defines the following object-specific access rights (bits 0-15 of the access mask):

| Right | Bit | Value | Description |
|---|---|---|---|
| `EVENTD_READ` | 0 | 0x0001 | Read records matching this pattern. |
| `EVENTD_CLEAR` | 1 | 0x0002 | Delete records matching this pattern (for future administrative operations). |

Generic mapping for eventd objects:

| Generic right | Maps to |
|---|---|
| GENERIC_READ | EVENTD_READ \| READ_CONTROL |
| GENERIC_WRITE | EVENTD_CLEAR \| READ_CONTROL |
| GENERIC_EXECUTE | EVENTD_READ \| READ_CONTROL |
| GENERIC_ALL | EVENTD_READ \| EVENTD_CLEAR \| READ_CONTROL \| WRITE_DAC \| WRITE_OWNER |

The generic mapping is passed to `kacs_access_check` via the `generic_read`, `generic_write`, `generic_execute`, and `generic_all` fields.

## Per-field access control

eventd supports per-field access control using KACS object ACEs and object type lists. Each queryable field is assigned a GUID. An SD can grant `EVENTD_READ` on specific field GUIDs, allowing fine-grained control over which fields a caller can see.

### Object type list

When performing an access check, eventd constructs an object type list as defined by PSD-004 §10.5. The list is a tree with the security pattern as the root and individual fields as children:

```
Level 0: Root (pattern GUID -- e.g., GUID for "kacs")
  Level 1: timestamp field GUID
  Level 1: event_type field GUID
  Level 1: cpu_id field GUID
  Level 1: origin_class field GUID
  Level 1: effective_token_guid field GUID
  Level 1: true_token_guid field GUID
  Level 1: process_guid field GUID
  Level 1: payload field GUID (covers all payload fields)
```

The access check is performed using `kacs_access_check_list` (syscall 1024), which returns separate verdicts for each node in the tree. eventd uses the per-node results to include or exclude fields from the result record.

### SD construction for per-field control

An SD with per-field restrictions uses object ACEs:

- An object ACE with no object type GUID applies to all fields (the root).
- An object ACE with a field GUID applies to that specific field.

Example: grant SecurityAdmins full read access, but grant MonitoringTeam read access to only timestamp, event_type, and cpu_id:

- Allow ACE: SecurityAdmins, EVENTD_READ (no object GUID -- applies to root, propagates to all fields)
- Allow ACE: MonitoringTeam, EVENTD_READ, object GUID = timestamp
- Allow ACE: MonitoringTeam, EVENTD_READ, object GUID = event_type
- Allow ACE: MonitoringTeam, EVENTD_READ, object GUID = cpu_id

MonitoringTeam members querying KACS events see records with only `timestamp`, `event_type`, and `cpu_id`. Payload fields, identity GUIDs, and other header fields are excluded.

### Field GUIDs

Field GUIDs are generated deterministically using UUID v5 (RFC 4122). A fixed namespace UUID is defined for eventd field GUIDs:

```
EVENTD_FIELD_NAMESPACE = {to be assigned}
```

A field's GUID is computed as:

```
field_guid = uuid_v5(EVENTD_FIELD_NAMESPACE, field_name)
```

Where `field_name` is the field's query-language name as a UTF-8 string. For header fields, this is the column name (e.g., `"timestamp"`, `"event_type"`, `"cpu_id"`). For payload fields, this is the dot-separated path (e.g., `"granted_access"`, `"target_sid"`, `"source.name"`). For log fields, this is the column name (e.g., `"origin"`, `"message"`, `"is_error"`). For metric labels, this is the label key (e.g., `"core"`, `"device"`).

The computation is deterministic: the same field name always produces the same GUID. No central registry is required. An SD author computes the GUID from the field name using the same algorithm when constructing object ACEs.

The field GUID does not encode the event type, log origin, or metric name. The SD hierarchy provides that scoping. An object ACE referencing the `granted_access` GUID in the SD for pattern `kacs` means "the `granted_access` field of KACS events."

### Object type list construction

When performing an access check, eventd constructs the object type list dynamically based on the fields present in the record being checked:

1. The root node (level 0) uses a fixed GUID for the security pattern's data type (one GUID for events, one for logs, one for metrics).
2. For each field in the record, a level-1 node is added with the field's deterministically computed GUID.

For event records, the object type list includes nodes for all header fields plus all payload fields present in that specific event's payload. Different event types produce different object type lists because they have different payload fields. The access check result is cached per (token, pattern, field set) tuple.

For log records, the field set is fixed (timestamp, origin, is_error, message, boot_id) and the object type list is the same for all log records.

For metric records, the field set includes the fixed metric fields (timestamp, name, type, value) plus label keys, which vary per series.

## Pattern resolution

When eventd evaluates access for a specific event type, log origin, or metric name, it resolves the applicable SD using hierarchical matching:

1. Look for an exact match on the full identifier (e.g., `kacs.access_denied`).
2. Walk up the hierarchy by removing the last dot-separated component (e.g., `kacs`).
3. Fall back to the wildcard default (`*`).

The first match wins. More specific patterns override less specific ones.

## SD storage

SDs are stored as registry values under the eventd security subtree:

```
Machine\System\eventd\Security\Events\*                     → SD (default for all events)
Machine\System\eventd\Security\Events\kacs                  → SD (all KACS events)
Machine\System\eventd\Security\Events\kacs.access_denied    → SD (specific override)
Machine\System\eventd\Security\Logs\*                        → SD (default for all logs)
Machine\System\eventd\Security\Logs\loregd                   → SD (loregd logs)
Machine\System\eventd\Security\Metrics\*                     → SD (default for all metrics)
Machine\System\eventd\Security\Metrics\cpu                   → SD (all cpu.* metrics)
```

The wildcard default keys (`*`) MUST exist. If a default SD does not exist, eventd MUST deny access to all data of that type (fail-closed).

## Default SDs

On first boot, eventd MUST create the default security keys if they do not exist:

| Key | Default SD |
|---|---|
| `Machine\System\eventd\Security\Events\*` | SYSTEM and Administrators: EVENTD_READ on all fields. |
| `Machine\System\eventd\Security\Logs\*` | SYSTEM, Administrators, and Authenticated Users: EVENTD_READ on all fields. |
| `Machine\System\eventd\Security\Metrics\*` | SYSTEM, Administrators, and Authenticated Users: EVENTD_READ on all fields. |

> [!INFORMATIVE]
> The defaults reflect the sensitivity hierarchy: events (which include security audit data) are restricted to administrators by default. Logs and metrics are readable by all authenticated users because they primarily contain operational data. Administrators can tighten these defaults by modifying the SDs.

## Conditional ACEs

SDs on eventd security objects MAY contain conditional ACEs (PSD-004 §3.8). eventd SHOULD pass relevant contextual information as local claims via the `local_claims_ptr` parameter of the access check syscall. This enables attribute-based policies such as "allow read if the caller's department claim equals 'security'".

The specific local claims passed by eventd are implementation-defined in v0.23.
