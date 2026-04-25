---
title: Overview
---

A service is the primary unit of management in peinit. Every
supervised process -- a long-running daemon, a run-to-completion
task, a mount operation -- is represented as a service with a
definition, a runtime state, and a security policy.

Service definitions are stored in the registry under
`Machine\System\Services\<name>`. The key name is the service
name. peinit reads definitions at Phase 2 boot and on demand
when an administrator starts a service or issues a reload-config
command.

## Service types

peinit supports two service types.

### Simple

A long-running daemon. peinit forks, installs a token, and execs
the binary. The process IS the service. When it exits, the service
has stopped. This is the default type and covers the majority of
services (registryd, authd, sshd, application services, etc.).

**Readiness:** determined by the Readiness field. Notify (default)
requires the service to send `READY=1` via sd_notify. Alive
treats the process as ready as soon as it exists.

**Lifecycle:** the service transitions to Active on readiness and
remains Active until the process exits or is stopped.

### Oneshot

A run-to-completion task. peinit forks, installs a token, execs
the binary, and waits for it to exit. Success (exit code 0, or any
code in SuccessExitCodes) marks the service as completed; failure
triggers the failure policy. Used for setup tasks (database
initialisation, directory creation, schema migration).

**Readiness:** the Readiness field is ignored. Oneshot readiness is
always "successful exit." A oneshot that exits 0 has succeeded; one
that exits non-zero has failed. `READY=1` is meaningless for a
process whose job is to exit.

**Lifecycle differences from Simple:**

- Successful exit transitions to Completed. With RemainAfterExit=1,
  the service remains in Completed. Without RemainAfterExit, the
  service transitions Completed -> Inactive after dependents are
  released.
- Non-zero exit transitions to Failed.
- ExecStartPost runs after successful exit, not after a readiness
  signal. If the oneshot fails, ExecStartPost MUST NOT run.
- StartTimeout covers the entire execution time -- from first
  pre-hook to process exit.

**RemainAfterExit:** a Oneshot service with RemainAfterExit=1
stays in the Completed state after its process exits successfully.
Without RemainAfterExit, the service passes through Completed
(releasing dependents) then transitions to Inactive.
RemainAfterExit is useful when the Completed state must persist --
for example, so status queries show the service as finished rather
than inactive.

## Triggers

Triggers determine when a service starts. A service's type
(Simple/Oneshot) is independent of its triggers. Triggers are
stored as a multi_string array on the service definition, each
entry in the format `type` or `type:argument`.

| Trigger | Format | Meaning |
|---|---|---|
| Boot | `boot` | Start during the Phase 2 boot sequence. |
| Timer | `timer:<schedule>` | Start on a schedule. The schedule is a calendar expression (§9.1). |

A service with no triggers is demand-only -- it is started
exclusively via explicit control interface commands.

Multiple triggers of the same type are permitted. A service with
`["timer:*-*-* 02:00:00", "timer:*-*-* 14:00:00"]` runs at 2am
and 2pm. The shortcuts `daily`, `weekly`, `hourly`, and `monthly`
are supported.

The trigger model is designed to be extensible. Future trigger
types (path, device, event) slot into the same array without
schema changes.

## Disabled flag

A service with `Disabled=1` MUST NOT be started by any trigger
(boot, timer, or future trigger types). The Disabled flag
suppresses automatic activation only -- the service MAY still be
started explicitly via the control interface.

To prevent a service from being started entirely, modify its
ServiceSecurity SD to deny SERVICE_START. This is an access
control concern, not a trigger concern.

Enable and disable are registry write operations performed by admin
tools, not peinit control commands. peinit picks up Disabled flag
changes via registry change notifications or on reload-config.

## Forking daemons

peinit does not support forking daemons. Services that double-fork
to "daemonise" themselves are using a workaround for a problem that
does not exist when a service manager tracks the process it
spawned. peinit tracks the process it forks via pidfd.

If a legacy binary requires double-fork behaviour, the role
packager MUST wrap it (e.g., a wrapper script with a `--no-daemon`
flag). This is a packaging concern, not an init concern.
