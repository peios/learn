---
title: Health Checks
---

Active health checks run a command periodically to verify service
health beyond "process is alive." This addresses the gap where a
service's process is running but is functionally broken (lost
database connection, stuck in bad state, returning errors).

## Execution model

The health check command runs with the service's own token. It
checks the service's health from the service's perspective.

Each health check invocation runs in an ephemeral `health/`
sub-cgroup under the service's cgroup tree. It is a child of
peinit, not of the service process. When the check completes or
times out, peinit MUST kill the entire `health/` sub-cgroup --
this cleans up any grandchildren the health check may have spawned.

## Overlap prevention

If a previous health check is still running when the next interval
fires, the new check MUST be skipped. A health check that exceeds
HealthCheckTimeout triggers a kill of the `health/` sub-cgroup and
is counted as a failure.

## Failure semantics

HealthCheckRetries consecutive failures mark the service as
unhealthy. An unhealthy service is restarted using the same restart
policy as a crashed service (RestartPolicy, exponential backoff,
and throttling all apply). The health check failure count MUST
reset when a check succeeds.

## Flap protection

The restart throttling mechanism (RestartMaxRetries within
RestartWindow) protects against health check flapping. A service
that repeatedly fails health checks, restarts, passes initial
checks, then fails again will eventually exhaust its restart budget
and transition to Failed.

This only works if the health check failure cycle is shorter than
RestartWindow. The graph validation check (see the Dependencies
section) MUST enforce:

```
HealthCheckRetries * HealthCheckInterval < RestartWindow
```

Configurations that violate this constraint allow the restart
counter to reset between failures, meaning RestartMaxRetries is
never reached and the service restarts indefinitely. This is a
validation error, not a warning.

## D-state sub-cgroup leak

If a health check process is stuck in uninterruptible kernel sleep
(D-state -- typically hung NFS, broken disk controller), SIGKILL
on the `health/` sub-cgroup will not terminate it. peinit detects
this via `cgroup.events` (`populated` still 1 after SIGKILL + a
post-kill timeout (default 5 seconds)).

Unlike the main process, a stuck health check MUST NOT cause the
service to enter the Abandoned state. The health check is a
diagnostic probe -- it holds no service resources (ports, file
locks, database connections).

Instead, peinit MUST orphan the leaked sub-cgroup:

1. Mark it internally as leaked.
2. Log a warning: "health check sub-cgroup for service X has
   D-state processes -- likely dead I/O. Sub-cgroup leaked.
   Underlying I/O problem requires investigation."
3. Continue normal service supervision.

The leaked sub-cgroup remains in the hierarchy until reboot. If
the service is later stopped and restarted, peinit creates a
generational cgroup tree (see the Pre-Exec Sequence section)
because the old tree's `rmdir` will fail with EBUSY.

The same leak handling applies to `hooks/` sub-cgroups -- a
pre-exec hook stuck in D-state is orphaned, not elevated to
service-level Abandoned.

## Leaked sub-cgroup observability

Leaked sub-cgroups MUST NOT be silent. peinit MUST track leaked
sub-cgroups per service and expose them:

- **Status queries** MUST include a `warnings` array listing each
  leak (sub-cgroup path, type, timestamp of detection).
- **Start commands** on a service with leaked sub-cgroups MUST
  return a warning in the response: "service has leaked sub-cgroups
  from a previous generation -- indicates underlying I/O problem
  requiring investigation."

## Critical service guidance

> [!INFORMATIVE]
> Active health checks on ErrorControl=Critical services should be
> used with extreme caution. A false positive health check failure
> on a Critical service eventually exhausts the restart budget and
> triggers a system reboot. Critical services (registryd, authd,
> lpsd, eventd) are better served by passive watchdog keepalives
> with generous timeouts -- the service itself knows whether it is
> healthy and can stop sending keepalives if it detects internal
> failure. peinit does not prevent health checks on Critical
> services, but the risk of false positives escalating to reboots
> is real.
>
> peinit MUST apply the same health check semantics to Critical
> services as to any other service. There is no special-casing.
