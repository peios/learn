---
title: Restart and Reload
---

## Restart semantics

When a restart-eligible cause occurs (§5.2), or when a Simple clean
exit produces the always-only CleanExitRestart cause (§5.2), peinit
evaluates the restart policy. The outcome is either **Failed** (no
restart) or **Backoff** -- the service waits out a delay, then
transitions to Starting:

```
evaluate_restart(service, cause):
    // Step 1: Check policy.
    if service.restart_policy == Never:
        return STAY_FAILED
    if cause == CleanExitRestart and service.restart_policy != Always:
        return INVALID_CAUSE_FOR_POLICY
    if service.restart_policy == OnFailure:
        // A termination counts as success (no restart) only when the
        // cause is a process exit whose code is in SuccessExitCodes.
        // Only ProcessCrash and CleanExitRestart carry an exit code.
        // CleanExitRestart is Always-only and was handled above.
        // Every other
        // restart-eligible cause (WatchdogTimeout, HealthCheckFailure,
        // ReadinessTimeout, PreHookFailure, PreExecFailure,
        // ParentSetupFailure -- see §5.2) has no exit code and is
        // always a failure under OnFailure.
        if cause == ProcessCrash and exit_code in service.success_exit_codes:
            return STAY_FAILED
    // restart_policy == Always falls through unconditionally.

    // Step 2: Check budget. consecutive_failures is the count of
    // prior consecutive restart-eligible failures (the same counter
    // backoff uses in Step 3). It resets to 0 only after the service
    // stays Active for RestartWindow seconds -- it is NOT a count of
    // restarts within a trailing window.
    if consecutive_failures >= service.restart_max_retries:
        service.cause = RestartBudgetExhausted
        if service.error_control == Critical:
            sync filesystems and reboot
        // Otherwise: service remains in Failed state.
        return STAY_FAILED

    // Step 3: Compute delay.
    delay = service.restart_delay * (2 ^ consecutive_failures)
    delay = min(delay, 60)

    // Step 4: Schedule restart.
    return RESTART_AFTER(delay)
```

`RESTART_AFTER(delay)` places the service in the **Backoff** state
for `delay` seconds; when the delay elapses the service transitions
to Starting and the normal activation sequence (and its
StartTimeout) begins. A restart-policy retry therefore never passes
through Failed -- Failed is reached only via `STAY_FAILED`
(RestartPolicy=Never, invalid policy for CleanExitRestart, or budget
exhausted). This is why OnFailure (§5.2), which fires on entry to
Failed, does not fire on each retry, only when the service finally
fails out. While in Backoff the service is down and does not satisfy
dependents; an explicit `start` honors the remaining delay and a
`stop` cancels the pending restart (§11.2).

### Policy values

| Policy | Value | Behaviour |
|---|---|---|
| Never | 0 | Never restart. Service remains Failed. |
| OnFailure | 1 | Restart only on non-zero exit or runtime failure. Exits matching SuccessExitCodes are not restarted. |
| Always | 2 | Restart on any failure regardless of exit code. For Simple services, also restart successful clean exits using CleanExitRestart. Successful Oneshot exits (code 0 or SuccessExitCodes match) are not restart-eligible -- see below. |

For Oneshot services with RestartPolicy=Always, a successful exit
(code 0 or SuccessExitCodes match) is NOT restart-eligible.
RestartPolicy governs the response to failures. A successful
Oneshot exit transitions to Completed (then Inactive if no
RemainAfterExit) regardless of RestartPolicy. Only non-zero exits
trigger the restart evaluation. Timer triggers are the mechanism
for re-running a Oneshot on a schedule.

### Exponential backoff

The delay before each restart attempt doubles on each consecutive
failure, starting from RestartDelay (default 1 second) and capped
at 60 seconds. The consecutive failure counter resets when the
service stays healthy for RestartWindow seconds.

### Budget exhaustion

Once RestartMaxRetries restarts have occurred without the service
recovering -- that is, without it staying Active for RestartWindow
seconds to reset the counter -- the next failure is not restarted:
the service transitions to Failed with cause RestartBudgetExhausted.
peinit MUST then apply the service's ErrorControl level:

