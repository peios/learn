---
title: The Job View
description: The one JSON object by which a submitted job is reported on either channel — its fields, its five states and what each nullable field means in each, its causes, and how long it is retained.
---

The job view is the shape every successful response on this channel
carries, and the shape `job-status` and `job-list` return on the
control channel (§4.14). It is defined once, here.

```json
{
    "id": "0190a3b2-…",
    "type": "submitted",
    "state": "running",
    "cause": null,
    "submitter": "S-1-5-80-…",
    "identity": "S-1-5-21-…",
    "logon_session": 1042,
    "description": "Backup of docs",
    "image_path": "/usr/bin/peios-backup",
    "pid": 4521,
    "ready": null,
    "exit_code": null,
    "exit_signal": null,
    "status_text": "Backing up /home/u/docs (3/5)",
    "progress": {"current": 812, "total": 2048, "bounded": true,
                 "unit": "items"},
    "created_at": "2026-06-01T12:34:56.123456789Z",
    "started_at": "2026-06-01T12:34:56.223456789Z",
    "ended_at": null
}
```

| Field | Type | Meaning |
|---|---|---|
| `id` | string | The job's identifier. |
| `type` | string | Always `submitted` on this channel. §4.B |
| `state` | string | §7.B. |
| `cause` | string or null | Why the job ended, where the manager decided it. §7.B |
| `submitter` | string | The submitter's user SID. |
| `identity` | string | The job identity's user SID. |
| `logon_session` | integer | The job identity's logon session identifier. |
| `description` | string | As submitted. |
| `image_path` | string | As submitted. |
| `pid` | integer or null | The process identifier, while there is a process. |
| `ready` | bool or null | For a `notify` job: whether `READY=1` has arrived. Null for a `none` job. |
| `exit_code` | integer or null | The exit code, when the process exited. |
| `exit_signal` | integer or null | The signal, when the process was killed. |
| `status_text` | string or null | The most recent `STATUS` the job sent (§4.19). |
| `progress` | object or null | The most recent progress the job sent (§4.19). |
| `created_at` | string | When the record was created. §4.5 |
| `started_at` | string or null | When exec was confirmed. |
| `ended_at` | string or null | When the job became terminal. |

A field that does not apply MUST be present and null, never omitted.

`identity` and `submitter` are user SIDs. A client that needs the
identity's groups, privileges or integrity does not get them here;
they are the job's, not the view's.

`progress` carries `current` (integer), `total` (integer or null),
`bounded` (bool) and `unit` (string or null), in the representation
§4.19 defines. A progress object whose `total` is null is either
unbounded or not yet bounded, and `bounded` distinguishes them.

## States

| State | Process? | Terminal? | Meaning |
|---|---|---|---|
| `created` | Not yet | No | The record exists; exec has not been confirmed. Never visible on this channel — a `submit` is answered only after leaving it. |
| `running` | Yes | No | Exec succeeded and the process is alive. |
| `completed` | No | Yes | The process exited with `0` or a code in `success_exit_codes`. |
| `failed` | No | Yes | The process exited otherwise, was killed by a signal, or never ran because setup failed. |
| `abandoned` | Yes, unkillably | Yes | The process survived the kill. The manager has stopped supervising it. |

These are the states of every job the manager runs, not a set
invented for this channel; a client that understands them for a
service's main job understands them here. A stopped job whose
process died to the termination signal is `failed` with
`exit_signal` set, and `cause` says the stop was asked for.

Which fields are populated is a function of state, and a client MAY
rely on it:

| State | `pid` | `started_at` | `ended_at` | `exit_code` / `exit_signal` |
|---|---|---|---|---|
| `running` | set | set | null | null |
| `completed` | null | set | set | exactly one set |
| `failed`, process ran | null | set | set | exactly one set |
| `failed`, setup failed | null | null | set | both null |
| `abandoned` | set | set | set | both null |

`exit_code` and `exit_signal` are never both set: a process exits or
is killed. For `abandoned`, `ended_at` records when supervision
stopped; nothing exited.

## Causes

`cause` is set when the manager itself brought the job to its end, or
decided it could not start, and null when the process ended of its own
accord — a clean exit, a crash, a signal from elsewhere.

| Value | State | Meaning |
|---|---|---|
| `parent_setup_failure` | `failed` | The manager could not prepare the launch: no token, no cgroup, no fork. No process existed. |
| `pre_exec_failure` | `failed` | The child's setup between fork and exec failed, or exec itself did. |
| `readiness_timeout` | `failed` | A `notify` job did not send `READY=1` within `readiness_timeout`. The manager stopped it. |
| `timeout` | `failed` | The job ran longer than `timeout`. The manager stopped it. |
| `explicit_stop` | `failed` | A `stop` or `job-stop` was issued and the process died to it. |
| `shutdown` | `failed` | The system was shutting down and the manager stopped it. |
| `process_unkillable` | `abandoned` | The process survived the kill. |

A `stop` whose process handled the termination signal and exited `0`
produces `completed` with cause `explicit_stop`: the manager asked, the
process agreed, and both facts are recorded.

## Retention

The manager MUST hold a terminal job's record for at least a grace
period after it reaches a terminal state, so that a submitter polling
for the outcome can retrieve it. The value a Peios service manager
uses is in §7.A.

An identifier that never existed and one whose record has been dropped
MUST both be answered `UNKNOWN_JOB`, and a submitter MUST NOT
distinguish them (§4.14's rule for operations, applied to jobs).

A job that is terminal stops counting against its submitter's quota at
once; its record's retention is for the submitter's benefit, not a
cost to it.
