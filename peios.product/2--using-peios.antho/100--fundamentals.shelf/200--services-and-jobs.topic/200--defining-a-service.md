---
title: Defining a service
type: concept
description: A service is a registry key under Machine\System\Services\, made of typed values. The schema, and the mutability class that decides when a change lands.
related:
  - peios/services-and-jobs/overview
  - peios/services-and-jobs/service-types
  - peios/services-and-jobs/controlling-services
  - peios/services-and-jobs/registry-key-reference
  - peios/registry-concepts/keys-values-and-types
  - peios/registry-concepts/configuration-and-meaning
  - peios/registry-concepts/watches
---

A service is defined by a single key in the [registry](~peios/registry-concepts/overview), under `Machine\System\Services\<name>`. The key's name *is* the service name, and the typed [values](~peios/registry-concepts/keys-values-and-types) inside it are the definition — the binary, who it runs as, what it depends on, how it is supervised. There is no file under `/etc`; there is a registry key.

peinit reads these definitions in two situations: once at boot, to build the service graph, and on demand, when an administrator starts a service or runs `reload-config`. Between those reads it works from an in-memory copy. That last fact is the source of the most common "why didn't my change take effect?" question, and the second half of this page is devoted to it.

## Service names

A service name must be made of characters from `[A-Za-z0-9._-]` and be 1–128 bytes long. Anything else is a validation error. Two characters are pointedly excluded:

- **`/`** — names map directly onto cgroup ids and registry key names, and a slash would be ambiguous in both.
- **`:`** — reserved for peinit-internal synthetic names (for example, the way a hook job is labelled).

The name is how you refer to the service everywhere: in `svctl` commands, in another service's dependency list, in a [ServiceSecurity](~peios/services-and-jobs/who-can-manage-a-service) descriptor, and in the [per-service SID](~peios/services-and-jobs/identity-and-privileges) derived from it.

## The definition schema

A definition is a set of typed registry values. Rather than list all of them in one wall of rows, the tables below group the fields by what they are *for*, with a pointer to the page that explains each group in depth. Every field is optional unless noted; the only hard requirement is `ImagePath`. The full type-and-default catalog lives in the [Registry key reference](~peios/services-and-jobs/registry-key-reference).

**What to run** — the binary and its execution context.

| Field | Default | Purpose |
|---|---|---|
| `ImagePath` *(required)* | — | Absolute path to the service binary. |
| `Arguments` | — | Argument list passed to the binary. |
| `WorkingDirectory` | `/` | Working directory for the process. |
| `Environment` | — | `KEY=VALUE` pairs added to the environment. |
| `RuntimeDirectories` | — | Private directories created under `/run` just before the process starts. See [The execution environment](~peios/services-and-jobs/execution-environment). |
| `LimitNOFILE`, `LimitCORE` | — | `RLIMIT_NOFILE` / `RLIMIT_CORE`. |

**What kind of service** — type and readiness. See [Simple and Oneshot services](~peios/services-and-jobs/service-types).

| Field | Default | Purpose |
|---|---|---|
| `Type` | Simple | `Simple` (long-running) or `Oneshot` (run-to-completion). |
| `Readiness` | Notify | `Notify` (`READY=1` via sd_notify) or `Alive` (ready when the process exists). Ignored for Oneshot. |
| `RemainAfterExit` | 0 | Oneshot only — stay in `Completed` after a successful exit. |
| `SuccessExitCodes` | — | Non-zero exit codes to treat as success. |

**When to start** — triggers and conditions. See [Triggers and timers](~peios/services-and-jobs/triggers-and-timers).

| Field | Default | Purpose |
|---|---|---|
| `Triggers` | — | `boot`, `boot:settled`, `timer:<schedule>`, `tty:released`. Absent = demand-only. |
| `Disabled` | 0 | If 1, triggers must not activate the service (manual start still allowed). |
| `SafeMode` | 0 | If 1, attempt to start in [Safe mode](~peios/services-and-jobs/boot-and-boot-modes). |
| `Conditions`, `Asserts` | — | Start-time checks. A failed condition *skips*; a failed assert *fails*. |

**Who it runs as** — identity and privileges. See [Service identity and privileges](~peios/services-and-jobs/identity-and-privileges).

| Field | Default | Purpose |
|---|---|---|
| `Identity` | `LocalService` | Principal name or SID for the service token. |
| `RequiredPrivileges` | — | Privilege allow-list; everything else is stripped from the token. |
| `HookIdentity` | service's `Identity` | Identity for `ExecStartPre`/`ExecStartPost` hooks. |

**How it relates to other services** — dependencies. See [Dependencies and ordering](~peios/services-and-jobs/dependencies).

