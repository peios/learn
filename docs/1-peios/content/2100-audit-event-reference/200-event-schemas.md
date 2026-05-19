---
title: Event schemas
type: reference
description: Full field schemas for each audit event type emitted by the kernel — access-audit, continuous-audit, privilege-use, logon-session-destroyed. Every key with its type, meaning, and constraints.
related:
  - peios/audit-event-reference/overview
  - peios/audit-event-reference/common-records
  - peios/auditing/audit-aces
  - peios/auditing/policy-forced-auditing
---

This page is the field-by-field schema for each audit event type the kernel emits. Common sub-records (`subject`, `process`, `trigger`) are referenced here and detailed in [Common records](~peios/audit-event-reference/common-records).

Every event is a msgpack map. Every event has the universal fields `event_type` (string) and `event_time` (uint); those are listed in the [overview](~peios/audit-event-reference/overview) and not repeated per-event.

## access-audit

The most common event. Fires from the SACL audit walk (step 14) and from token `audit_policy` forced auditing (step 14b) at AccessCheck completion.

`event_type` value: `"access-audit"`.

| Key | Type | Always present? | Meaning |
|---|---|---|---|
| `subject` | map | Yes | Subject record. Identifies the calling principal. See [Common records](~peios/audit-event-reference/common-records). |
| `object_context` | bin or nil | Yes | Caller-supplied opaque identifier for the object being accessed. nil if not provided to AccessCheck. |
| `requested_access` | uint | Yes | The access mask the caller requested (after generic mapping). |
| `granted_access` | uint | Yes | The mask of rights actually granted. |
| `success` | bool | Yes | Whether the access succeeded (every requested bit is in granted_access). |
| `trigger` | map | Yes | Trigger record. See below. |
| `process` | map | Yes | Process record. See [Common records](~peios/audit-event-reference/common-records). |

### trigger record

The `trigger` map identifies why this event fired:

| Key | Type | Always present? | Meaning |
|---|---|---|---|
| `kind` | string | Yes | `"sacl"` (a SACL audit ACE matched) or `"policy"` (token audit_policy forced it). |
| `ace` | bin or nil | Yes | For `kind = "sacl"`, the matched ACE's bytes. For `kind = "policy"`, nil. |

When `kind = "sacl"`, the `ace` field lets the consumer reconstruct which specific audit ACE in the object's (or CAAP's) SACL produced the event. When `kind = "policy"`, the audit fired because of the calling token's `audit_policy` flags (OBJECT_ACCESS_SUCCESS or OBJECT_ACCESS_FAILURE), not because of an ACE.

### Example

A successful read by a user where an audit ACE on the SACL matched:

```
{
  "event_type": "access-audit",
  "event_time": <kernel timestamp>,
  "subject": { ... see Common records ... },
  "object_context": <bin: opaque blob identifying the file>,
  "requested_access": 0x00120089,   // GENERIC_READ mapped to specific bits
  "granted_access":   0x00120089,
  "success": true,
  "trigger": {
    "kind": "sacl",
    "ace": <bin: the matched audit ACE bytes>
  },
  "process": { ... see Common records ... }
}
```

## continuous-audit

Fires per-operation on an open handle whose continuous audit mask overlaps the operation's required mask. Configured by `SYSTEM_ALARM*` ACEs at the access check that opened the handle; fires by the enforcement point (FACS, registryd, etc.) for each subsequent operation.

`event_type` value: `"continuous-audit"`.

| Key | Type | Always present? | Meaning |
|---|---|---|---|
| `subject` | map | Yes | Subject record. Reflects the **operation-time effective token**, not the token from when the handle was opened. |
| `object_context` | bin or nil | Yes | Object identifier; may be the same as the open-time context or different if the enforcement point retains its own. |
| `operation` | string | Yes | The operation name. FACS operations use a `file.` prefix (e.g., `"file.read"`, `"file.write"`, `"file.fallocate"`). Other enforcement points use their own prefixes. |
| `requested_access` | uint | Yes | The required access mask for this specific operation (read needs FILE_READ_DATA, etc.). |
| `matched_access` | uint | Yes | The subset of `requested_access` that overlapped the handle's continuous audit mask. Why the event fired. |
| `granted_access` | uint | Yes | The access mask cached on the handle at open time. |
| `success` | bool | Yes | Whether the operation itself succeeded. |
| `process` | map | Yes | Process record (operation-time, not open-time). |

### How the three access masks relate

- `requested_access` is what the *operation* needs. `read` needs FILE_READ_DATA; `write` needs FILE_WRITE_DATA; `mmap(PROT_EXEC)` needs FILE_EXECUTE; etc.
- `matched_access` is the intersection of `requested_access` with the handle's continuous audit mask (the alarm ACE's mask). This is the bit(s) that caused the audit to fire.
- `granted_access` is the mask the handle was opened with. The operation can only succeed if `requested_access` is a subset of `granted_access`.

Reading these together tells you: "the operation needed these bits, of which these bits triggered audit, against a handle that had been opened with these bits, and the operation succeeded/failed".

### Example

A read on a file with an alarm ACE on FILE_READ_DATA:

```
{
  "event_type": "continuous-audit",
  "event_time": ...,
  "subject": { ... operation-time effective token ... },
  "object_context": <bin>,
  "operation": "file.read",
  "requested_access": 0x00000001,   // FILE_READ_DATA
  "matched_access":   0x00000001,
  "granted_access":   0x00120089,   // (full granted mask cached on the handle)
  "success": true,
  "process": { ... }
}
```

