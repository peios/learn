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
  |
  +--> Failed
```

| State | Meaning |
|---|---|
| Pending | Validated and queued. Waiting for preconditions (e.g., a prior stop to complete before a queued start can run). |
| Running | Actively executing. For start: the service is transitioning through Starting. For stop: the service is in Stopping. |
| Completed | The operation achieved its goal. Start: service reached Active for Simple, or Completed/Inactive for Oneshot. Stop: service reached Inactive or Failed (the service is no longer running). Reload: reload acknowledged. |
| Failed | The operation did not achieve its goal. Start: service reached Failed. Stop: timed out (service did not exit within StopTimeout + SIGKILL escalation). Pending operations can also fail before execution if their maximum lifetime expires while queued, because operation timeout clocks start at creation time. |
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
                              // BindsToPropagation, ConflictResolution,
                              // OnFailure
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
| BindsToPropagation | A `BindsTo` target stopped and generated a stop operation for the bound dependent. |
| ConflictResolution | A `Conflicts` relationship generated a stop operation for the currently active conflicting service. |
| OnFailure | A failed service's `OnFailure` handler generated a fallback start operation. |

### Start

Creates a job for the target service. If the service has
unsatisfied dependencies, start operations are created for each
dependency (source: DependencyPropagation). The operation completes
when the service reaches Active (Simple) or Completed/Inactive
(Oneshot), or when pre-start conditions place the service in
Skipped.

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
type remains Restart for observability. The operation completes when the
service reaches its normal successful start target after the restart:
Active for Simple services, Completed/Inactive for Oneshot services, or
Skipped when pre-start conditions place the service in Skipped.

If the target service becomes definition-removed while a Restart operation is
Running in its stop phase, the stop phase still drains the existing instance,
but peinit MUST NOT begin the start phase. When the stopped instance exits,
peinit MUST abort the Restart operation with reason
`definition_removed_during_restart_stop_leg` and then perform the normal final
service-removal discard for that definition-removed entry (§3.5, §11.1).

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

During shutdown, a generated Stop operation for a service in a later
graceful-stop wave can expire while it is still Pending because its
dependency wave has not yet become eligible. That timeout fails the
operation object and any waiters observing that operation; it does
not authorize peinit to send SIGTERM or SIGKILL to the service before
the shutdown dependency ordering in §10.1 permits that service's wave
to run. Shutdown execution continues to own service signalling and
cgroup escalation for the service independently of the timed-out
operation object.

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

When one runtime step produces more than one operation lifecycle event, peinit
MUST emit the events in causal order before committing the retained state for
that step. For terminal pre-start graph dispatch, the terminal event for the
operation whose pre-start outcome satisfied or failed the graph input MUST
precede `operation.requested` events for newly dispatched graph operations,
which MUST preserve graph dispatch order.

All operation lifecycle event payloads include:

- `operation_id` -- operation GUID.
- `type` -- operation type.
- `service` -- target service name.
- `source` -- operation source.
- `caller` -- caller token summary for admin-initiated operations, or
  null for lifecycle-generated operations.
- `state` -- operation state after the transition represented by the
  event.

Event-specific fields are:

- **operation.requested** -- operation created. State is `pending`.
- **operation.started** -- execution began (Pending -> Running). State
  is `running`.
- **operation.completed** -- succeeded. State is `completed`.
  Includes `duration_ns` (`completed_at - created_at`) and `result`.
- **operation.failed** -- did not achieve its goal. State is `failed`.
  Includes `duration_ns` (`completed_at - created_at`) and
  `failure_reason`.
- **operation.cancelled** -- superseded or explicitly cancelled before
  execution. State is `cancelled`. Includes `reason`.
- **operation.merged** -- merged into an existing operation. State is
  `merged`. Includes `merged_into`.
- **operation.aborted** -- was running, interrupted. State is
  `aborted`. Includes `duration_ns` (`completed_at - created_at`) and
  `reason`.

## Control protocol integration

Every lifecycle control command that creates, merges into, queues,
cancels, clears, or executes an operation returns an operation GUID:

```json
{"status": "ok", "operation_id": "a1b2c3d4-...", "service": "jellyfin", "state": "active", "cause": "explicit_start", "warnings": []}
```

Callers can poll for completion via the `operation-status` command:

```json
{"command": "operation-status", "operation_id": "a1b2c3d4-..."}
```

With `wait=true`, the control socket connection stays open until
the operation reaches a terminal state.

Commands that do not create or attach to an operation do not invent
one solely for observability. `status`, `list`, and
`operation-status` use their own response shapes (§11.2). Lifecycle
commands that resolve as `ALREADY` or `NOOP` return the normal
service status response shape (§11.2) because no operation exists.