| Field | Purpose |
|---|---|
| `Requires` | Hard dependencies — must be satisfied first; their failure fails this service. |
| `Wants` | Soft dependencies — started first if present, but optional. |
| `BindsTo` | Runtime coupling — if the target stops, this stops too. |
| `Conflicts` | Mutual exclusion — starting this stops the named services. |
| `OnFailure` | Service to start when this one enters `Failed`. |

**How it is kept alive** — supervision and health. See [Keeping services running](~peios/services-and-jobs/supervision).

| Field | Default | Purpose |
|---|---|---|
| `ErrorControl` | Normal | `Normal` (stay Failed) or `Critical` (sync + reboot on irrecoverable failure). |
| `RestartPolicy` | OnFailure | `Never` / `OnFailure` / `Always`. |
| `RestartMaxRetries`, `RestartWindow`, `RestartDelay` | 5 / 120 / 1 | Restart budget, the window of health that resets it, and the backoff base. |
| `HealthCheck`, `HealthCheckInterval`, `HealthCheckTimeout`, `HealthCheckRetries` | — / 30 / 5 / 3 | Active health-check command and its timing. |
| `WatchdogTimeout` | 0 | Expected interval between `WATCHDOG=1` pings; 0 disables. |

**The transition phases** — hooks and timeouts. See [The execution environment](~peios/services-and-jobs/execution-environment) and [The service lifecycle](~peios/services-and-jobs/the-service-lifecycle).

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

## Creating and changing a definition

A definition is a registry key, so `reg` can write one. Two tools also know what each field means, and check a definition before writing it.

### From a terminal: `svctl definition`

```
$ svctl definition show sshd
$ svctl definition validate sshd
$ svctl definition create web --set ImagePath=/usr/bin/web --set Requires=lpsd --set Requires=netd:routed
$ svctl definition edit web --set StopTimeout=20 --unset Wants
$ svctl definition delete web
```

`def` is short for `definition`.

- **Fields go by their registry names**, in any case.
- **Values are given as text:**
  - a number as digits;
  - `yes` or `no`;
  - a choice by its name (`Type=Oneshot`);
  - a list with one `--set` for each item, in order.
