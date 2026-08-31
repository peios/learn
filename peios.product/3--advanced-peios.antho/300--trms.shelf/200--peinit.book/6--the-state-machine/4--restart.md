---
title: Restart
description: What happens when a restart-eligible cause occurs — the policies, backoff, the budget and when it resets, and exhaustion.
---

When a restart-eligible cause occurs, or a Simple clean exit produces
`CleanExitRestart`, peinit evaluates the restart policy. The outcome is
either Failed, or Backoff followed by Starting.

```
evaluate_restart(service, cause):
    // 1. Policy.
    if cause is never-restart:
        return STAY_FAILED
    if cause == CleanExitRestart and policy != Always:
        return INVALID_CAUSE_FOR_POLICY
    if policy == Never:
        return STAY_FAILED
    if policy == OnFailure:
        // A termination counts as success only when the cause is a
        // process exit whose code is in SuccessExitCodes. Only
        // ProcessCrash and CleanExitRestart carry an exit code, and
        // CleanExitRestart was handled above. Every other eligible
        // cause has no exit code and is always a failure here.
        if cause == ProcessCrash and exit_code in success_exit_codes:
            return STAY_FAILED
    // Always falls through unconditionally.

    // 2. Budget.
    if consecutive_failures >= restart_max_retries:
        cause = RestartBudgetExhausted
        if error_control == Critical:
            sync and reboot
        return STAY_FAILED

    // 3. Delay.
    delay = min(restart_delay << consecutive_failures, 60)

    // 4. Schedule.
    return RESTART_AFTER(delay)
```

`RESTART_AFTER` puts the service in Backoff for the delay; when it
elapses the service transitions to Starting and the ordinary activation
sequence begins, with its own fresh `StartTimeout`.

The exit code is available only when peinit observed a process exit, and
it is carried into the evaluation wherever there was one — including the
pre-readiness exit, where a Simple service exits before signalling
`READY=1`. So `SuccessExitCodes` means the same thing on both sides of
readiness: a service that legitimately concludes "nothing to do" during
startup and exits with a listed code is not restarted.

Failures with no process exit behind them — a hook that never ran, a
readiness deadline, a dependency failure — carry no code, and the
`SuccessExitCodes` branch cannot apply to them. That is not a gap: a
success code is a statement about how the service's own process ended.

## The policies

| Policy | Value | Behaviour |
|---|---|---|
| Never | 0 | Never restart. The service stays Failed. |
| OnFailure | 1 | Restart on a non-zero exit or a runtime failure. An exit matching `SuccessExitCodes` is not restarted. |
| Always | 2 | Restart on any failure regardless of exit code, and for a Simple service also on a successful clean exit. |

For a **Oneshot** with `RestartPolicy=Always`, a successful exit is not
restart-eligible. `RestartPolicy` governs the response to failures; a
Oneshot that succeeds has done its job. It goes to Completed — and then
Inactive without `RemainAfterExit` — whatever the policy says, and only
a non-zero exit reaches the restart evaluation at all. Timer triggers
are the mechanism for re-running a Oneshot on a schedule.

## Backoff

The delay doubles on each consecutive failure, starting from
`RestartDelay` and capped at 60 seconds. The arithmetic is
overflow-safe, so a large `RestartDelay` or a long failure run saturates
at the cap rather than wrapping.

While a service is in Backoff it is down and does not satisfy
dependents. An explicit `start` creates or merges into a **deferred**
start operation, which honours the remaining delay rather than
short-circuiting it; a `stop` cancels the pending restart and takes the
service to Inactive.

## The budget, and when it resets

`consecutive_failures` counts consecutive restart-eligible failures. It
resets to zero **only after the service has stayed Active for
`RestartWindow` seconds**. It is not a count of restarts within a
trailing window, and the difference is what the mechanism turns on.

peinit stamps the moment a service becomes dependent-satisfying, and
clears that stamp on any transition to a non-satisfying state — so a
crash restarts the clock. The reset fires when the stamp plus
`RestartWindow` is reached with the service still Active.

A service that recovers and stays Active longer than `RestartWindow`
between crashes therefore never exhausts its budget: each crash starts
from a counter of zero. Only failures recurring faster than the service
can sustain a window of health accumulate.

Two other events also zero the counter, both of which mean the service
is no longer in a failure run: a clean exit to Inactive, and an
administrative reset. An explicit stop while in Backoff does not — the
accrued failures are preserved.

Because the reset requires the service to be Active, a service that
happens to be Reloading when its window boundary passes misses that
reset and gets it on returning to Active.

## Exhaustion

Once `RestartMaxRetries` restarts have happened without the service
sustaining a window of health, the next failure is not restarted: Failed
with cause `RestartBudgetExhausted`. peinit then applies `ErrorControl`:

- **Normal** — the service stays Failed.
- **Critical** — peinit syncs the filesystems and reboots immediately.
  The reboot takes precedence over `OnFailure`.

The reboot does not depend on how the budget was exhausted. The paths
that observe a terminal outcome for a running service — the main job
ending, a health check failing or timing out, the watchdog expiring —
raise it directly. Every other route reaches it through a check made
once per runtime turn, which asks a single question of the service
table: is a Critical service Failed with cause `RestartBudgetExhausted`?
That covers a budget exhausted purely by startup failures — repeated
`ReadinessTimeout`, `PreHookFailure`, `ParentSetupFailure` — where a
service that can never get as far as running would otherwise have
settled in Failed with neither escalation.

The `OnFailure` suppression asks the same question rather than
inspecting `ErrorControl` itself, so the handler is skipped exactly when
a reboot is owed and never on the strength of one that was not
scheduled.

A failure during a shutdown reboots nothing (§12.2 step 2), and the
handler is not started either — the machine is already going down.
