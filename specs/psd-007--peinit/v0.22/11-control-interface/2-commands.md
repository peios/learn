---
title: Command Set
---

## Service lifecycle commands

| Command | Behaviour | Default wait |
|---|---|---|
| start | Start the service. Full pre-exec sequence. | Wait for Active or Failed. |
| stop | Send SIGTERM, escalate to SIGKILL after StopTimeout. | Wait for Inactive. |
| restart | Stop then start. | Wait for the successful start target or Failed. |
| reload | Send reload signal/command (ExecReload or SIGHUP). | Immediate (wait defaults to false). |
| reset | Clear Failed, Abandoned, or Skipped state. Transition to Inactive. | Immediate. |
| status | Return current state, transition cause, PID, uptime, health, warnings, current job, current operation. | Immediate. |
| list | Return all services and their states. Filtered to services the caller can query. | Immediate. |

### Access rights per command

| Command | Required right |
|---|---|
| start | SERVICE_START |
| stop | SERVICE_STOP |
| restart | SERVICE_STOP + SERVICE_START |
| reload | SERVICE_INTERROGATE |
| reset | SERVICE_STOP |
| status | SERVICE_QUERY_STATUS |
| list | (returns only services with SERVICE_QUERY_STATUS) |

## System commands

| Command | Behaviour | Required right |
|---|---|---|
| shutdown | Initiate graceful shutdown. Requires `type` field: poweroff, reboot, or halt. | SYSTEM_SHUTDOWN |
| reload-config | Re-read all service definitions from the registry. Rebuild the dependency graph. | SYSTEM_RELOAD_CONFIG |
| operation-status | Return the current state of an operation by GUID. | SERVICE_QUERY_STATUS on the target service. |

## Wait semantics

By default, lifecycle commands block until the operation reaches a
terminal state. The client MAY set `"wait": false` for immediate
acknowledgment.

When waiting, the response is sent when:

- The service reaches the target state (Active for start, Inactive
  for stop).
- The service enters Failed state.
- The operation timeout expires.

Lifecycle commands that create, merge into, queue, cancel, clear, or
execute an operation return the lifecycle operation acknowledgement
shape from §8.1. With `wait=false`, peinit returns that response
after accepting the operation. With `wait=true`, peinit returns the
same response shape after the operation resolves, with the current
service `state`, `cause`, and `warnings` observed at that time.
`warnings` is an array of human-readable warning strings.

For Oneshot services, the start and restart target state is Completed
(if RemainAfterExit=1) or Inactive (if RemainAfterExit=0).

Reload defaults to `wait=false`. If `wait=true`, the connection
stays open until the Reloading state resolves. The response
includes `"mode": "confirmed"` or `"mode": "advisory"` (§5.3).

## reload-config semantics

`reload-config` loads a new snapshot of all service definitions
from the registry. It MUST NOT live-update the running system.

The reload is atomic: peinit builds and validates a complete new
graph snapshot in memory and only swaps it in if validation
succeeds. If validation fails, the previous generation remains
active and errors are returned to the caller.

- All service definitions are re-read from the registry.
- A new dependency graph is built and validated.
- Running services are NOT affected -- they continue on their
  activation generation.
- New definitions take effect on the next start, restart, or
  trigger firing.
- New services become available for start commands immediately.
- Timer triggers on inactive services are re-evaluated.

## Command x state matrix

Commands sent to a service in an unexpected state return an error,
not a silent no-op.

| Command | Inactive | Starting | Active | Reloading | Stopping | Completed | Backoff | Failed | Abandoned | Skipped |
|---|---|---|---|---|---|---|---|---|---|---|
| start | Start | MERGE | ALREADY | ALREADY | QUEUE | Start | MERGE | Start | ERROR | Start |
| stop | NOOP | Cancel+Stop | Stop | Stop | MERGE | Clear | Cancel | NOOP | ERROR | NOOP |
| restart | Start | QUEUE | Restart | Restart | QUEUE | Start | Restart | Start | ERROR | Start |
| reload | ERROR | ERROR | Reload | MERGE | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR |
| reset | NOOP | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR | Clear | Clear | Clear |
| status | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |

- **ALREADY:** the service is already in the command's target state
  and no operation of this type is in flight. Return current state
  using the status response shape (not an error).
- **MERGE:** an operation of this type is already in progress. The
  command merges into it (§8.2); the caller receives the in-flight
  operation's GUID and, when waiting, blocks on that operation's
  terminal state.
- **NOOP:** command has no effect. Return the status response shape.
- **ERROR:** command is invalid for this state. Return error with
  explanation.
- **Clear:** reset to Inactive.
- **Cancel:** abort current operation then proceed.
- **QUEUE:** operation is queued as Pending. Executes after the
  current operation completes (§8.2).

In the **Backoff** column the service is down with an automatic
restart pending (§5.1): `start` merges into that pending restart and
honors the backoff delay; `stop` cancels the pending restart (the
service goes Inactive); `restart` cancels the automatic restart and
performs an admin-initiated one; `reload` and `reset` are invalid
(no process exists).

## Status response

The status response for a service MUST include:

```json
{
    "status": "ok",
    "service": "jellyfin",
    "state": "active",
    "cause": "explicit_start",
    "status_text": "Listening on port 8096",
    "current_job": {
        "id": "a1b2c3d4-...",
        "type": "service_main",
        "pid": 1234,
        "started_at": "...",
        "identity": "jellyfin-svc"
    },
    "current_operation": {
        "id": "e5f6g7h8-...",
        "type": "start",
        "source": "admin"
    },
    "health": "healthy",
    "uptime_seconds": 86400,
    "definition_removed": false,
    "warnings": []
}
```

The response `status` field MUST be `"ok"` for a successful status
query. `current_job` MUST be the current service-main job object
when one exists and null otherwise. `current_operation` MUST be the
current service operation object when one exists and null otherwise.

The `status_text` field carries the most recent `STATUS=` string
sent by the service via sd_notify. If the service has never sent
`STATUS=`, the field MUST be null. peinit MUST clear `status_text`
to null at the start of each new activation generation (restart).
A STATUS= from a previous incarnation MUST NOT persist across
restarts.

The `warnings` array MUST include leaked sub-cgroups, if any (see
§4.2).

The `definition_removed` field MUST be `true` when the service's
definition has been removed from the registry but a running instance
is still draining (§3.5), and `false` otherwise. A `start`,
`restart`, or `reload` on a definition-removed service returns
`UNKNOWN_SERVICE`; `stop` drains it.

The `health` field MUST be one of:

| Value | Meaning |
|---|---|
| `healthy` | The most recent HealthCheck passed. |
| `unhealthy` | HealthCheck is currently failing (within HealthCheckRetries; the service has not yet failed out). |
| `unknown` | A HealthCheck is configured but has not produced a result yet. |
| `null` | No HealthCheck is configured for the service. |

## list response

`list` returns every service the caller can query, with a compact
per-service summary. Services for which the caller lacks
`SERVICE_QUERY_STATUS` are omitted (not denied).

```json
{
    "status": "ok",
    "services": [
        {"service": "jellyfin", "state": "active", "cause": "explicit_start", "health": "healthy"},
        {"service": "registryd", "state": "active", "cause": "dependency_start", "health": null}
    ]
}
```

## operation-status response

`operation-status` returns the state of a single operation by GUID.
If the GUID is unknown or its record has been dropped after the
retention grace (§8.1), peinit MUST return the `UNKNOWN_OPERATION`
error (§11.1).

```json
{
    "status": "ok",
    "operation": {
        "id": "e5f6g7h8-...",
        "type": "start",
        "service": "jellyfin",
        "source": "admin",
        "state": "completed",
        "result": "active",
        "merged_into": null,
        "error": null,
        "requested_at": "...",
        "completed_at": "..."
    }
}
```

The operation `state` MUST be one of `pending`, `running`,
`completed`, `failed`, `cancelled`, `merged`, or `aborted` (§8).
`result` carries the resulting service state on success; `error`
carries the failure reason on `failed`; `merged_into` carries the
surviving operation's GUID on `merged`. Fields that do not apply
to the current `state` MUST be `null`.