## privilege-use

Fires at step 13 of AccessCheck for each privilege that contributed bits to the granted mask, when the token's `audit_policy` requests it.

`event_type` value: `"privilege-use"`.

| Key | Type | Always present? | Meaning |
|---|---|---|---|
| `subject` | map | Yes | Subject record. |
| `object_context` | bin or nil | Yes | Object identifier from the access check that fired this. |
| `privilege` | string | Yes | The canonical privilege name (e.g., `"SeBackupPrivilege"`). |
| `requested_access` | uint | Yes | The bits the caller requested that this privilege might address. |
| `granted_access` | uint | Yes | The bits the privilege contributed to the running grant (before narrowing). |
| `surviving_access` | uint | Yes | The subset of `granted_access` that survived to the final granted mask. |
| `success` | bool | Yes | True if `surviving_access` is non-empty (the privilege actually granted access); false if the privilege fired but its contribution was stripped by a later layer (confinement, CAAP, PIP). |
| `process` | map | Yes | Process record. |

### Success vs failure

`success = true` (PRIVILEGE_USE_SUCCESS audit policy): the privilege contributed bits that made it through. The audit log records that the privilege did useful work.

`success = false` (PRIVILEGE_USE_FAILURE audit policy): the privilege contributed bits but they were stripped. The audit log records that the privilege *tried* to grant access but could not (the caller was in a confinement that doesn't permit it, or a CAAP rule narrowed it out, or the caller was non-dominant in PIP).

Tokens can have either, both, or neither of these audit policy bits set. Each one independently controls whether its flavour of the event fires.

### Example

A backup tool using SeBackup that confinement stripped:

```
{
  "event_type": "privilege-use",
  "event_time": ...,
  "subject": { ... },
  "object_context": <bin>,
  "privilege": "SeBackupPrivilege",
  "requested_access": 0x00000001,
  "granted_access":   0x00000001,   // The privilege did try to grant it
  "surviving_access": 0x00000000,   // Stripped by confinement
  "success": false,
  "process": { ... }
}
```

## logon-session-destroyed

Fires when a logon session loses its last token reference and is destroyed by the kernel.

`event_type` value: `"logon-session-destroyed"`.

| Key | Type | Always present? | Meaning |
|---|---|---|---|
| `session_id` | uint | Yes | The destroyed session's LUID (same as `auth_id` of every token that belonged to it). |
| `user_sid` | bin | Yes | The session's user SID. |
| `logon_type` | uint | Yes | The session's logon type (Interactive, Network, etc. — see [Logon types](~peios/logon-sessions/logon-types)). |
| `auth_package` | string | Yes | The auth-package string (e.g., `"Kerberos"`, `"NTLM"`, `"local"`). |
| `created_at` | uint | Yes | The session's creation timestamp. |

This event has no `subject` or `process` — the session was the subject, and it just ended. No process is the cause.

Consumers (notably authd) use this event to release session-scoped state: Kerberos tickets, cached directory data, per-session credentials. The event fires exactly once per session.

### Example

```
{
  "event_type": "logon-session-destroyed",
  "event_time": ...,
  "session_id": 42,
  "user_sid": <bin: S-1-5-21-...-1001>,
  "logon_type": 2,           // Interactive
  "auth_package": "Kerberos",
  "created_at": <kernel timestamp>
}
```

## corrupt-sd

Fires once per inode per cache population when FACS encounters a structurally-invalid SD on a file.

`event_type` value: `"corrupt-sd"`.

| Key | Type | Always present? | Meaning |
|---|---|---|---|
| `subject` | map | Yes | Subject record for the access that triggered the detection. |
| `object_context` | bin or nil | Yes | Identifier of the object whose SD was corrupt. |
| `reason` | string | Yes | Diagnostic description of the failure (e.g., `"sd_too_large"`, `"acl_malformed"`, `"sid_invalid"`). |
| `process` | map | Yes | Process record. |

The event is rate-limited: one event per inode per cache population. The same corrupt SD encountered repeatedly during one mount's lifetime produces one event, not one per access. This prevents a flurry of corrupt files from drowning the audit stream.

The event is informational — the kernel denies the access regardless (fail-closed on corrupt SD; see [Policy classes](~peios/mount-policies/policy-classes)). The audit event is what tells administrators that the corruption exists.

## What events do not exist

A few notable absences in v0.20:

- **No `logon-session-created` event.** The kernel does not emit an event when authd creates a session. Tracking creations is done by subscribing to authd's higher-level events or by polling `/sys/kernel/security/kacs/sessions`.
- **No `token-created` event.** Similarly, the kernel does not emit when authd creates a token. The token's existence is observable through process inspection.
- **No periodic audit events.** Audit is event-driven; the kernel does not emit summary or heartbeat events.

These absences are intentional. The kernel's audit surface is for access decisions and session lifecycle endings; other lifecycle events are tracked at higher layers (authd's own logging, KMES's other event types).

## Event versioning

Audit events are not versioned by an explicit field in v0.20. The fields documented here are stable; new fields may be added in future versions (and consumers should ignore unknown keys per the forward-compatibility rule).

If a future version needs to break compatibility (rename a field, change a value type, remove a field), the event-type name itself would change — e.g., `access-audit` becomes `access-audit-v2`. This way old consumers continue to receive (and process) the old version's events; new consumers receive the new.

In v0.20 this hasn't happened; all events use the unversioned names listed above.