- **A change is checked first, as peinit checks it.** It goes through peinit's own decoder, and every `timer:` schedule is parsed. If peinit would reject it, nothing is written and you are told why.
- **Only the values that change are written,** in one registry transaction. If one of them has changed since svctl read it, nothing is written.
- **Values that are not fields are kept** as they are.
- **`edit` names any changed fields that wait for a restart** on a running service. See [the mutability classes](#field-mutability-when-a-change-takes-effect).

Some things can't be checked until later:

- **privilege names**, when the token is made;
- **whether the services a definition names exist**, when the graph is built;
- **the identity**, by authd.

`svctl status` after the change is the final word.

### From the desktop: Services Manager

In [Services Manager](~peios/services-and-jobs/controlling-services#from-the-desktop-services-manager), **Edit definition…** opens the selected service's definition in a window of its own. It's in the details pane and on each row's right-click menu. It reads **Definition…** when you may only read the definition. **New service…** on the bar defines a new one.

- **Every field is shown, by group.** Each has its name in words with the registry name beside it, its default, and when a change takes effect.
- **What you type is checked when you leave the field,** as peinit checks it. Anything wrong is said beside the field, and **Save** stays unavailable until it is put right.
- **Save writes as svctl does.** Only the changes are written, in one transaction, and it is refused if someone else changed a value meanwhile. **Revert** reads the definition again. If the service is running, Save says which changes wait for a restart.
- **Delete…** asks first. A running service carries on until it stops.
- **What you may do is asked of the registry:**
  - changing needs the right to set values on the service's key;
  - defining a service needs the right to create keys under `Machine\System\Services`;
  - deleting needs `DELETE` on the key.

  Without those rights, the definition is shown with every field fixed and the reason said.
- **Who may control the service** (`ServiceSecurity`) is changed with **Who may control it…**, not here. See [Who can manage a service](~peios/services-and-jobs/who-can-manage-a-service).

## peinit works from a snapshot, not the live registry

Here is the idea that explains most surprises. peinit does **not** re-read the registry every time it touches a service. It reads definitions at well-defined moments and operates on an in-memory model in between.

Two layers of snapshotting stack on top of each other:

- **Boot generation.** At the start of boot, peinit reads *all* definitions, builds the dependency graph, and validates it. The whole boot runs against that one snapshot. Changes made *during* boot — by an install script, a post-hook — do not perturb the boot in progress.
- **Activation generation.** When peinit starts a specific service, it snapshots *that* service's definition for the entire start. Pre-exec hooks, the token request, the readiness timeout, the first health checks — all use the values captured at activation. Edit a field while the service is `Starting`, and the edit waits for the next start.

peinit learns about registry edits through [change notifications](~peios/registry-concepts/watches): it subscribes to `Machine\System\Services\` and `Machine\System\Init\` at boot, and processes events in its event loop at a time of its choosing. If the notification queue overflows — a bulk admin operation, a flurry of scripted writes — peinit detects the overflow marker and does a full `reload-config` to resynchronise. You never have to think about the queue; you do have to know that *a change is picked up, not pushed*, and that when it takes *effect* depends on the field.

## Field mutability: when a change takes effect

Every field falls into one of four mutability classes. This table is the one to keep handy.

| Class | When a change takes effect | Fields |
|---|---|---|
| **Immutable at runtime** | Next **restart** only. | `ImagePath`, `Type`, `Identity`, `RequiredPrivileges`, `ErrorControl`, `RemainAfterExit`, and, while it is running, `Triggers` and `Disabled` |
| **Apply on next start** | Next **start** or explicit graph reload — not while running. | `Requires`, `Wants`, `BindsTo`, `Conflicts`, `OnFailure`, `Conditions`, `Asserts` |
| **Hot-reloaded** | Next relevant **event**, no restart. | `ServiceSecurity` (next control request) |
| **Reloadable at runtime** | Next relevant **operation** (restart, health-check cycle, …), no restart. | `Arguments`, `SuccessExitCodes`, all timeout/retry values, the health-check fields, `RestartPolicy`, `Environment`, `WorkingDirectory`, the hooks and `HookIdentity`, `Readiness`, `NotifyAccess`, `LimitNOFILE`/`LimitCORE`, `FdStoreMax`, `TTYPath`/`TTYPrecedence`, `RuntimeDirectories`, `Provides`, `TimerPersistent`/`TimerJitter`, `SafeMode`, `DisplayName`, `Description` |

On a service that is not running, `Triggers` and `Disabled` take effect as soon as peinit has read the change: that is what arms a timer added to an inactive service.

The practical reading: changing *what a process is or runs as* (`ImagePath`, `Identity`, `Type`, privileges, `ErrorControl`) is fundamental enough that it only applies when a fresh process starts — you must `restart`. Changing *policy that peinit consults each time it acts* (timeouts, restart behaviour, health checks) is picked up the next time peinit acts. And `ServiceSecurity` is special: it is re-read on every control request, so an access-control change takes effect on the very next command without touching the running service.

For inactive services the rules are simpler, because there is no running process to protect: a new service entry becomes available once the change notification is processed; a changed timer arms on the next evaluation; a changed dependency takes effect on the next start.

> [!NOTE]
> `reload-config` is the explicit, atomic way to make peinit re-read *everything*. It builds and validates a complete new graph snapshot and swaps it in only if validation passes; running services are not disturbed. It is covered with the rest of the command set in [Controlling services](~peios/services-and-jobs/controlling-services).

## Removing a service definition

Deleting a definition from the registry does **not** kill a running instance. peinit learns of the removal through the same notification path and behaves according to whether the service is running:

- **Not running** (Inactive, Failed, Completed, Skipped, Abandoned): peinit discards the in-memory entry immediately. There is nothing to supervise.
- **Running** (Active, Starting, Reloading, Backoff, Stopping): the running process is a [job](~peios/services-and-jobs/jobs-and-operations), and a job outlives its definition. peinit marks the entry **definition-removed**, keeps the cached definition only to finish supervising the existing instance, and does *not* restart it when it exits. Once it exits, the entry — and any stored fds — are discarded.

While an entry is definition-removed it keeps satisfying its dependents (it is still running), `stop` still works so you can drain it cleanly, but `start`, `restart`, and `reload` are rejected with `UNKNOWN_SERVICE` — there is no definition to start from. A `status` query reports it with a `definition_removed: true` flag so the draining instance is never invisible.

> [!IMPORTANT]
> Removing a definition is not how you stop a service. It stops *future management*, not work in progress. To actually stop a running service, `stop` it. To prevent it from auto-starting, set `Disabled=1` (see [Triggers and timers](~peios/services-and-jobs/triggers-and-timers)). To prevent it from being started at all, deny `SERVICE_START` in its [ServiceSecurity](~peios/services-and-jobs/who-can-manage-a-service) descriptor.

## Where to start

To understand the `Type` and `Readiness` fields and the Simple/Oneshot split, read [Simple and Oneshot services](~peios/services-and-jobs/service-types).

To understand how a definition becomes a running, supervised process — and what each state in a `status` output means — read [The service lifecycle](~peios/services-and-jobs/the-service-lifecycle).

For the complete type-and-default catalog of every registry key peinit reads, see the [Registry key reference](~peios/services-and-jobs/registry-key-reference).
