---
title: Transition Causes
---

Every state transition carries a cause that records why the
transition happened. peinit MUST track both the current state and
the cause of the most recent transition. Causes affect restart
eligibility, logging detail, OnFailure behaviour, and
administrator comprehension.

## Cause taxonomy

| Cause | Applies to | Description |
|---|---|---|
| ExplicitStart | -> Starting | Administrator or trigger initiated start. |
| DependencyStart | -> Starting | Started to satisfy another service's dependency. |
| RestartPolicy | -> Starting | Automatic restart after failure. |
| BindsToRecovery | -> Starting | Bound dependency returned to Active. peinit automatically restarts the dependent. Does not consume the restart budget. |
| ExplicitStop | -> Stopping | Administrator requested stop. |
| ConflictEviction | -> Stopping | Conflicting service started; this service lost. |
| BindsToPropagation | -> Stopping | Bound dependency stopped. |
| ShutdownWave | -> Stopping or Failed | System shutdown in progress. Services in Active or Reloading transition to Stopping. Services in Starting transition directly to Failed (SIGKILL, no graceful stop). |
| ProcessCrash | -> Failed or Starting | Main process exited unexpectedly (non-zero or signal). |
| ReadinessTimeout | -> Failed | StartTimeout expired before readiness. |
| WatchdogTimeout | -> Failed or Starting | Watchdog keepalive not received in time. |
| HealthCheckFailure | -> Failed or Starting | HealthCheckRetries consecutive failures. |
| PreHookFailure | -> Failed | ExecStartPre exited non-zero. |
| ParentSetupFailure | -> Failed | Parent-side failure before fork (pipe2 EMFILE, clone3 EAGAIN/ENOMEM, cgroup creation failed). No child process was created. |
| PreExecFailure | -> Failed | Post-fork setup failed before exec (token installation, rlimit, environment). Detected via the cloexec error pipe. |
| DependencyFailure | -> Failed | A Requires dependency entered Failed. |
| RestartBudgetExhausted | -> Failed | RestartMaxRetries reached within RestartWindow. |
| CycleDetected | -> Failed | Service is part of a dependency cycle. |
| ValidationError | -> Failed | Service definition failed validation (unknown type, missing required field, etc.). |
| AssertionError | -> Failed | A start-time assert check failed. |
| ConditionSkipped | -> Skipped | Start-time condition check failed (service does not apply). |
| ProcessUnkillable | -> Abandoned | Processes survived SIGKILL -- stuck in uninterruptible kernel sleep (D-state). |

## Restart eligibility

Causes are classified into two groups that determine whether the
restart policy is consulted.

### Restart-eligible causes

For these causes, peinit MUST consult RestartPolicy and the
restart budget before deciding the next state. If the policy
allows restart and the budget is not exhausted, the service
transitions to Starting.

- ProcessCrash
- WatchdogTimeout
- HealthCheckFailure
- ReadinessTimeout
- PreHookFailure
- PreExecFailure
- ParentSetupFailure

> [!INFORMATIVE]
> Startup failures (ReadinessTimeout, PreHookFailure,
> PreExecFailure, ParentSetupFailure) are restart-eligible because
> transient failures during startup should retry. A pre-hook that
> fails because a network mount was momentarily unavailable should
> get another chance, not immediately give up.

### Budget-exempt causes

BindsToRecovery transitions Failed → Starting when a bound
dependency returns to Active. It is not subject to RestartPolicy
evaluation or the restart budget. The service was stopped because
its dependency went away, not because it failed on its own.

### Never-restart causes

For these causes, peinit MUST NOT consult RestartPolicy. The
service transitions directly to Failed (or the cause-specific
target state). Retrying cannot help.

- ExplicitStop -- intentional stop.
- ShutdownWave -- system is shutting down.
- ConflictEviction -- the conflict winner would stop it again.
- BindsToPropagation -- bound dependency is down. Recovery is
  reactive: when the bound service returns to Active, peinit
  automatically restarts dependents with cause BindsToRecovery.
- ProcessUnkillable -- old cgroup still has live processes.
- RestartBudgetExhausted -- already exhausted.
- ValidationError -- definition is broken.
- CycleDetected -- graph structure is broken.
- DependencyFailure -- dependency is broken.
- AssertionError -- required precondition is missing.
- ConditionSkipped -- not a failure.

## OnFailure

When a service transitions to Failed -- for any cause -- and the
service definition includes an OnFailure field, peinit MUST start
the designated fallback service. The OnFailure service fires on
every transition to Failed regardless of cause. The transition
cause is logged, so the OnFailure service or eventd can distinguish
causes.

OnFailure is for graceful degradation (e.g., primary web UI fails,
start minimal emergency endpoint), not for monitoring or alerting
(that is eventd's responsibility).

## Logging contract

Every state transition MUST produce a log entry that includes:

- **What failed:** service name, operation, specific field if
  validation.
- **Why it failed:** cause from the taxonomy above.
- **What peinit did:** state transition, restart attempt, recovery
  mode entry.
- **What the administrator should do:** actionable suggestion
  where possible (e.g., "check Identity field on service X,"
  "resolve cycle between A, B, C").

Cryptic failure messages are a specification violation. A reboot
loop caused by a configuration error with an opaque log message is
unacceptable.
