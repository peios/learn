---
title: Defining a service
type: concept
description: "A service is a key in the registry under Machine\\System\\Services\\, made of typed values. This page covers where definitions live, the naming rules, the definition schema grouped by what each field is for, and the single most important operational idea: peinit works from a snapshot, so a field's mutability class decides whether your change takes effect now, on the next start, or never until restart."
related:
  - peios/peinit/overview
  - peios/peinit/service-types
  - peios/peinit/controlling-services
  - peios/peinit/registry-key-reference
  - peios/the-registry/keys-values-and-types
  - peios/the-registry/configuration-and-meaning
  - peios/the-registry/watches
---

A service is defined by a single key in the [registry](~peios/the-registry/overview), under `Machine\System\Services\<name>`. The key's name *is* the service name, and the typed [values](~peios/the-registry/keys-values-and-types) inside it are the definition — the binary, who it runs as, what it depends on, how it is supervised. There is no file under `/etc`; there is a registry key.

peinit reads these definitions in two situations: once at boot, to build the service graph, and on demand, when an administrator starts a service or runs `reload-config`. Between those reads it works from an in-memory copy. That last fact is the source of the most common "why didn't my change take effect?" question, and the second half of this page is devoted to it.

## Service names

A service name must be made of characters from `[A-Za-z0-9._-]` and be 1–128 bytes long. Anything else is a validation error. Two characters are pointedly excluded:

- **`/`** — names map directly onto cgroup ids and registry key names, and a slash would be ambiguous in both.
- **`:`** — reserved for peinit-internal synthetic names (for example, the way a hook job is labelled).

The name is how you refer to the service everywhere: in `peiosctl` commands, in another service's dependency list, in a [ServiceSecurity](~peios/peinit/who-can-manage-a-service) descriptor, and in the [per-service SID](~peios/peinit/identity-and-privileges) derived from it.

## The definition schema

A definition is a set of typed registry values. Rather than list all of them in one wall of rows, the tables below group the fields by what they are *for*, with a pointer to the page that explains each group in depth. Every field is optional unless noted; the only hard requirement is `ImagePath`. The full type-and-default catalogue lives in the [Registry key reference](~peios/peinit/registry-key-reference).

**What to run** — the binary and its execution context.

| Field | Default | Purpose |
|---|---|---|
| `ImagePath` *(required)* | — | Absolute path to the service binary. |
| `Arguments` | — | Argument list passed to the binary. |
| `WorkingDirectory` | `/` | Working directory for the process. |
| `Environment` | — | `KEY=VALUE` pairs added to the environment. |
| `RuntimeDirectories` | — | Private directories created under `/run` just before the process starts. See [The execution environment](~peios/peinit/execution-environment). |
| `LimitNOFILE`, `LimitCORE` | — | `RLIMIT_NOFILE` / `RLIMIT_CORE`. |

**What kind of service** — type and readiness. See [Simple and Oneshot services](~peios/peinit/service-types).

| Field | Default | Purpose |
|---|---|---|
| `Type` | Simple | `Simple` (long-running) or `Oneshot` (run-to-completion). |
| `Readiness` | Notify | `Notify` (`READY=1` via sd_notify) or `Alive` (ready when the process exists). Ignored for Oneshot. |
| `RemainAfterExit` | 0 | Oneshot only — stay in `Completed` after a successful exit. |
| `SuccessExitCodes` | — | Non-zero exit codes to treat as success. |

**When to start** — triggers and conditions. See [Triggers and timers](~peios/peinit/triggers-and-timers).

| Field | Default | Purpose |
|---|---|---|
| `Triggers` | — | `boot` and/or `timer:<schedule>`. Absent = demand-only. |
| `Disabled` | 0 | If 1, triggers must not activate the service (manual start still allowed). |
| `SafeMode` | 0 | If 1, attempt to start in [Safe mode](~peios/peinit/boot-and-boot-modes). |
| `Conditions`, `Asserts` | — | Start-time checks. A failed condition *skips*; a failed assert *fails*. |

**Who it runs as** — identity and privileges. See [Service identity and privileges](~peios/peinit/identity-and-privileges).

