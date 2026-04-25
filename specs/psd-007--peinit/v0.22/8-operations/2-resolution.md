---
title: Conflict Resolution
---

When a new operation is requested and an existing operation for the
same service is Pending or Running, peinit MUST apply the conflict
resolution rules defined in this section.

## Same-type merging

If the new operation has the same type as the existing operation,
peinit MUST merge them. The new caller receives the existing
operation's GUID. From the caller's perspective, their request is
in progress.

| Existing | New | Resolution |
|---|---|---|
| Start | Start | Merge. |
| Stop | Stop | Merge. |
| Reload | Reload | Merge. |

Restart is not mergeable -- a new restart while one is in progress
is queued (see cross-type rules below).

## Cross-type conflicts

| Existing | New | Resolution |
|---|---|---|
| Start (Pending) | Stop | Cancel the start. Create stop operation. |
| Start (Running) | Stop | Abort the start. Create stop operation. |
| Stop (Pending or Running) | Start | Queue start as Pending. Executes after stop completes. |
| Stop (Pending or Running) | Restart | Queue restart as Pending. Executes after stop completes. |
| Restart (Pending) | Stop | Cancel the restart. Create stop operation. |
| Restart (Running) | Stop | Abort the restart. Create stop operation. |
| Restart (Pending or Running) | Start | Merge into the restart (restart already includes a start). |
| Any (Pending or Running) | Reset | Reject. Reset MUST NOT be issued while an operation is in progress. |
| Start (Pending) | Restart | Cancel the pending start. Queue restart as Pending. |
| Start (Running) | Restart | Queue restart as Pending. Executes after start completes. |
| Reload (Running) | Stop | Abort the reload. Create stop operation. |
| Reload (Running) | Restart | Abort the reload. Create restart operation. |

## Resolution principles

1. **Stop wins over start.** An explicit stop always takes
   priority. The admin said stop, so stop. A queued start can
   follow after.
2. **Later operations supersede earlier ones.** If an admin sends
   start then immediately sends stop, the stop wins and the start
   is cancelled.
3. **Merging is transparent.** The caller of a merged operation
   receives the original operation's GUID. They do not know or
   care that their request merged.

## Dependency propagation

When a start operation executes and the target service has
unsatisfied dependencies, peinit MUST create start operations for
those dependencies:

- **Requires dependencies:** start operations with source
  `DependencyPropagation`. If any dependency's start operation
  fails, the parent operation fails with result DependencyFailure.
- **Wants dependencies:** start operations with source
  `DependencyPropagation`. If a Wants dependency's start operation
  fails, the parent operation continues.
- **BindsTo recovery:** when a bound service returns to Active,
  peinit MUST create start operations (source: `BindsToRecovery`)
  for any dependents that are Failed with cause
  BindsToPropagation.

Dependency-created operations follow the same conflict resolution
rules as admin-created operations. If a dependency is already
starting (due to another service also depending on it), the
operations merge.

## Restart policy integration

When a service transitions to Failed with a restart-eligible cause
(§5.2), peinit MUST create a start
operation with source `RestartPolicy` after the configured
RestartDelay. This operation goes through normal validation and
conflict resolution -- if an admin has already sent a stop or the
restart budget is exhausted, the operation is rejected.

BindsTo recovery restarts (source: `BindsToRecovery`) are NOT
subject to the restart budget. They are created when a bound
dependency returns to Active, not in response to a service
failure. See §6.1.

## Timer integration

When a timerfd fires, peinit creates operations based on the
service's current state:

| Service type | Current state | Action |
|---|---|---|
| Oneshot | Inactive/Completed/Failed | Create start operation (source: Timer). |
| Oneshot | Active/Starting | Set pending flag (one catch-up run). No operation created. |
| Simple | Active/Starting | No-op. Log the firing. |
| Simple | Inactive/Failed | Create start operation (source: Timer). |

The catch-up mechanism for Oneshot services creates a start
operation when the current execution completes. Multiple missed
firings collapse into one pending run.

Timer-created operations follow normal conflict resolution.

## Bulk operations

Shutdown and boot are system lifecycle events, not operations. They
produce operations (stop/start for individual services) but are not
operations themselves. There is no "shutdown operation" -- shutdown
is a mode that peinit enters, which then generates per-service
stop operations.
