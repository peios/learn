---
title: Transition Causes
description: Every transition carries a cause — the taxonomy, which causes are restart-eligible, OnFailure, the loop guard and the logging contract.
---

Every transition carries a cause recording why it happened. peinit
tracks both the current state and the cause of the most recent
transition, and the cause determines restart eligibility, `OnFailure`
behaviour, and what an administrator is told.

## The taxonomy

| Cause | Leads to | Meaning |
|---|---|---|
| `ExplicitStart` | Starting | An administrator, an `OnFailure` handler, or a boot plan started it. |
| `ExplicitStart` | Inactive | An explicit start on a Skipped service, clearing it so the conditions are re-evaluated. |
| `DependencyStart` | Starting | Started to satisfy another service's dependency. |
| `RestartPolicy` | Starting | An automatic restart after a backoff delay. |
| `BindsToRecovery` | Starting | A bound dependency returned to Active. |
| `Timer` | Starting | A timer trigger fired. |
| `ExplicitStop` | Stopping | An administrator requested a stop. |
| `ExplicitReload` | Reloading, Active | A reload was issued and resolved. |
| `ExplicitReset` | Inactive | An administrator cleared Failed, Abandoned or Skipped. |
| `ConflictEviction` | Stopping | A conflicting service started; this one lost. |
| `BindsToPropagation` | Stopping | A bound dependency stopped. |
| `ShutdownWave` | Stopping, Failed | The system is shutting down. Active and Reloading services go to Stopping; Starting services go straight to Failed. |
| `ProcessCrash` | Failed, Backoff | The main process exited unexpectedly. |
| `CleanExit` | Inactive | A Simple process exited successfully with a policy other than Always. |
| `CleanExitRestart` | Backoff | A Simple process exited successfully under `RestartPolicy=Always`. |
| `ReadinessTimeout` | Failed, Backoff | `StartTimeout` expired before readiness. |
| `WatchdogTimeout` | Failed, Backoff | A keepalive did not arrive in time. |
| `HealthCheckFailure` | Failed, Backoff | `HealthCheckRetries` consecutive failures. |
| `PreHookFailure` | Failed, Backoff | An `ExecStartPre` hook exited non-zero, or its token failed, or the start timed out during hooks. |
| `ParentSetupFailure` | Failed, Backoff | A parent-side failure before the fork. No child was created. |
| `PreExecFailure` | Failed, Backoff | Post-fork setup failed before exec, reported through the error pipe. |
| `DependencyFailure` | Failed | A `Requires` dependency entered Failed. |
| `RestartBudgetExhausted` | Failed | `RestartMaxRetries` reached. |
| `CycleDetected` | Failed | The service is part of a dependency cycle. |
| `ValidationError` | Failed | The definition failed graph validation. |
| `AssertionError` | Failed | A start-time assert failed. |
| `ConditionSkipped` | Skipped | A start-time condition failed. |
| `ProcessUnkillable` | Abandoned | Processes survived SIGKILL. |

## Restart eligibility

Causes fall into four classes, and the class decides whether the restart
policy is consulted at all.

**Restart-eligible.** peinit consults `RestartPolicy` and the budget. If
a restart is allowed and the budget holds, the service goes to Backoff
and then to Starting; otherwise Failed.

`ProcessCrash`, `WatchdogTimeout`, `HealthCheckFailure`,
`ReadinessTimeout`, `PreHookFailure`, `PreExecFailure`,
`ParentSetupFailure`.

> [!NOTE]
> The startup failures are restart-eligible because a transient problem
> during startup should get another go. A pre-hook that failed because a
> network mount was briefly unavailable deserves a retry rather than an
> immediate give-up.

**Always-only.** `CleanExitRestart` applies when a Simple service exits
successfully and the policy is Always. It uses the same backoff and the
same budget as a failure, which is what stops a daemon that exits
cleanly in a tight loop from bypassing throttling entirely. It is never
treated as a `ProcessCrash`, and both status and events make clear the
process succeeded and was restarted only because the policy says so.

`CleanExit` is its non-restarting counterpart: straight to Inactive,
consulting neither policy nor budget.

**Budget-exempt.** `BindsToRecovery` takes a service from Failed to
Starting when its binding target returns. It is not subject to the
policy or the budget, because the service did not fail on its own — it
was stopped because its dependency went away.

**Never-restart.** peinit does not consult the policy at all:
`ExplicitStop`, `ExplicitReset`, `ShutdownWave`, `ConflictEviction`,
`BindsToPropagation`, `ProcessUnkillable`, `RestartBudgetExhausted`,
`ValidationError`, `CycleDetected`, `DependencyFailure`,
`AssertionError`, `ConditionSkipped`. Retrying cannot help with any of
them.

## OnFailure

When a service enters Failed and its definition names an `OnFailure`
service, peinit starts that service — with the exceptions below.
`OnFailure` fires on *entry* to Failed, and Failed to Failed is not a
transition, so it fires at most once per failure.

It does not fire for:

- **`ShutdownWave`** — no new service starts during shutdown, so a
  fallback would be both impossible and pointless.
- **`ValidationError`, `CycleDetected`, `DependencyFailure`,
  `AssertionError`** — these are definition or graph breakage rather
  than runtime degradation. A broken definition cannot meaningfully
  trigger a fallback, and the fallback would probably sit in the same
  broken graph.

It fires for everything else, including `ProcessCrash`,
`WatchdogTimeout`, `HealthCheckFailure`, the startup failures, and
`RestartBudgetExhausted` on a non-Critical service.

For a **Critical** service exhausting its budget, the reboot takes
precedence and no fallback is started. The suppression keys on the cause
and the service's `ErrorControl` rather than on whether a reboot was
actually scheduled.

`OnFailure` is for graceful degradation — the main web interface fails,
so start a minimal emergency endpoint. It is not for monitoring or
alerting, which is eventd's job.

### The loop guard

An `OnFailure` handler can fail and carry its own `OnFailure`, so a
misconfiguration where A's handler is B and B's is A could run forever.
peinit bounds the chain originating from one failure two ways: it tracks
the set of services already started as handlers for that failure and
will not start one already in the set, and it will not follow the chain
past a fixed depth of 16. When either trips, peinit records an
`on_failure.loop_suppressed` event naming which, and stops.

A chain entry is retired two ways.

**The handler stopped needing tracking.** Completed, Inactive, Skipped or
Abandoned — it ended, gave up, or became unkillable.

**The handler arrived.** It has been dependent-satisfying for its
`RestartWindow` — the same window that resets a restart budget (§6.4).
That is peinit's existing test for a service having genuinely taken over
rather than merely come up, and it is what ends the originating failure:
a later failure of that handler is a new one, starting a fresh chain.

The distinction matters in both directions. Without the second rule, a
handler that runs healthily for days holds a slot forever, so a
degradation path handing off through several healthy layers exhausts its
own depth budget by working. But retiring on `Active` alone would break
the guard entirely: `Readiness=Alive` reports Active the instant the
process spawns, so two services naming each other as handlers would hand
off forever, with no delay and no cost — an `OnFailure` start is not a
restart and spends no restart budget. Only a handler that *held* is
treated as having arrived.

## The logging contract

Every state transition produces a record covering four things: what
failed, why it failed, what peinit did about it, and what the
administrator should do. Cryptic failure messages are a defect. A reboot
loop caused by a configuration error with an opaque message is the worst
outcome the system has, and the cause taxonomy exists so that the "why"
is never a guess.
