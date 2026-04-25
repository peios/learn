---
title: Restart and Reload
---

## Restart semantics

When a service transitions to Failed with a restart-eligible cause
(§5.2), peinit evaluates the restart
policy:

```
evaluate_restart(service, cause):
    // Step 1: Check policy.
    if service.restart_policy == Never:
        return STAY_FAILED
    if service.restart_policy == OnFailure:
        if exit_code in service.success_exit_codes:
            return STAY_FAILED
    // restart_policy == Always falls through unconditionally.

    // Step 2: Check budget.
    recent_restarts = count restarts within service.restart_window
    if recent_restarts >= service.restart_max_retries:
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

### Policy values

| Policy | Value | Behaviour |
|---|---|---|
| Never | 0 | Never restart. Service remains Failed. |
| OnFailure | 1 | Restart only on non-zero exit or runtime failure. Exits matching SuccessExitCodes are not restarted. |
| Always | 2 | Restart on any failure regardless of exit code. Successful Oneshot exits (code 0 or SuccessExitCodes match) are not restart-eligible -- see below. |

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

If RestartMaxRetries restarts occur within RestartWindow seconds,
the service transitions to Failed with cause
RestartBudgetExhausted. peinit MUST then apply the service's
ErrorControl level:

- **Normal:** service remains in Failed state.
- **Critical:** peinit syncs filesystems and reboots.

### Budget reset

If a restarted service stays in the Active state for at least
RestartWindow seconds without failing, the restart counter MUST
reset to zero. This means a service that crashes once every few
minutes with a 120-second RestartWindow never exhausts its budget
-- each crash is treated as a fresh failure.

## Reload semantics

Reload tells a service to re-read its configuration without
restarting. peinit sends the reload command (ExecReload or SIGHUP)
and transitions the service to the Reloading state.

### Reload lifecycle

```
evaluate_reload(service):
    // Step 1: Send reload.
    if service.exec_reload is not null:
        if exec_reload starts with "signal:":
            send the named signal to the main process
        else:
            fork and exec the reload command
    else:
        send SIGHUP to the main process

    // Step 2: Enter Reloading state.
    service.state = Reloading
    start detection_window timer (2 seconds)

    // Step 3: Wait for protocol detection.
    // Three outcomes:

    // 3a: RELOADING=1 arrives within detection window.
    //     Service speaks the reload protocol.
    //     Extend wait up to StartTimeout for READY=1.
    on RELOADING=1 within detection_window:
        cancel detection_window
        start extended_wait timer (StartTimeout)

    // 3b: READY=1 arrives at any point during Reloading.
    //     Reload complete. Transition to Active.
    on READY=1:
        service.state = Active
        return "confirmed"

    // 3c: Detection window expires with no RELOADING=1.
    //     Service does not speak the protocol.
    //     Assume reload was instant. Transition to Active.
    on detection_window expired:
        service.state = Active
        return "advisory"

    // 3d: Extended wait expires without READY=1.
    //     Service signalled RELOADING=1 but never completed.
    //     Transition to Active with a warning.
    on extended_wait expired:
        log warning: "service signalled RELOADING=1 but
                      never completed reload"
        service.state = Active
        return "advisory"
```

The detection window duration (2 seconds) is fixed and is not
configurable via the registry.

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
  the service transitions Reloading → Starting (restart).
- If RestartPolicy does not allow restart or the budget is
  exhausted, the service transitions Reloading → Failed.

The reload detection window and extended wait timers are cancelled
on process exit.

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

- `"mode": "confirmed"` -- if `READY=1` was received.
- `"mode": "advisory"` -- if the detection window expired without
  `RELOADING=1`, or if the extended wait expired without `READY=1`.

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
