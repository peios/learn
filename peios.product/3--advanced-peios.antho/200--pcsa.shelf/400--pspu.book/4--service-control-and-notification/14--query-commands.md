---
title: Query Commands
description: The three commands that read state and change nothing — status, list and operation-status — and how long results are retained.
---

Three commands read state and change nothing.

## status

Returns everything the manager knows about one service.

```json
{
    "status": "ok",
    "service": "jellyfin",
    "state": "active",
    "cause": "explicit_start",
    "status_text": "Listening on port 8096",
    "current_job": {
        "id": "a1b2c3d4-…",
        "type": "service_main",
        "pid": 1234,
        "started_at": "2026-06-01T12:34:56.123456789Z",
        "identity": "jellyfin-svc"
    },
    "current_operation": {
        "id": "e5f6g7h8-…",
        "type": "start",
        "source": "admin"
    },
    "health": "healthy",
    "uptime_seconds": 86400,
    "definition_removed": false,
    "warnings": []
}
```

| Field | Type | Meaning |
|---|---|---|
| `state` | string | §4.B. |
| `cause` | string or null | Why the service last transitioned. §4.B. |
| `status_text` | string or null | The most recent status string the service sent (§4.19). |
| `current_job` | object or null | The current main job, or null if none. |
| `current_operation` | object or null | The current operation, or null if none. |
| `health` | string or null | `healthy`, `unhealthy`, `unknown`, or null when the service has no health check configured. |
| `uptime_seconds` | integer or null | Whole seconds since the current job started. Null when nothing is running. |
| `definition_removed` | bool | True while the service's definition has been withdrawn and an instance is still draining (§4.12). |
| `warnings` | array of objects | Conditions worth an operator's attention. |

`current_job` carries `id`, `type` (§4.B), `pid`, `started_at` and
`identity`. `pid` and `started_at` are independently nullable.
`identity` is the identity string the manager resolved for the
execution, which is not necessarily what the resulting token contains.

`current_operation` carries `id`, `type` and `source` (§4.B).

The manager MUST clear `status_text` to null at the start of every
activation generation. A status string from a previous incarnation MUST
NOT survive a restart and be reported as though it described the current
process.

### Status warnings

`warnings` in the status shape is an array of **objects**, not strings:

```json
{"path": "/sys/fs/cgroup/peinit/jellyfin/health",
 "type": "health",
 "detected_at": "2026-06-01T12:34:56.123456789Z"}
```

| Field | Type | Meaning |
|---|---|---|
| `path` | string | What the warning is about. |
| `type` | string | The kind of warning. §4.B. |
| `detected_at` | string | When the manager noticed. §4.5. |

A client MUST accept a `type` it does not recognise and MUST NOT discard
the warning, since a warning it cannot classify is still one an operator
should see.

## list

Returns every service the caller may query, with a compact summary.

```json
{
    "status": "ok",
    "services": [
        {"service": "jellyfin", "state": "active",
         "cause": "explicit_start", "health": "healthy"},
        {"service": "registryd", "state": "active",
         "cause": "dependency_start", "health": null}
    ]
}
```

Exactly four fields per entry. Services the caller may not query are
omitted (§4.7).

A service whose definition has been withdrawn is listed, and the list
entry does not say so. A client that needs to know MUST issue a
`status`.

## operation-status

Returns one operation by identifier.

```json
{
    "status": "ok",
    "operation": {
        "id": "e5f6g7h8-…",
        "type": "start",
        "service": "jellyfin",
        "source": "admin",
        "state": "completed",
        "result": "active",
        "merged_into": null,
        "error": null,
        "requested_at": "2026-06-01T12:34:56.123456789Z",
        "started_at": "2026-06-01T12:34:56.223456789Z",
        "completed_at": "2026-06-01T12:34:58.923456789Z"
    }
}
```

| Field | Meaning | Present when |
|---|---|---|
| `id` | The operation's identifier. | Always. |
| `type` | §4.B. | Always. |
| `service` | The target. | Always. |
| `source` | Why the manager created it. §4.B. | Always. |
| `state` | §4.B. | Always. |
| `result` | The resulting service state. | `completed`. |
| `error` | Why it did not complete. | `failed`, `cancelled`, `aborted`. |
| `merged_into` | The surviving operation's identifier. | `merged`. |
| `requested_at` | When it was created. | Always. |
| `started_at` | When it began executing. | Once running. |
| `completed_at` | When it reached a terminal state. | Once terminal. |

Fields that do not apply to the current state MUST be null.

`error` carries a reason for all three non-success terminal states, not
only for `failed`. A client MUST NOT read a non-null `error` as meaning
the operation failed — it MUST read `state` for that. Cancellation and
abortion have reasons worth reporting, and a separate field for each
would give a client three places to look for one fact.

## Retention

The manager MUST hold an operation record for at least a grace period
after it reaches a terminal state, so that a client polling for the
result can retrieve it. The value a Peios service manager uses is in
§4.A.

An identifier that never existed, and one whose record has been dropped
after its grace period, MUST both be answered `UNKNOWN_OPERATION`. A
client MUST NOT distinguish them, and MUST treat `UNKNOWN_OPERATION`
after a successful acknowledgement as meaning the result is no longer
available rather than that the operation never ran.
