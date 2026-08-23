---
title: Health Checks
description: A watchdog says a service is still ticking; a health check says it still works — execution, overlap, failure and the flap constraint.
---

A watchdog tells peinit that a service is still ticking. A health check
tells it that the service still works. They address different failures:
a process can be alive and responsive to its own event loop while having
lost its database connection, wedged in a bad state, or started
returning errors to everyone.

## Execution

The health check command runs with the **service's own token** — never
`HookIdentity` — so it checks the service's health from the service's
own vantage point.

Each invocation runs in an ephemeral `health/` sub-cgroup under the
service's tree, as a child of peinit rather than of the service. When
the check completes or times out, peinit kills the whole sub-cgroup,
which cleans up anything the check spawned.

## Overlap

If the previous check is still running when the next interval fires, the
new one is skipped and nothing is counted. A check exceeding
`HealthCheckTimeout` has its sub-cgroup killed and **is** counted as a
failure.

A launch failure — a token that could not be materialised, a fork that
failed — is also counted as a failure and escalates immediately.

## Failure

`HealthCheckRetries` consecutive failures mark the service unhealthy.
An unhealthy service is restarted through the ordinary restart policy:
`RestartPolicy`, exponential backoff and throttling all apply, exactly
as for a crash. The failure count resets the moment a check succeeds.

Escalation kills the service's **root** cgroup rather than just `main/`,
so it takes hooks and probes with it.

## The flap constraint

Restart throttling is what stops a service flapping — failing checks,
restarting, passing initial checks, failing again. But it only works if
the failure cycle is shorter than `RestartWindow`, because otherwise the
service stays healthy long enough between failures to reset the restart
counter, `RestartMaxRetries` is never reached, and it restarts forever.

So this relationship has to hold:

```
HealthCheckRetries × HealthCheckInterval < RestartWindow
```

It is enforced as an error rather than a warning, in both places a
definition can arrive. At boot, a violating service is blocked with
cause `ValidationError` and never started. On reload-config, it is a
validation finding, and a finding rejects the entire reload.

The constraint is checked for any service that declares a `HealthCheck`,
including a Oneshot — even though health checks are scheduled only for
Simple services, so the check being constrained would never run.

> [!NOTE]
> Active health checks on `ErrorControl=Critical` services deserve
> caution. A false positive eventually exhausts the restart budget and
> reboots the machine. Critical services — registryd, authd, lpsd,
> eventd — are usually better served by a passive watchdog with a
> generous timeout: the service knows whether it is healthy and can stop
> sending keepalives when it decides it is not. peinit does not prevent
> health checks on Critical services and applies identical semantics to
> them, but the escalation path ends at a reboot.
