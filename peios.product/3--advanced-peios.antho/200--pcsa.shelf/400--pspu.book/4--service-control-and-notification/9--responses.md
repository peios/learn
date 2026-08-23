---
title: Responses
description: The four response shapes — acknowledgement, status, system and error — and what may be null in each.
---

Every response carries a `status` field, which MUST be exactly `"ok"` or
`"error"`. What else it carries depends on which of four shapes it is.

## The acknowledgement shape

Returned by a lifecycle command that created, merged into, queued,
cancelled, cleared or executed an operation.

```json
{"status": "ok", "operation_id": "a1b2c3d4-…", "service": "jellyfin",
 "state": "active", "cause": "explicit_start", "warnings": []}
```

| Field | Type | Meaning |
|---|---|---|
| `operation_id` | string | The operation to observe. |
| `service` | string | The target. |
| `state` | string | The service's state when the response was formed. §4.B |
| `cause` | string or null | Why the service last transitioned. §4.B |
| `warnings` | array of strings | Human-readable warnings. Often empty. |
| `mode` | string | For a `reload` only. §4.13 |

`warnings` here is an array of **strings**. The `status` response uses
the same field name for an array of objects (§4.14); a client MUST
distinguish them by which command it sent, not by inspecting the array.

## The status shape

Returned by `status`, and also by a lifecycle command that had no effect
— see §4.12. §4.14 gives it in full.

## The system shape

Returned by `shutdown`:

```json
{"status": "ok"}
```

Nothing else. A shutdown has no operation to observe and no service to
report on. `reload-config` has its own shape (§4.15).

## The error shape

```json
{"status": "error", "code": "ACCESS_DENIED",
 "message": "caller lacks SERVICE_START on jellyfin"}
```

`code` MUST be one of the values in §4.10. `message` is human-readable
and is not normative: a client MUST NOT parse it, match on it, or branch
on its content. Two managers answering the same request with the same
code MAY word the message differently.

## Nullability

A field that does not apply to the current state MUST be present and
`null` rather than omitted, except where this chapter says otherwise.
A client MUST accept `null` for any field this chapter marks nullable,
and MUST NOT treat a `null` as an error.

The two exceptions are `mode`, which appears only on a reload response,
and `job_id` in the notification event payloads, which is omitted when
there is no job.