| Field | Default | Purpose |
|---|---|---|
| `Identity` | `LocalService` | Principal name or SID for the service token. |
| `RequiredPrivileges` | — | Privilege allow-list; everything else is stripped from the token. |
| `HookIdentity` | service's `Identity` | Identity for `ExecStartPre`/`ExecStartPost` hooks. |

**How it relates to other services** — dependencies. See [Dependencies and ordering](~peios/peinit/dependencies).

| Field | Purpose |
|---|---|
| `Requires` | Hard dependencies — must be satisfied first; their failure fails this service. |
| `Wants` | Soft dependencies — started first if present, but optional. |
| `BindsTo` | Runtime coupling — if the target stops, this stops too. |
| `Conflicts` | Mutual exclusion — starting this stops the named services. |
| `OnFailure` | Service to start when this one enters `Failed`. |

**How it is kept alive** — supervision and health. See [Keeping services running](~peios/peinit/supervision).

| Field | Default | Purpose |
|---|---|---|
| `ErrorControl` | Normal | `Normal` (stay Failed) or `Critical` (sync + reboot on irrecoverable failure). |
| `RestartPolicy` | OnFailure | `Never` / `OnFailure` / `Always`. |
| `RestartMaxRetries`, `RestartWindow`, `RestartDelay` | 5 / 120 / 1 | Restart budget, the window of health that resets it, and the backoff base. |
| `HealthCheck`, `HealthCheckInterval`, `HealthCheckTimeout`, `HealthCheckRetries` | — / 30 / 5 / 3 | Active health-check command and its timing. |
| `WatchdogTimeout` | 0 | Expected interval between `WATCHDOG=1` pings; 0 disables. |

**The transition phases** — hooks and timeouts. See [The execution environment](~peios/peinit/execution-environment) and [The service lifecycle](~peios/peinit/the-service-lifecycle).

| Field | Default | Purpose |
|---|---|---|
| `ExecStartPre`, `ExecStartPost` | — | Commands run before the binary / after readiness. |
| `ExecReload` | (SIGHUP) | Reload command or `signal:<NAME>`. |
| `StartTimeout`, `StopTimeout` | 30 / 10 | Seconds for the whole start sequence / between SIGTERM and SIGKILL. |

**The remaining knobs** — scheduling, notify, fds, metadata.

| Field | Default | Purpose |
|---|---|---|
| `TimerPersistent`, `TimerJitter` | 1 / 0 | Catch up missed timer runs after reboot / random delay per firing. |
| `NotifyAccess` | Main | Who may send sd_notify messages (only `Main` is supported). |
| `FdStoreMax` | 0 | Size of the per-service fd store; 0 disables it. |
| `ServiceSecurity` | inherit | Security descriptor controlling who may manage the service. |
| `DisplayName`, `Description` | — | Human-readable labels for status output. |

### Forward compatibility

The schema version lives at `Machine\System\Services\SchemaVersion` (currently `1`). peinit is deliberately forward-compatible:

- **Unknown values are ignored.** A definition written for a newer peinit does not break an older one.
- **A newer schema version does not block boot.** peinit logs a warning and continues.
- **The schema only grows.** New capability arrives as new optional fields, never as a breaking change to an existing one.

One defensive rule cuts the other way: a *known* field must not appear more than once in a collected definition. A duplicated known field is a validation error, even though the registry would ordinarily give you at most one value per name.

## peinit works from a snapshot, not the live registry

Here is the idea that explains most surprises. peinit does **not** re-read the registry every time it touches a service. It reads definitions at well-defined moments and operates on an in-memory model in between.

Two layers of snapshotting stack on top of each other:

- **Boot generation.** At the start of boot, peinit reads *all* definitions, builds the dependency graph, and validates it. The whole boot runs against that one snapshot. Changes made *during* boot — by an install script, a post-hook — do not perturb the boot in progress.
- **Activation generation.** When peinit starts a specific service, it snapshots *that* service's definition for the entire start. Pre-exec hooks, the token request, the readiness timeout, the first health checks — all use the values captured at activation. Edit a field while the service is `Starting`, and the edit waits for the next start.

