---
title: Query and Job Commands
description: The three commands that read service state and change nothing — status, list and operation-status — the three that observe and stop submitted jobs, and how long results are retained.
---

Three commands read service state and change nothing. Three more
observe and stop submitted jobs (§7), and are here because a client of
this channel sees jobs alongside services.

## status

Returns everything the manager knows about one service.

```json
{
    "status": "ok",
    "service": "jellyfin",
    "display_name": "Jellyfin",
    "description": "Media server for the living room.",
    "state": "active",
    "cause": "explicit_start",
    "status_text": "Listening on port 8096",
    "progress": null,
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
| `display_name` | string or null | The definition's human-readable name. |
| `description` | string or null | The definition's human-readable description. |
| `state` | string | §4.B. |
| `cause` | string or null | Why the service last transitioned. §4.B. |
| `status_text` | string or null | The most recent status string the service sent (§4.19). |
| `progress` | object or null | The most recent progress the service sent (§4.19), in the form §7.7 gives. |
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

The manager MUST clear `status_text` and `progress` to null at the
start of every activation generation. A status string or a progress
figure from a previous incarnation MUST NOT survive a restart and be
reported as though it described the current process.

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
        {"service": "jellyfin", "display_name": "Jellyfin",
         "description": "Media server for the living room.",
         "state": "active", "cause": "explicit_start",
         "health": "healthy"},
        {"service": "registryd", "display_name": null,
         "description": null, "state": "active",
         "cause": "dependency_start", "health": null}
    ]
}
```

Exactly six fields per entry: the name, the definition's nullable
`display_name` and `description`, and the state, cause and health of
the status shape. Services the caller may not query are omitted
(§4.7).

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

## job-status

Returns one submitted job by identifier, as the job view of §7.7.

```json
{"command": "job-status", "job_id": "0190a3b2-…"}
```

```json
{"status": "ok", "job": { … }}
```

The view is §7.7's, unchanged: what a submitter sees of its job on the
jobs channel is what a client sees of it here.

## job-list

Returns every submitted job the caller may query, as job views.

```json
{"command": "job-list", "identity": "S-1-5-21-…"}
```

```json
{"status": "ok", "jobs": [ { … }, { … } ]}
```

Each entry is the full job view (§7.7). Jobs the caller may not query
are omitted (§4.7). The four filters of §4.8 — `submitter`,
`identity`, `logon_session`, `state` — narrow the result before it is
filtered by right, and the manager MUST NOT let the response reveal
whether the filters or the rights removed an entry.

Terminal jobs still within their retention period are listed; a client
that wants only live ones filters by `state`.

> [!NOTE]
> `logon_session` is what an authority uses to find everything running
> under a logon it is ending: it lists the jobs in that session and
> stops each it holds `JOB_STOP` on. A user-facing view of "my jobs"
> filters by `identity`; a broker's view of "the jobs I started"
> filters by `submitter`.

## job-stop

Stops one submitted job, with the semantics of the jobs channel's
`stop` (§7.8): the termination signal, the job's `stop_timeout`, then
the kill.

```json
{"command": "job-stop", "job_id": "0190a3b2-…", "wait": true}
```

`wait` defaults to true, and the response is the job view when the job
is terminal; with `wait: false` it is the view as soon as the stop has
been initiated. A `job-stop` on a terminal job returns the view
unchanged, with `"status": "ok"`.

This is the one command on this channel that acts on a job, and it
creates no operation: a job has no state machine to contend for (§7.6).
There is no `job-signal` here; signalling is the submitter's business,
on its own channel.

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

Job records are retained under §7.7's rule, and `UNKNOWN_JOB` carries
the same two meanings.
