---
title: Operations
description: A requested state machine action as a first-class object — every control command creates one rather than mutating state directly.
---

An operation is a requested state machine action on a service, as a
first-class object. Control commands do not mutate state directly: every
one creates an operation that is validated, queued, resolved against
whatever else is in flight, and executed by the event loop.

Operations exist because peinit serves concurrent callers —
administrative tools, automated triggers, other services. Without them,
two commands arriving together collide with whatever behaviour falls
out; with them, the resolution is explicit and observable.

## Lifecycle

```
Pending --> Running --> Completed
  |           |
  +-> Merged  +-------> Failed
  |           |
  +-> Cancelled +-----> Aborted
  |
  +-> Failed
```

| State | Meaning |
|---|---|
| Pending | Validated and queued, waiting on a precondition. |
| Running | Executing. |
| Completed | The goal was reached. Start: Active for Simple, Completed or Inactive for Oneshot. Stop: the service is no longer running. Reload: the reload resolved. |
| Failed | The goal was not reached — or the operation's maximum lifetime expired while it was still Pending. |
| Merged | Merged into an existing identical operation, whose identifier is recorded. |
| Cancelled | Terminated while Pending. It never executed. |
| Aborted | Terminated while Running. |

Cancelled and Aborted are the same idea at different points: never ran
versus was running. Why it happened is a property of the event, not of
the state.

Two things reach Aborted. A conflicting operation superseding this one,
and a Restart whose target's definition is withdrawn while its stop leg
is draining — the stop still finishes, but there is nothing to start, so
the operation is aborted with the reason
`definition_removed_during_restart_stop_leg` (§3.8).

## Fields

```
Operation {
    id:               GUID
    operation_type:   enum    // Start, Stop, Restart, Reload, Reset
    service:          string
    state:            enum
    created_at_ns:    u64
    started_at_ns:    u64?
    completed_at_ns:  u64?
    source:           enum
    caller:           token_summary?   // admin-initiated only
    result:           string?
    merged_into:      GUID?
}
```

## Sources

Why peinit created the operation:

| Source | Meaning |
|---|---|
| `Admin` | A control client asked for it. |
| `Boot` | The Phase 2 boot plan. |
| `Shutdown` | The shutdown lifecycle. |
| `DependencyPropagation` | A start operation created one for an unsatisfied dependency. |
| `RestartPolicy` | A restart policy generated a start. |
| `Timer` | A timer trigger fired. |
| `BindsToRecovery` | A bound target returned to Active. |
| `BindsToPropagation` | A bound target stopped. |
| `ConflictResolution` | A conflict evicted the running service. |
| `OnFailure` | A failed service's fallback handler. |

`Shutdown` is declared and labelled but not currently produced: shutdown
transitions services and signals them directly, without creating
operations for the stops (§12.2).

## The types

**Start** creates a job for the target. Unsatisfied dependencies produce
their own start operations with source `DependencyPropagation`. It
completes when the service reaches Active, Completed or Inactive as
appropriate, or Skipped when pre-start conditions do not hold.

**Stop** sends SIGTERM, arms `StopTimeout`, escalates to SIGKILL. It
completes when the service reaches Inactive, or Failed after a conflict
eviction or bound-dependency propagation.

**Restart** is a stop then a start, tracked under one identifier across
both phases, and the type stays `Restart` throughout for observability.

**Reload** issues the reload command or signal (§6.5) and completes when
the reload resolves. Unlike the other lifecycle commands it defaults to
not waiting — the caller gets the identifier immediately.

**Reset** clears Failed, Abandoned or Skipped, taking the service to
Inactive. It is synchronous.

## Timeouts

A start, reload or reset inherits the target's `StartTimeout` as its
maximum lifetime; a stop inherits `StopTimeout`. A restart has two legs,
each enforced against its own timeout, with the sum as the overall
lifetime.

**The clock starts at creation, including queue time.** From the
caller's point of view they have been waiting since they sent the
command, not since peinit got round to it. A start that sits Pending
behind a stop for longer than `StartTimeout` fails without ever running.

## Retention

Pending and Running operations are held in memory. A terminal operation
is emitted as an event and dropped after a grace period of 60 seconds —
long enough for a polling client to collect the result.

peinit keeps no operation history, for the same reason it keeps no job
history. eventd is the historian.
