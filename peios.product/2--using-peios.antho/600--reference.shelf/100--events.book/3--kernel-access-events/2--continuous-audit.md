---
title: continuous-audit
description: Per-operation auditing on an already-open handle — the three masks involved, and why the subject is re-read each time.
---

Fires per operation on an already-open handle, when the operation's
required access overlaps a continuous audit mask cached on that handle.

Where `access-audit` records the decision to open something,
`continuous-audit` records what was then done with it. The mask is
configured by `SYSTEM_ALARM*` ACEs at the access check that opened the
handle, and the event is fired afterwards by whatever kernel subsystem
enforces the operation — FACS for file handles.

Event type string: `continuous-audit`.

| Key | Type | Meaning |
|---|---|---|
| `subject` | map | Subject record (§2.1), reflecting the **operation-time** effective token. |
| `object_context` | bin or nil | Object identifier. May differ from the open-time context if the enforcement point keeps its own. |
| `operation` | string | The operation name. FACS uses a `file.` prefix — `file.read`, `file.write`, `file.fallocate`. Other enforcement points use their own. |
| `requested_access` | uint | The mask this specific operation needs. |
| `matched_access` | uint | The subset of `requested_access` that overlapped the handle's continuous audit mask. |
| `granted_access` | uint | The mask cached on the handle at open time. |
| `success` | bool | Whether the operation itself succeeded. |
| `process` | map | Process record (§2.2), operation-time. |

Every field is always present.

## The three masks

They are easy to confuse, and reading them together is the point of the
event.

- **`requested_access`** is what the *operation* needs. A read needs
  `FILE_READ_DATA`; a write needs `FILE_WRITE_DATA`; an `mmap` with
  `PROT_EXEC` needs `FILE_EXECUTE`.
- **`matched_access`** is `requested_access` intersected with the
  handle's continuous audit mask. This is why the event exists — the
  bits that triggered it.
- **`granted_access`** is what the handle was opened with. An operation
  can only succeed if `requested_access` is a subset of it.

Read as a sentence: *the operation needed these bits, of which these
triggered audit, against a handle opened with these, and it
succeeded or did not.*

## Why the subject is re-read

A handle outlives the token that opened it. A process that changes its
effective token — starting or stopping impersonation — keeps its
handles, and every subsequent operation is audited under the token
current at that moment.

An investigation that assumes the open-time identity for later
operations will attribute them to the wrong principal.

## Example

A read on a file carrying an alarm ACE on `FILE_READ_DATA`:

```
{
  "event_type": "continuous-audit",
  "event_time": <timestamp>,
  "subject": { ... },
  "object_context": <bin>,
  "operation": "file.read",
  "requested_access": 0x00000001,
  "matched_access":   0x00000001,
  "granted_access":   0x00120089,
  "success": true,
  "process": { ... }
}
```
