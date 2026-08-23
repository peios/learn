---
title: access-audit
description: The most common event in the system — what triggers it, why one access can produce several, and a worked example.
---

The most common event in the system. Fires at AccessCheck completion,
from the SACL audit walk, and from a token's `audit_policy` forcing an
audit that no ACE asked for.

Event type string: `access-audit`.

| Key | Type | Meaning |
|---|---|---|
| `subject` | map | Subject record (§2.1). |
| `object_context` | bin or nil | Caller-supplied opaque identifier for the object. `nil` if AccessCheck was not given one. |
| `requested_access` | uint | The mask the caller requested, after generic mapping. |
| `granted_access` | uint | The mask actually granted. |
| `success` | bool | True when every requested bit is in `granted_access`. |
| `trigger` | map | Why this event fired. Below. |
| `process` | map | Process record (§2.2). |

Every field is always present.

## The trigger record

| Key | Type | Meaning |
|---|---|---|
| `kind` | string | `sacl` or `policy`. |
| `ace` | bin or nil | For `kind = sacl`, the matched ACE's bytes. For `kind = policy`, `nil`. |

`kind = sacl` means an audit ACE in the object's SACL — or in a central
access policy's SACL — matched this access, and `ace` carries the exact
ACE so a consumer can identify which rule fired.

`kind = policy` means nothing in any SACL asked for this. The audit
fired because the calling token's `audit_policy` carries
`OBJECT_ACCESS_SUCCESS` or `OBJECT_ACCESS_FAILURE`, which forces an
audit on every access that token makes.

The distinction matters when reading volume. A flood of `kind = policy`
events is a property of the token, and is fixed by changing the token's
policy. A flood of `kind = sacl` events is a property of the object, and
is fixed by changing its SACL.

## One access can produce several events

The event is per matching audit ACE, not per access. An access that
matches three audit ACEs produces three events, each with a different
`ace` in its trigger and otherwise identical.

## Example

A successful read where a SACL audit ACE matched:

```
{
  "event_type": "access-audit",
  "event_time": <timestamp>,
  "subject": { ... },
  "object_context": <bin>,
  "requested_access": 0x00120089,
  "granted_access":   0x00120089,
  "success": true,
  "trigger": { "kind": "sacl", "ace": <bin> },
  "process": { ... }
}
```

`0x00120089` is `GENERIC_READ` after mapping to file-specific bits.
Generic bits never survive into an event; the mask is always specific.
