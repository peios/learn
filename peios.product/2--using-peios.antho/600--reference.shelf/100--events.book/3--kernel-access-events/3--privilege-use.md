---
title: privilege-use
description: Recording a privilege that contributed bits to the granted mask — the five that can appear, and what success actually means here.
---

Fires at AccessCheck for a privilege that contributed bits to the
granted mask, when the token's `audit_policy` asks for it.

Event type string: `privilege-use`.

| Key | Type | Meaning |
|---|---|---|
| `subject` | map | Subject record (§2.1). |
| `object_context` | bin or nil | Object identifier from the access check. |
| `privilege` | string | The canonical privilege name. |
| `requested_access` | uint | The bits the caller requested that this privilege might address. |
| `granted_access` | uint | The bits the privilege contributed, before later narrowing. |
| `surviving_access` | uint | The subset of `granted_access` that reached the final granted mask. |
| `success` | bool | True when `surviving_access` is non-empty. |
| `process` | map | Process record (§2.2). |

Every field is always present.

## Only five privileges can appear

The `privilege` field carries a canonical name, and **only five are
representable**:

- `SeSecurityPrivilege`
- `SeTakeOwnershipPrivilege`
- `SeBackupPrivilege`
- `SeRestorePrivilege`
- `SeRelabelPrivilege`

Any other bit fails the encoder closed rather than emitting an unnamed
privilege. This is consistent with those being the only five that can
influence an access check at all, and therefore the only five that can
produce this event.

A consumer will never see a sixth name here. A privilege used for
something other than an access decision produces no `privilege-use`
event.

## Success means it worked, not that it fired

This is the field most often misread.

`success = true` — the privilege contributed bits and they survived to
the final grant. The privilege did useful work. Governed by the
`PRIVILEGE_USE_SUCCESS` audit policy.

`success = false` — the privilege contributed bits and a later layer
stripped them. The caller was in a confinement that does not permit it,
or a CAAP rule narrowed it out, or the caller was non-dominant under
PIP. Governed by `PRIVILEGE_USE_FAILURE`.

A `success = false` event is not a failed attempt to *use* a privilege.
It is a privilege that fired and was then overridden — which is usually
the more interesting record of the two, because it shows a boundary
doing its job.

A token can carry either policy bit, both, or neither, and each controls
its own flavour independently.

## Example

A backup tool whose `SeBackupPrivilege` was stripped by confinement:

```
{
  "event_type": "privilege-use",
  "event_time": <timestamp>,
  "subject": { ... },
  "object_context": <bin>,
  "privilege": "SeBackupPrivilege",
  "requested_access": 0x00000001,
  "granted_access":   0x00000001,
  "surviving_access": 0x00000000,
  "success": false,
  "process": { ... }
}
```