- **Normal:** service remains in Failed state.
- **Critical:** peinit syncs filesystems and reboots immediately.
  This immediate reboot takes precedence over OnFailure; peinit
  MUST NOT start an OnFailure handler for the Critical budget
  exhaustion.

### Budget reset

If a restarted service stays in the Active state for at least
RestartWindow seconds without failing, the restart counter MUST
reset to zero. A service that recovers and stays Active for longer
than RestartWindow between crashes therefore never exhausts its
budget -- each crash starts from a counter of zero. Only failures
recurring faster than the service can sustain RestartWindow of
health accumulate toward RestartMaxRetries.

## Reload semantics

Reload tells a service to re-read its configuration without
restarting. peinit sends the reload command (ExecReload or SIGHUP)
and transitions the service to the Reloading state.

### Reload lifecycle

```
evaluate_reload(service):
    // Step 1: Issue the reload and enter the Reloading state.
    // ExecReload is either a signal (e.g. "signal:SIGHUP") or an
    // external command. An external command runs in the service's
    // hooks/ sub-cgroup under the service's own Identity (§3.3) --
    // never peinit's token, and HookIdentity does not apply.
    service.state = Reloading

    if service.exec_reload is null:
        send SIGHUP to the main process
        return await_signal_reload(service)
    if service.exec_reload starts with "signal:":
        send the validated named signal (§3.2) to the main process
        return await_signal_reload(service)
    else:
        materialise the service token, fork the command into hooks/,
        exec it, and wait for it to exit
        return await_command_reload(service)

// Signal / SIGHUP path: there is no command exit to observe, so
// completion is inferred from the main process's sd_notify protocol.
await_signal_reload(service):
    start detection_window timer (2 seconds)

    on READY=1 (any time):
        service.state = Active
        return "confirmed"
    on RELOADING=1 within detection_window:
        cancel detection_window
        start extended_wait timer (StartTimeout)
    on detection_window expired (no RELOADING=1):
        service.state = Active
        return "advisory"
    on extended_wait expired (no READY=1):
        log warning: "service signalled RELOADING=1 but never
                      completed reload"
        service.state = Active
        return "advisory"

// External-command path: the command's exit gates FAILURE; the main
// process's READY=1 (if any) gates CONFIRMATION.
await_command_reload(service):
    on command exits non-zero:
        log error: "ExecReload command failed (exit <code>)"
        service.state = Active   // a failed reload does NOT kill a running service
        return "failed"
    on command runtime exceeds StartTimeout:
        SIGKILL the command and its hooks/ descendants
        log error: "ExecReload command timed out"
        service.state = Active
        return "failed"
    on command exits zero:
        service.state = Active
        if READY=1 was received from the main process during reload:
            return "confirmed"
        else:
            return "advisory"
```

The detection window duration (2 seconds) is fixed and is not
configurable via the registry. A failed reload (either branch)
leaves the service Active -- reload failure is reported to the
caller but never transitions a running service out of Active.

### Auto-detection

The reload protocol is auto-detecting -- no per-service
configuration is needed. Services that implement sd_notify reload
signalling (`RELOADING=1` followed by `READY=1`) get proper
lifecycle tracking. Services that do not get a brief Reloading
state that auto-resolves after the detection window.

Reload MUST never get stuck. Every path has a timeout.

### Process crash during reload

If the service's main process exits while in the Reloading state,
peinit MUST treat it as a ProcessCrash. The restart policy is
consulted:

- If RestartPolicy allows restart and the budget is not exhausted,
  the service transitions Reloading → Backoff (then Starting after
  the backoff delay).
- If RestartPolicy does not allow restart or the budget is
  exhausted, the service transitions Reloading → Failed.

The reload detection window and extended wait timers are cancelled
on process exit. This concerns the service's **main process**
crashing -- distinct from an external ExecReload *command* exiting
non-zero, which is the "failed" reload outcome above and leaves the
main process (and the service) running.

### Reload during stop

If a stop command arrives while a service is in the Reloading
state, peinit MUST cancel the reload immediately -- send SIGTERM
without waiting for the detection window or extended wait to
expire. The service transitions to Stopping.

