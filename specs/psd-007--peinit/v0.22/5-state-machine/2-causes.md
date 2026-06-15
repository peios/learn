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
| ExplicitStart | -> Starting or Skipped -> Inactive | Administrator or trigger initiated start. A start from Skipped first clears Skipped to Inactive before re-evaluating conditions. |
| DependencyStart | -> Starting | Started to satisfy another service's dependency. |
| RestartPolicy | -> Starting | Automatic restart after a Backoff delay. |
| BindsToRecovery | -> Starting | Bound dependency returned to Active. peinit automatically restarts the dependent. Does not consume the restart budget. |
| ExplicitStop | -> Stopping | Administrator requested stop. |
| ExplicitReset | -> Inactive | Administrator cleared Failed, Abandoned, or Skipped state without starting the service. |
| ConflictEviction | -> Stopping | Conflicting service started; this service lost. |
| BindsToPropagation | -> Stopping | Bound dependency stopped. |
| ShutdownWave | -> Stopping or Failed | System shutdown in progress. Services in Active or Reloading transition to Stopping. Services in Starting transition directly to Failed (SIGKILL, no graceful stop). |
| ProcessCrash | -> Failed or Backoff | Main process exited unexpectedly (non-zero or signal). |
| CleanExit | -> Inactive | Simple main process exited successfully and RestartPolicy is not Always. This is not a crash and does not consult restart policy. |
| CleanExitRestart | -> Backoff | Simple main process exited successfully, but RestartPolicy=Always requires peinit to restart it. This is not a crash. |
| ReadinessTimeout | -> Failed or Backoff | StartTimeout expired before readiness. |
| WatchdogTimeout | -> Failed or Backoff | Watchdog keepalive not received in time. |
| HealthCheckFailure | -> Failed or Backoff | HealthCheckRetries consecutive failures. |
| PreHookFailure | -> Failed or Backoff | ExecStartPre exited non-zero. |
| ParentSetupFailure | -> Failed or Backoff | Parent-side failure before fork (pipe2 EMFILE, clone3 EAGAIN/ENOMEM, cgroup creation failed). No child process was created. |
| PreExecFailure | -> Failed or Backoff | Post-fork setup failed before exec (token installation, rlimit, environment). Detected via the cloexec error pipe. |
| DependencyFailure | -> Failed | A Requires dependency entered Failed. |
| RestartBudgetExhausted | -> Failed | RestartMaxRetries reached within RestartWindow. |
| CycleDetected | -> Failed | Service is part of a dependency cycle. |
| ValidationError | -> Failed | Service definition failed validation (unknown type, missing required field, etc.). |
| AssertionError | -> Failed | A start-time assert check failed. |
| ConditionSkipped | -> Skipped | Start-time condition check failed (service does not apply). |
| ProcessUnkillable | -> Abandoned | Processes survived SIGKILL -- stuck in uninterruptible kernel sleep (D-state). |

## Restart eligibility

Causes are classified into three groups that determine whether the
restart policy is consulted.

### Restart-eligible causes

For these causes, peinit MUST consult RestartPolicy and the
restart budget before deciding the next state. If the policy
allows restart and the budget is not exhausted, the service
transitions to Backoff (and then to Starting once the backoff
delay elapses; see §5.3). Otherwise it transitions to Failed.

- ProcessCrash
- WatchdogTimeout
- HealthCheckFailure
- ReadinessTimeout
- PreHookFailure
- PreExecFailure
- ParentSetupFailure

### Always-only restart causes

CleanExitRestart is consulted only when a Simple service exits
successfully (exit code 0 or SuccessExitCodes) and
RestartPolicy=Always. It uses the same exponential backoff and
RestartMaxRetries budget as restart-eligible failures. This
prevents a daemon that exits cleanly in a tight loop from bypassing
restart throttling.

CleanExitRestart MUST NOT be treated as ProcessCrash. Logs and
status MUST make clear that the process exited successfully and was
restarted solely because the service policy is Always.

CleanExit is the non-restart counterpart for a Simple service that
exits successfully while RestartPolicy is not Always. CleanExit MUST
transition directly to Inactive, MUST NOT consult RestartPolicy or the
restart budget, and MUST NOT be treated as ProcessCrash.

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
- ExplicitReset -- intentional administrative state clear.
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

When a service transitions to Failed and the service definition
includes an OnFailure field, peinit MUST start the designated
fallback service -- except for the causes excluded below. The
transition cause is logged, so the OnFailure service or eventd can
distinguish causes.

OnFailure MUST NOT fire for:

- **ShutdownWave** -- no new services may start during shutdown
  (§10.1), so a fallback would be both impossible and pointless. A
  Starting service SIGKILLed by the shutdown wave transitions to
  Failed without triggering OnFailure.
- **ValidationError, CycleDetected, DependencyFailure,
  AssertionError** -- these are definition or dependency-graph
  breakage, not runtime degradation. A broken or unsatisfiable
  definition cannot meaningfully trigger a fallback, and the
  fallback would likely sit in the same broken graph. OnFailure is
  for degrading a *running* service, not for configuration errors.

For all other Failed causes -- including ProcessCrash,
WatchdogTimeout, HealthCheckFailure, the startup-failure causes,
and non-Critical RestartBudgetExhausted -- OnFailure fires.

If RestartBudgetExhausted is produced for an ErrorControl=Critical
service, the immediate reboot requirement in §5.3/§10.1 takes
precedence. peinit MUST NOT start the OnFailure service in that
case. Implementations MAY record that OnFailure was suppressed by
Critical reboot; eventd-backed logging remains governed by the
logging/event specifications.

OnFailure is for graceful degradation (e.g., primary web UI fails,
start minimal emergency endpoint), not for monitoring or alerting
(that is eventd's responsibility).

### Loop guard

An OnFailure service can itself fail and carry its own OnFailure, so
a misconfiguration (A's OnFailure is B, B's OnFailure is A) could
loop indefinitely. peinit MUST bound the chain originating from a
single failure: it tracks the set of services already started as
OnFailure handlers for that originating failure and MUST NOT start
one already in the set, and MUST NOT follow the chain beyond a fixed
depth (16). When the guard trips, peinit logs the loop and stops --
it does not keep firing fallbacks.

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
