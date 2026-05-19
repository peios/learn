---
title: Common records
type: reference
description: Several audit event types share common sub-record structures — the subject record identifying the calling principal, and the process record identifying the running process. This page covers the full schema for each.
related:
  - peios/audit-event-reference/overview
  - peios/audit-event-reference/event-schemas
  - peios/auditing/overview
---

Three sub-record structures appear inside multiple audit event types:

- The **subject record** describes the calling principal — the token under which the operation ran.
- The **process record** describes the running process — pid, name, executable path.
- The **trigger record** appears only inside `access-audit` events and is documented inline in [Event schemas](~peios/audit-event-reference/event-schemas).

This page covers the subject and process records in detail.

## Subject record

The subject record identifies the **effective token** under which the operation was performed. For events fired from inside an impersonating thread, the subject reflects the impersonation token, not the primary. For non-impersonating threads, the primary is the effective.

For `continuous-audit` events specifically, the subject is the effective token **at the moment of the operation**, not at the moment the handle was opened. A process whose effective token has changed since the handle's open gets the up-to-date subject for each subsequent operation.

### Fields

| Key | Type | Always present? | Meaning |
|---|---|---|---|
| `user_sid` | bin | Yes | The token's user SID. |
| `group_sids` | array of bin | Yes | The token's group SIDs. Each entry is a binary SID. |
| `group_attributes` | array of uint | Yes | Per-group attributes bitmask, parallel to `group_sids`. Each entry holds the `SE_GROUP_*` flags for the corresponding group. |
| `integrity_level` | uint | Yes | The token's integrity level (the integrity RID — 0, 4096, 8192, 12288, or 16384). |
| `pip_type` | uint | Yes | The PIP type of the calling process. 0 = None, 512 = Protected, 1024 = Isolated. |
| `pip_trust` | uint | Yes | The PIP trust level of the calling process. |
| `auth_id` | uint | Yes | The session LUID the token belongs to. Lets consumers cross-reference with `/sys/kernel/security/kacs/sessions` or with `logon-session-destroyed` events. |
| `token_id` | uint | Yes | The token's unique LUID. Lets consumers correlate events by specific token. |
| `impersonation_level` | uint | Yes | The effective token's impersonation level (0–3). For non-impersonating threads, this is 0 (the primary token's conventional level). |
| `projected_uid` | uint | Yes | The Linux UID projection. For correlation with Linux-side audit data. |

### group_sids and group_attributes pairing

The two arrays are parallel: `group_sids[i]` is a SID, and `group_attributes[i]` is the attributes bitmask for that group entry. The arrays have the same length.

The attributes use the standard `SE_GROUP_*` flags:

| Flag | Value | Meaning |
|---|---|---|
| `SE_GROUP_MANDATORY` | 0x01 | Group cannot be disabled. |
| `SE_GROUP_ENABLED_BY_DEFAULT` | 0x02 | Enabled at creation time. |
| `SE_GROUP_ENABLED` | 0x04 | Currently enabled. |
| `SE_GROUP_OWNER` | 0x08 | Can act as owner for new objects. |
| `SE_GROUP_USE_FOR_DENY_ONLY` | 0x10 | Matches only deny ACEs. |
| `SE_GROUP_LOGON_ID` | 0xC0000000 | The logon SID; cannot be disabled. |

Consumers parsing for group membership should typically filter by `SE_GROUP_ENABLED` set and `SE_GROUP_USE_FOR_DENY_ONLY` clear (for allow-style matching) — same rule the access check uses.

### What the subject record does *not* include

The subject record carries identity and integrity state. It does **not** include:

- The token's privileges (could be added in a future version; consumers needing privileges parse them via separate API queries on running tokens).
- The token's claims (user_claims, device_claims).
- The token's restricted_sids list.
- The token's confinement state.
- The token's full default DACL.

These are absent for compactness — audit events get heavy fast, and most consumers don't need them. Code that needs the full token state queries the token directly (where it still exists) via `KACS_IOC_QUERY` rather than looking at the audit record.

### Example

A typical subject record for a user-mode access:

```
{
  "user_sid": <bin: S-1-5-21-...-1001>,
  "group_sids": [
    <bin: S-1-5-21-...-1001>,    // The user themselves (often a group reference too)
    <bin: S-1-5-32-545>,          // BUILTIN\Users
    <bin: S-1-1-0>,               // Everyone
    <bin: S-1-5-11>,              // Authenticated Users
    <bin: S-1-5-5-X-Y>,            // The logon SID
  ],
  "group_attributes": [
    0x01,         // mandatory + enabled
    0x07,         // mandatory + enabled-by-default + enabled
    0x07,
    0x07,
    0xC0000007    // logon SID + standard flags
  ],
  "integrity_level": 8192,         // Medium
  "pip_type": 0,                   // None — user-mode binary
  "pip_trust": 0,
  "auth_id": 42,
  "token_id": 1234,
  "impersonation_level": 0,
  "projected_uid": 1001
}
```

For a TCB process the values would be different: `integrity_level: 16384` (System), `pip_type: 512` (Protected), `pip_trust: 8192`, the user_sid likely SYSTEM.

## Process record

The process record identifies the kernel-level process the event came from.

### Fields

| Key | Type | Always present? | Meaning |
|---|---|---|---|
| `pid` | uint | Yes | The process ID. |
| `name` | string | Yes | The process's executable name (e.g., `"loregd"`). |
| `executable_path` | string | Yes | The full filesystem path to the executable (e.g., `"/usr/bin/loregd"`). |

For `continuous-audit` events, this is the operation-time process; for everything else, the process at the time the event fired.

### Reading the process record

`pid` is useful in the short term — the process may still exist when the consumer is processing the event. After a long delay the pid may have been reused; correlating with `name` and `executable_path` is safer for long-term records.

The `name` is the kernel's internal name for the process (typically the basename of the executable). It may differ from what `argv[0]` was set to; consumers wanting argv-style names need to look elsewhere.

The `executable_path` is the path the kernel resolved at exec — the path that was passed to `execve`. Symlinks have been resolved at this point.

### Example

```
{
  "pid": 12345,
  "name": "loregd",
  "executable_path": "/usr/bin/loregd"
}
```

## What's missing

A few things the records do not include but audit consumers sometimes want:

- **Thread ID (`tid`)**. The records identify the process; for thread-level granularity, the process record is too coarse. Future versions may add `tid` to events that fire on a specific thread. v0.20 does not include it.
- **Originating session beyond `auth_id`**. The subject's `auth_id` is the immediate session. For tokens derived from other sessions (S4U, network logon), the original session's ID lives in the token's `origin` field, not in audit events.
- **Conditional ACE values**. Events from `*_CALLBACK` ACEs do not include the values of the conditional expression — the consumer cannot tell from the audit log exactly which claim values caused the ACE to match. The ACE's bytes are in the trigger record; consumers wanting evaluated values need to reproduce the evaluation themselves.

These absences are deliberate — the audit events are sized for the common case, not for forensic completeness. For deeper investigation, the audit pipeline (eventd plus longer-term storage) is the right tool, not the kernel's emission format.

## Field stability

The fields listed here are stable for the v0.20 line. New fields may appear in future versions; existing fields will not be renamed or removed without a versioned event type name change.

Consumers should:

1. Ignore unknown keys.
2. Not rely on the absence of a key.
3. Not assume specific value ranges beyond what is documented (e.g., don't assume `integrity_level` is exactly one of the five documented values — future versions may add levels).

The forward-compatibility rule applies uniformly: parse what you understand, ignore what you don't, and your code keeps working across kernel versions.