peinit learns about registry edits through [change notifications](~peios/the-registry/watches): it subscribes to `Machine\System\Services\` and `Machine\System\Init\` at boot, and processes events in its event loop at a time of its choosing. If the notification queue overflows — a bulk admin operation, a flurry of scripted writes — peinit detects the overflow marker and does a full `reload-config` to resynchronise. You never have to think about the queue; you do have to know that *a change is picked up, not pushed*, and that when it takes *effect* depends on the field.

## Field mutability: when a change takes effect

Every field falls into one of four mutability classes. This table is the one to keep handy.

| Class | When a change takes effect | Fields |
|---|---|---|
| **Immutable at runtime** | Next **restart** only. | `ImagePath`, `Type`, `Identity`, `RequiredPrivileges`, `ErrorControl` |
| **Apply on next start** | Next **start** or explicit graph reload — not while running. | `Requires`, `Wants`, `BindsTo`, `Conflicts`, `OnFailure`, `Conditions`, `Asserts` |
| **Hot-reloaded** | Next relevant **event**, no restart. | `ServiceSecurity` (next control request) |
| **Reloadable at runtime** | Next relevant **operation** (restart, health-check cycle, …), no restart. | `Arguments`, `SuccessExitCodes`, all timeout/retry values, the health-check fields, `RestartPolicy`, `Environment`, `WorkingDirectory`, the hooks, `Readiness`, `NotifyAccess`, `LimitNOFILE`/`LimitCORE`, `FdStoreMax`, `SafeMode`, `DisplayName`, `Description` |

The practical reading: changing *what a process is or runs as* (`ImagePath`, `Identity`, `Type`, privileges, `ErrorControl`) is fundamental enough that it only applies when a fresh process starts — you must `restart`. Changing *policy that peinit consults each time it acts* (timeouts, restart behaviour, health checks) is picked up the next time peinit acts. And `ServiceSecurity` is special: it is re-read on every control request, so an access-control change takes effect on the very next command without touching the running service.

For inactive services the rules are simpler, because there is no running process to protect: a new service entry becomes available once the change notification is processed; a changed timer arms on the next evaluation; a changed dependency takes effect on the next start.

> [!NOTE]
> `reload-config` is the explicit, atomic way to make peinit re-read *everything*. It builds and validates a complete new graph snapshot and swaps it in only if validation passes; running services are not disturbed. It is covered with the rest of the command set in [Controlling services](~peios/peinit/controlling-services).

## Removing a service definition

Deleting a definition from the registry does **not** kill a running instance. peinit learns of the removal through the same notification path and behaves according to whether the service is running:

- **Not running** (Inactive, Failed, Completed, Skipped, Abandoned): peinit discards the in-memory entry immediately. There is nothing to supervise.
- **Running** (Active, Starting, Reloading, Backoff, Stopping): the running process is a [job](~peios/peinit/jobs-and-operations), and a job outlives its definition. peinit marks the entry **definition-removed**, keeps the cached definition only to finish supervising the existing instance, and does *not* restart it when it exits. Once it exits, the entry — and any stored fds — are discarded.

While an entry is definition-removed it keeps satisfying its dependents (it is still running), `stop` still works so you can drain it cleanly, but `start`, `restart`, and `reload` are rejected with `UNKNOWN_SERVICE` — there is no definition to start from. A `status` query reports it with a `definition_removed: true` flag so the draining instance is never invisible.

> [!IMPORTANT]
> Removing a definition is not how you stop a service. It stops *future management*, not work in progress. To actually stop a running service, `stop` it. To prevent it from auto-starting, set `Disabled=1` (see [Triggers and timers](~peios/peinit/triggers-and-timers)). To prevent it from being started at all, deny `SERVICE_START` in its [ServiceSecurity](~peios/peinit/who-can-manage-a-service) descriptor.

## Where to start

To understand the `Type` and `Readiness` fields and the Simple/Oneshot split, read [Simple and Oneshot services](~peios/peinit/service-types).

To understand how a definition becomes a running, supervised process — and what each state in a `status` output means — read [The service lifecycle](~peios/peinit/the-service-lifecycle).

For the complete type-and-default catalogue of every registry key peinit reads, see the [Registry key reference](~peios/peinit/registry-key-reference).
