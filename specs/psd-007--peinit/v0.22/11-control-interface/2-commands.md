---
title: Command Set
---

## Service lifecycle commands

| Command | Behaviour | Default wait |
|---|---|---|
| start | Start the service. Full pre-exec sequence. | Wait for Active or Failed. |
| stop | Send SIGTERM, escalate to SIGKILL after StopTimeout. | Wait for Inactive. |
| restart | Stop then start. | Wait for Active or Failed. |
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

For Oneshot services, the start target state is Completed (if
RemainAfterExit=1) or Inactive (if RemainAfterExit=0).

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

| Command | Inactive | Starting | Active | Reloading | Stopping | Completed | Failed | Abandoned | Skipped |
|---|---|---|---|---|---|---|---|---|---|
| start | Start | ALREADY | ALREADY | ALREADY | QUEUE | Start | Start | ERROR | Start |
| stop | NOOP | Cancel+Stop | Stop | Stop | ALREADY | Clear | NOOP | ERROR | NOOP |
| restart | Start | QUEUE | Restart | Restart | QUEUE | Start | Start | ERROR | Start |
| reload | ERROR | ERROR | Reload | ALREADY | ERROR | ERROR | ERROR | ERROR | ERROR |
| reset | NOOP | ERROR | ERROR | ERROR | ERROR | ERROR | Clear | Clear | Clear |
| status | OK | OK | OK | OK | OK | OK | OK | OK | OK |

- **ALREADY:** command is redundant. Return current state (not an
  error).
- **NOOP:** command has no effect. Return success.
- **ERROR:** command is invalid for this state. Return error with
  explanation.
- **Clear:** reset to Inactive.
- **Cancel:** abort current operation then proceed.
- **QUEUE:** operation is queued as Pending. Executes after the
  current operation completes (§8.2).

## Status response

The status response for a service MUST include:

```json
{
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
    "warnings": []
}
```

The `status_text` field carries the most recent `STATUS=` string
sent by the service via sd_notify. If the service has never sent
`STATUS=`, the field MUST be null. peinit MUST clear `status_text`
to null at the start of each new activation generation (restart).
A STATUS= from a previous incarnation MUST NOT persist across
restarts.

The `warnings` array MUST include leaked sub-cgroups, if any (see
§4.2).
