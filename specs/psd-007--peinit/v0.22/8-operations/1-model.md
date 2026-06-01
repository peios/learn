---
title: Operation Model
---

An operation is a first-class object representing a requested state
machine action on a service. Instead of control commands directly
mutating service state, every command creates an operation that is
validated, queued, and executed by peinit's event loop.

Operations exist because peinit handles concurrent callers (admin
tools, remote SCM, PAC, automated triggers). Without operations,
concurrent commands collide with implementation-defined behaviour.
With operations, conflict resolution is explicit and observable.

## Lifecycle

```
Pending --> Running --> Completed
  |                      |
  +--> Merged            +--> Failed
  |                      |
  +--> Cancelled         +--> Aborted
```

| State | Meaning |
|---|---|
| Pending | Validated and queued. Waiting for preconditions (e.g., a prior stop to complete before a queued start can run). |
| Running | Actively executing. For start: the service is transitioning through Starting. For stop: the service is in Stopping. |
| Completed | The operation achieved its goal. Start: service reached Active/Completed. Stop: service reached Inactive or Failed (the service is no longer running). Reload: reload acknowledged. |
| Failed | The operation did not achieve its goal. Start: service reached Failed. Stop: timed out (service did not exit within StopTimeout + SIGKILL escalation). |
| Merged | This operation was merged into an existing identical operation. The merged-into GUID is recorded. |
| Cancelled | Terminated while Pending -- the operation never executed. |
| Aborted | Terminated while Running -- the operation was in progress and was interrupted. |

Cancelled and Aborted are the same concept (terminated before
completion) at different lifecycle points. Cancelled = never ran.
Aborted = was running. The cause (admin action, conflict
supersession) is a property of the event, not the state.

## Fields

```
Operation {
    id:           GUID        // unique identifier
    type:         enum        // Start, Stop, Restart, Reload, Reset
    service:      string      // target service name
    state:        enum        // Pending, Running, Completed, Failed,
                              // Merged, Cancelled, Aborted
    created_at:   timestamp   // when the operation was created
    started_at:   timestamp?  // when execution began
    completed_at: timestamp?  // when terminal state was reached
    source:       enum        // Admin, Boot, Shutdown,
                              // DependencyPropagation, RestartPolicy,
                              // Timer, BindsToRecovery,
                              // ConflictResolution
    caller:       token_summary?  // caller identity (admin-initiated)
    result:       string?     // human-readable result or error
    merged_into:  GUID?       // if Merged, the target operation
}
```

## Operation types

## Operation sources

Operation sources identify why peinit created an operation:

| Source | Meaning |
|---|---|
| Admin | A control client requested the operation. |
| Boot | The Phase 2 boot lifecycle generated a per-service start operation. |
| Shutdown | The shutdown lifecycle generated a per-service stop operation. |
| DependencyPropagation | A start operation created another start operation for an unsatisfied dependency. |
| RestartPolicy | A service restart policy generated a start operation. |
| Timer | A timer trigger generated a start operation. |
| BindsToRecovery | A `BindsTo` target returned to Active and generated a budget-exempt dependent start operation. |
| ConflictResolution | A `Conflicts` relationship generated a stop operation for the currently active conflicting service. |

### Start

Creates a job for the target service. If the service has
unsatisfied dependencies, start operations are created for each
dependency (source: DependencyPropagation). The operation completes
when the service reaches Active (Simple) or Completed/Inactive
(Oneshot).

### Stop

Sends SIGTERM, starts StopTimeout, escalates to SIGKILL. The
operation completes when the service reaches Inactive (clean stop)
or Failed (conflict eviction, BindsTo propagation).

### Restart

A Stop followed by a Start. Implemented as a single operation --
peinit stops the service then starts it, tracking both phases
under one operation GUID. If the service has no running process
(Inactive, Completed, Failed, Skipped), the stop phase is skipped
and peinit proceeds directly to the start phase. The operation
type remains Restart for observability. The operation completes when the service
reaches Active after the restart.

### Reload

Sends the ExecReload command or signal (§5.3). The operation
completes when the reload resolves. Unlike
other operations, reload defaults to `wait=false` -- the caller
gets the operation GUID immediately.

### Reset

Clears Failed, Abandoned, or Skipped state. Transitions the
service to Inactive. Synchronous -- completes immediately.

## Timeout

Start, reload, and reset operations inherit their target service's
StartTimeout as their maximum lifetime. Stop operations inherit
their target service's StopTimeout as their maximum lifetime.
Restart operations have two timeout legs: the stop leg uses
StopTimeout and the start leg uses StartTimeout. The maximum
restart operation lifetime is the sum of those two legs, and each
leg is still enforced against its own timeout.

The timeout clock starts at operation creation (including queue
time), not at execution. From the caller's perspective, they have
been waiting since they sent the command. For restart operations,
queue time counts against the combined operation lifetime before
the stop and start legs execute.

## Retention

peinit retains operation objects in memory while they are Pending
or Running. Terminal operations (Completed, Failed, Cancelled,
Merged, Aborted) are emitted as structured events via KMES and
dropped from memory after a grace period (default 60 seconds --
long enough for a polling client to retrieve the result).

peinit MUST NOT maintain operation history. eventd is the
historian -- it consumes these events from the KMES kernel ring
buffer.

## Event emission

peinit MUST emit a structured event via KMES (`kmes_emit`; eventd
consumes it from the kernel ring buffer, not over a socket from
peinit) at each operation lifecycle transition:

- **operation.requested** -- operation created. Includes
  operation_id, type, service, source, caller.
- **operation.started** -- execution began (Pending -> Running).
- **operation.completed** -- succeeded. Includes duration, result.
- **operation.failed** -- did not achieve its goal. Includes
  failure reason, duration.
- **operation.cancelled** -- superseded or explicitly cancelled.
- **operation.merged** -- merged into an existing operation.
  Includes merged_into GUID.
- **operation.aborted** -- was running, interrupted.

## Control protocol integration

Every control command returns an operation GUID:

```json
{"status": "ok", "operation_id": "a1b2c3d4-..."}
```

Callers can poll for completion via the `operation-status` command:

```json
{"command": "operation-status", "operation_id": "a1b2c3d4-..."}
```

With `wait=true`, the control socket connection stays open until
the operation reaches a terminal state.
