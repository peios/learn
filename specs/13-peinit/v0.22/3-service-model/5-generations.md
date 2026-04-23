---
title: Configuration Generations
---

peinit operates on snapshots of service definitions, not a live
view of the registry. Two generation concepts govern when registry
changes take effect.

## Boot generation

At the start of Phase 2, peinit MUST read ALL service definitions
from `Machine\System\Services\`, build the dependency graph, and
validate it. The entire boot executes against this snapshot.

Registry changes made during boot (by install scripts, post-hooks,
etc.) MUST NOT affect the in-progress boot. This prevents mid-boot
graph mutations from creating inconsistent state -- a dependency
added while services are Starting would be impossible to honour
consistently.

## Activation generation

When peinit starts a specific service (whether at boot or on
demand), it MUST snapshot that service's definition. The snapshot
governs the entire start lifecycle: pre-exec hooks, token request,
readiness timeout, and initial health checks all use the values
from the snapshot.

If an administrator changes a field while the service is Starting,
the change MUST NOT take effect until the next start.

## Inactive services

A service in Inactive or Failed state has no activation-specific
snapshot. When peinit starts such a service, it uses the current
version from its in-memory model. This means:

- Creating a new service entry: available after the change
  notification is processed.
- Changing a timer on an inactive service: takes effect on the
  next trigger evaluation.
- Changing a dependency on an inactive service: takes effect on
  the next start.
- Changing a dependency on an active service: takes effect on the
  next restart.

## Field mutability

Service definition fields have different mutability semantics
depending on when they are consumed.

### Immutable at runtime

Changes to these fields MUST NOT take effect until the service is
restarted:

- ImagePath
- Type
- Identity
- RequiredPrivileges
- ErrorControl

### Apply on next start

Changes to these fields take effect on the next service start or
explicit graph reload, not while services are running:

- Requires, Wants, BindsTo, Conflicts
- OnFailure
- Conditions, Asserts

### Hot-reloaded

Changes to these fields take effect on the next relevant event
without requiring a service restart:

- ServiceSecurity (next control request)

### Reloadable at runtime

Changes to these fields take effect on the next relevant operation
(restart, health check cycle, etc.) without requiring a service
restart:

- Arguments, SuccessExitCodes
- All timeout and retry values (StartTimeout, StopTimeout,
  WatchdogTimeout, RestartDelay, RestartMaxRetries, RestartWindow)
- HealthCheck, HealthCheckInterval, HealthCheckTimeout,
  HealthCheckRetries
- RestartPolicy
- Environment, WorkingDirectory
- ExecStartPre, ExecStartPost, ExecReload, HookIdentity
- Readiness, NotifyAccess
- LimitNOFILE, LimitCORE
- FdStoreMax
- SafeMode, DisplayName, Description

### Trigger changes

Adding or removing triggers and setting the Disabled flag are
registry writes performed by admin tools. peinit picks up trigger
changes on service restart or when notified via registry change
notifications. New timer triggers on inactive services are armed
immediately on notification.

## In-memory model

peinit MUST maintain a full in-memory model of all service
definitions. The registry is read synchronously only during Phase 2
boot (before meaningful supervision has started) and during
reload-config (admin-initiated, bounded). At runtime, peinit
operates exclusively on its in-memory model.

Registry change notifications are received as events on a pollable
fd. peinit MUST subscribe to `Machine\System\Services\` and
`Machine\System\Init\` at boot. When a notification arrives, peinit
processes it in its event loop -- reading the changed key at a time
of its choosing, not synchronously at the moment of change.

If the notification queue overflows (bulk admin operations, rapid
scripted writes), peinit MUST detect the overflow event and trigger
a full reload-config to resynchronise its in-memory model with the
registry.

> [!INFORMATIVE]
> The in-memory model exists because peinit's event loop MUST
> never block on userspace services during normal supervision. In
> single-threaded PID 1, a blocking syscall blocks the entire
> process -- SIGCHLD reaping, watchdog expiry, shutdown signals,
> and every other event stops while the syscall is stuck. The
> in-memory model ensures supervision never blocks on registry
> availability.
