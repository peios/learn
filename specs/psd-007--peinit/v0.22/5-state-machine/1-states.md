---
title: States and Transitions
---

Every service managed by peinit is in exactly one state at any
given time. This section defines the states, their semantics, and
every valid transition between them.

## States

| State | Process exists? | Satisfies dependents? | Description |
|---|---|---|---|
| Inactive | No | No | Service has not been started, or was stopped cleanly and is not set to restart. |
| Starting | Not yet or Yes | No | Activation in progress: conditions/asserts, pre-exec hooks, fork, or readiness wait. Process may not yet exist. Dependents are blocked. |
| Active | Yes | Yes | Service is running and ready. Dependents may start. |
| Reloading | Yes | Yes | Service is reloading configuration. Still satisfies dependents. |
| Stopping | Yes (briefly) | No | SIGTERM sent, waiting for exit or SIGKILL escalation. |
| Completed | No | Yes | Oneshot only. Process exited successfully. Satisfies dependents. With RemainAfterExit=1, remains in Completed. Without RemainAfterExit, transitions to Inactive after dependents are released. |
| Failed | No | No | Service exited abnormally and restart policy is exhausted or not configured. |
| Abandoned | Yes (unkillable) | No | SIGKILL sent but processes survived -- stuck in uninterruptible kernel sleep (D-state). peinit has abandoned supervision. The cgroup is leaked. |
| Skipped | No | Yes | Conditions evaluated and not met. The service does not apply. Satisfies dependents. |

## Transition table

Every valid state transition. Transitions not listed here are
invalid -- peinit MUST NOT perform them.

| From | To | Trigger | Conditions |
|---|---|---|---|
| Inactive | Starting | Start command or dependency resolution | Service is boot-triggered or explicitly started. |
| Inactive | Skipped | Condition check fails | At least one Condition evaluated to false. |
| Inactive | Failed | Validation, assertion, cycle, or dependency failure | Service failed before any process was created. |
| Starting | Active | Readiness signal | Simple only. `READY=1` received (Notify) or process exists (Alive). |
| Starting | Completed | Oneshot successful exit + RemainAfterExit | Process exited 0 (or SuccessExitCodes match) and RemainAfterExit=1. |
| Starting | Completed | Oneshot successful exit, no RemainAfterExit | Process exited 0 (or SuccessExitCodes match) and RemainAfterExit=0. Transitions through Completed to release dependents, then to Inactive. |
| Starting | Starting | Startup failure + restart policy | ReadinessTimeout, PreHookFailure, PreExecFailure, or ParentSetupFailure with RestartPolicy allowing restart and budget remaining. |
| Starting | Stopping | Stop command cancels in-progress start | Explicit stop while Starting. Restart commands on a Starting service are queued, not cancelled. |
| Starting | Failed | Timeout, hook failure, setup failure, or early exit | StartTimeout exceeded, pre-hook exited non-zero, parent setup failed, pre-exec failed, or process exited before readiness (Simple) or with non-zero exit (Oneshot). |
| Starting | Failed | Shutdown | ShutdownWave causes SIGKILL of Starting service. |
| Active | Reloading | Reload triggered | ExecReload command sent or SIGHUP delivered. |
| Active | Stopping | Stop command, conflict, BindsTo, or shutdown | Explicit stop, conflicting service started, bound dependency stopped, or shutdown in progress. |
| Active | Starting | Process crash + restart policy | Process exited unexpectedly, RestartPolicy allows restart, budget remaining. |
| Active | Failed | Process crash + no restart | Process exited unexpectedly, RestartPolicy=Never or budget exhausted. |
| Active | Starting | Health check failure + restart | HealthCheckRetries exhausted, RestartPolicy allows restart, budget remaining. |
| Active | Failed | Health check failure + no restart | HealthCheckRetries exhausted, RestartPolicy=Never or budget exhausted. |
| Active | Starting | Watchdog timeout + restart | Watchdog keepalive not received, RestartPolicy allows restart, budget remaining. |
| Active | Failed | Watchdog timeout + no restart | Watchdog keepalive not received, RestartPolicy=Never or budget exhausted. |
| Reloading | Active | Reload complete | `READY=1` received, detection window expires, or extended wait expires. |
| Reloading | Stopping | Stop command, conflict, BindsTo, or shutdown | Same triggers as Active to Stopping. Reload is cancelled. |
| Reloading | Starting | Process crash + restart policy | Process exited during reload, RestartPolicy allows restart, budget remaining. |
| Reloading | Failed | Process crash during reload | Process exited while Reloading and RestartPolicy=Never or budget exhausted. |
| Stopping | Inactive | Process exits (explicit stop or shutdown) | Clean shutdown requested by admin or system. |
| Stopping | Failed | Process exits (conflict or BindsTo) | Service was forcibly stopped by conflict eviction or dependency loss. The cause recorded is ConflictEviction or BindsToPropagation respectively, carried from the transition that initiated the stop. |
| Stopping | Abandoned | SIGKILL + post-kill timeout | SIGKILL sent but `main/` sub-cgroup still populated after post-kill timeout (default 5 seconds). |
| Stopping | Starting | Restart operation | Stop phase of an admin-initiated restart operation has completed. peinit begins the start phase. |
| Completed | Inactive | RemainAfterExit=0, dependents released | Oneshot without RemainAfterExit, after dependents have been released. |
| Completed | Inactive | Stop command | Explicit stop clears Completed state. |
| Completed | Inactive | Shutdown | Completed services (oneshot with RemainAfterExit) are cleared during shutdown. |
| Completed | Starting | Start command | Re-run the oneshot. |
| Failed | Starting | Explicit start command or automatic restart | Administrator manually restarts, BindsTo recovery (bound service returns to Active), timer trigger, or restart policy. |
| Failed | Inactive | Reset command | Administrator clears Failed state without starting. |
| Abandoned | Inactive | Reset command | Administrator clears state. peinit re-checks the cgroup -- if it finally emptied, clean up. If still populated, log a warning. |
| Skipped | Inactive | Reset or explicit start | Clears Skipped state. A subsequent start re-evaluates conditions. |

## Dependent satisfaction

A service satisfies its dependents only in the following states:

- **Active** -- running and ready.
- **Completed** -- Oneshot, finished successfully. Satisfies
  dependents regardless of RemainAfterExit.
- **Skipped** -- conditions not met, service does not apply
  (succeeded by not needing to run).

All other states do not satisfy dependents. A dependent blocked on
a Requires dependency that is in any non-satisfying state MUST NOT
start.

## Invariants

1. A service MUST be in exactly one state at any given time.
2. Only transitions listed in the transition table are valid.
3. Only peinit MAY transition service runtime state. No external
   process may directly manipulate a service's state.
4. A service object is securable independently of its process
   token. The ServiceSecurity SD controls who can manage the
   service. The service's process token controls what the service
   can access. These are independent.
5. Readiness is per-start-generation. A `READY=1` from a previous
   incarnation MUST NOT be valid for the current start.