### Wait semantics

The control socket `reload` command returns immediately by default
(`wait` defaults to false for reload, unlike other lifecycle
commands). If `wait=true`, the connection stays open until the
Reloading state resolves. The response includes:

- `"mode": "confirmed"` -- `READY=1` was received (signal path), or
  the ExecReload command exited 0 and `READY=1` was received.
- `"mode": "advisory"` -- the detection window expired without
  `RELOADING=1`, the extended wait expired without `READY=1`, or the
  ExecReload command exited 0 without a `READY=1` from the main
  process.
- `"mode": "failed"` -- the ExecReload command exited non-zero or
  timed out. The service remains Active.

## Runtime watchdog timeout update

A service MAY update its watchdog interval at runtime by sending
`WATCHDOG_USEC=<value>` via sd_notify.

When peinit receives a `WATCHDOG_USEC` message:

1. Sender authentication MUST be performed (§11.1).
2. The value MUST be parsed as an unsigned integer representing
   microseconds.
3. If the value is greater than 0, peinit MUST update the
   service's watchdog interval to the specified value. The current
   watchdog timer MUST be re-armed immediately with the new
   interval -- the previous timer is cancelled and a fresh timer
   starts from the moment of receipt.
4. If the value is 0, peinit MUST disable the watchdog for the
   service entirely. This is equivalent to WatchdogTimeout=0 in
   the schema -- no further keepalive pings are expected.

The runtime value does NOT persist across restarts. When a service
restarts, the watchdog interval reverts to the schema's
WatchdogTimeout value (converted to microseconds). If
WatchdogTimeout is 0, the watchdog starts disabled regardless of
any runtime update from the previous incarnation.

> [!INFORMATIVE]
> Runtime watchdog updates are useful for services that enter
> phases with different latency characteristics. A database engine
> might use a tight 5-second watchdog during normal operation but
> extend it to 60 seconds during a compaction pass. The service
> knows its own operational phases better than the administrator
> writing the schema.

## Timeout extension

A service MAY request additional time during a start, stop, or
reload transition by sending `EXTEND_TIMEOUT_USEC=<value>` via
sd_notify.

When peinit receives an `EXTEND_TIMEOUT_USEC` message during an
active transition (the service is in Starting, Stopping, or
Reloading state):

1. Sender authentication MUST be performed.
2. The value MUST be parsed as an unsigned integer representing
   microseconds.
3. peinit MUST reset the current phase's timeout to expire
   `<value>` microseconds from now. The extension is not additive
   -- each `EXTEND_TIMEOUT_USEC` message replaces the previous
   timeout deadline entirely.
4. The service MAY send `EXTEND_TIMEOUT_USEC` repeatedly. Each
   message resets the deadline.

### Extension caps

The extended timeout MUST NOT exceed the per-service timeout for
the current phase multiplied by 4:

| Phase | Base timeout | Maximum extended deadline |
|---|---|---|
| Starting | StartTimeout | StartTimeout x 4 |
| Stopping | StopTimeout | StopTimeout x 4 |
| Reloading | StartTimeout | StartTimeout x 4 |

If `<value>` would push the deadline beyond the cap, peinit MUST
clamp the deadline to the cap. The message is not rejected -- the
timeout is set to the maximum permissible value.

During shutdown, an additional global cap applies: the extended
deadline MUST NOT exceed the remaining time in the global
ShutdownTimeout. If both caps apply, the stricter (smaller) cap
wins.

### Outside transitions

If `EXTEND_TIMEOUT_USEC` is received while the service is in a
non-transitional state (Active, Completed, Failed, etc.), peinit
MUST ignore the message. There is no timeout to extend.

> [!INFORMATIVE]
> Timeout extension is designed for services that perform
> variable-duration work during transitions -- for example, a
> database that needs to replay a write-ahead log on startup. The
> service sends periodic EXTEND_TIMEOUT_USEC pings to prove it is
> making progress. If it stops sending, the original (or last
> extended) timeout fires and peinit escalates normally. The 4x cap
> prevents a buggy service from extending indefinitely.
