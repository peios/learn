---
title: Registry key reference
type: reference
description: "The complete catalogue: every field of the service definition schema with its registry type and default, and every registry key peinit reads or writes — service definitions, boot configuration, and operational parameters. Each entry links to the page that defines its meaning."
related:
  - peios/peinit/defining-a-service
  - peios/peinit/controlling-services
  - peios/the-registry/keys-values-and-types
  - peios/the-registry/regman
---

This page is the reference catalogue for everything peinit reads from or writes to the [registry](~peios/the-registry/overview): the full service-definition schema with types and defaults, and every key peinit touches outside the service definitions. For the *meaning* of each item, follow the link in its row; this page is for looking up a type, a default, or a path.

> [!NOTE]
> The registry stores a value's type but not its meaning — that is what [`regman`](~peios/the-registry/regman) and these docs are for. A value peinit accepts at write time can still be rejected when peinit reads and validates it; this page lists the schema, not the validation rules (those live on each field's page).

## Registry value types

Service definition fields map onto registry [value types](~peios/the-registry/keys-values-and-types) as follows:

| Schema type | Registry type | Is |
|---|---|---|
| string | `REG_SZ` | A UTF-8 string. |
| multi_string | `REG_MULTI_SZ` | An ordered list of strings. |
| dword | `REG_DWORD` | A 32-bit unsigned integer. |
| binary | `REG_BINARY` | A raw byte sequence. |
| (timestamp) | `REG_QWORD` | A 64-bit value — used for timer last-run timestamps. |

## The service definition schema

Every service is a key under `Machine\System\Services\<name>`; these are the values inside it. Only `ImagePath` is required. Fields are grouped by purpose; for full semantics see [Defining a service](~peios/peinit/defining-a-service) and the linked pages.

**Execution** — see [The execution environment](~peios/peinit/execution-environment)

| Field | Type | Default | Meaning |
|---|---|---|---|
| `ImagePath` | string | *(required)* | Absolute path to the service binary. |
| `Arguments` | multi_string | — | Command-line arguments. |
| `WorkingDirectory` | string | `/` | Working directory (non-empty absolute path). |
| `Environment` | multi_string | — | `KEY=VALUE` pairs added to the environment. |
| `RuntimeDirectories` | multi_string | — | Directories created directly under `/run` just before the main process starts, each secured for SYSTEM, Administrators, and the service's own SID. |
| `LimitNOFILE` | dword | — | `RLIMIT_NOFILE`. |
| `LimitCORE` | dword | — | `RLIMIT_CORE`, in bytes. |

> [!NOTE]
> Each `RuntimeDirectories` entry is a plain relative name — just `foo`, never a path — and must not contain `/`, `\`, `.`, `..`, NUL, or control characters. For an entry `foo`, peinit creates `/run/foo` immediately before launching the main process and applies a Peios file security descriptor granting full access to SYSTEM, Administrators, and this service's own SID. If the directory can't be created or the descriptor can't be applied, the start fails with `ParentSetupFailure`. peinit does *not* remove these directories when the service stops — `/run` is a boot-scoped tmpfs that the next boot clears for you.

**Type and readiness** — see [Simple and Oneshot services](~peios/peinit/service-types)

| Field | Type | Default | Meaning |
|---|---|---|---|
| `Type` | dword | 0 (Simple) | 0 = Simple, 1 = Oneshot. |
| `Readiness` | dword | 0 (Notify) | 0 = Notify (`READY=1`), 1 = Alive. Ignored for Oneshot. |
| `RemainAfterExit` | dword | 0 | Oneshot only — stay Completed after a successful exit. |
| `SuccessExitCodes` | multi_string | — | Non-zero exit codes treated as success (each 0–255). |

**Activation** — see [Triggers and timers](~peios/peinit/triggers-and-timers)

| Field | Type | Default | Meaning |
|---|---|---|---|
| `Triggers` | multi_string | — | `boot` and/or `timer:<schedule>`. Absent = demand-only. |
| `Disabled` | dword | 0 | If 1, triggers must not activate the service. |
| `SafeMode` | dword | 0 | If 1, attempt to start in Safe mode. Critical implies SafeMode. |
| `Conditions` | multi_string | — | Start-time checks; a failure *skips* the service. |
| `Asserts` | multi_string | — | Start-time checks; a failure *fails* the service. |
| `PreStartCheckTimeout` | dword | 5 | Seconds allowed for the helper that evaluates filesystem `Conditions`/`Asserts`; if it overruns, it is killed and the check counts as *not satisfied* (a Condition skips, an Assert fails). |
| `TimerPersistent` | dword | 1 | Catch up a missed timer run after a reboot. |
| `TimerJitter` | dword | 0 | Maximum random delay (seconds) added to each firing. |

**Identity** — see [Service identity and privileges](~peios/peinit/identity-and-privileges)

| Field | Type | Default | Meaning |
|---|---|---|---|
| `Identity` | string | `LocalService` | Principal name or SID for the service token. |
| `RequiredPrivileges` | multi_string | — | Privilege allow-list; all others are removed from the token. |
| `HookIdentity` | string | (service's `Identity`) | Identity for `ExecStartPre`/`ExecStartPost`. |

**Dependencies** — see [Dependencies and ordering](~peios/peinit/dependencies)

| Field | Type | Default | Meaning |
|---|---|---|---|
| `Requires` | multi_string | — | Hard dependencies. |
| `Wants` | multi_string | — | Soft dependencies. |
| `BindsTo` | multi_string | — | Runtime coupling. |
| `Conflicts` | multi_string | — | Mutual exclusion. |
| `OnFailure` | string | — | Service to start when this one enters Failed. |

**Supervision and health** — see [Keeping services running](~peios/peinit/supervision)

| Field | Type | Default | Meaning |
|---|---|---|---|
| `ErrorControl` | dword | 0 (Normal) | 0 = Normal, 1 = Critical (sync + reboot on irrecoverable failure). |
| `RestartPolicy` | dword | 1 (OnFailure) | 0 = Never, 1 = OnFailure, 2 = Always. |
| `RestartMaxRetries` | dword | 5 | Consecutive restarts before Failed. |
| `RestartWindow` | dword | 120 | Seconds of Active health that resets the restart counter. |
| `RestartDelay` | dword | 1 | Backoff base (doubles per failure, capped at 60). |
| `HealthCheck` | string | — | Periodic health-check command. |
| `HealthCheckInterval` | dword | 30 | Seconds between health checks. |
| `HealthCheckTimeout` | dword | 5 | Seconds before a check is killed and failed. |
| `HealthCheckRetries` | dword | 3 | Consecutive failures before unhealthy. |
| `WatchdogTimeout` | dword | 0 | Seconds between expected `WATCHDOG=1` pings; 0 disables. |

**Transition phases** — see [The service lifecycle](~peios/peinit/the-service-lifecycle) and [Controlling services](~peios/peinit/controlling-services)

| Field | Type | Default | Meaning |
|---|---|---|---|
| `ExecStartPre` | multi_string | — | Commands run before the binary (sequential; any failure aborts start). |
| `ExecStartPost` | multi_string | — | Commands run after readiness / successful exit (failure logged, not fatal). |
| `ExecReload` | string | — (SIGHUP) | Reload command, or `signal:<NAME>`. |
| `StartTimeout` | dword | 30 | Seconds for the whole start sequence. |
| `StopTimeout` | dword | 10 | Seconds between SIGTERM and SIGKILL. |

**Notify, fds, security, metadata**

| Field | Type | Default | Meaning |
|---|---|---|---|
| `NotifyAccess` | dword | 0 (Main) | Who may send sd_notify (only Main is supported). |
| `FdStoreMax` | dword | 0 | Max fds in the [fd store](~peios/peinit/execution-environment); 0 disables it. |
| `ServiceSecurity` | binary | inherit parent | [Descriptor](~peios/peinit/who-can-manage-a-service) controlling who may manage the service. |
| `DisplayName` | string | — | Human-readable name for status display. |
| `Description` | string | — | Description of the service. |

## Service definition keys

| Key | Type | Purpose | See |
|---|---|---|---|
| `Machine\System\Services\` | (parent key) | Parent of all service definitions; each child key is a service. | [Defining a service](~peios/peinit/defining-a-service) |
| `Machine\System\Services\SchemaVersion` | dword | Schema version guard (currently 1). | [Defining a service](~peios/peinit/defining-a-service) |
| `Machine\System\Services\<name>\LastTimerRun` | `REG_QWORD` | Last-run timestamp for a single-trigger persistent timer. Written by peinit. | [Triggers and timers](~peios/peinit/triggers-and-timers) |
| `Machine\System\Services\<name>\TimerState\` | (subkey) | Per-trigger last-run timestamps for multi-trigger services. Each value is named by the percent-encoded schedule string and holds a `REG_QWORD`. | [Triggers and timers](~peios/peinit/triggers-and-timers) |

## Boot configuration

Under `Machine\System\Boot\`:

| Key | Type | Default | Purpose | See |
|---|---|---|---|---|
| `MaxParallelStarts` | dword (> 0) | 10 | Maximum services starting concurrently. Missing → default; zero/invalid → Recovery. | [Boot and boot modes](~peios/peinit/boot-and-boot-modes) |
| `BootSuccessGrace` | dword | 30 | Seconds a Critical service must hold a satisfying state before boot is successful. | [Boot and boot modes](~peios/peinit/boot-and-boot-modes) |
| `ShutdownTimeout` | dword | 90 | Maximum seconds for the whole graceful shutdown. | [Shutdown](~peios/peinit/shutdown) |

## Operational parameters

Under `Machine\System\Init\`:

| Key | Type | Default | Purpose | See |
|---|---|---|---|---|
| `ControlSecurity` | binary | SYSTEM full; Administrators shutdown + reload-config | Descriptor for system-level control operations. | [Who can manage a service](~peios/peinit/who-can-manage-a-service) |
| `MaxControlConnections` | dword | 32 | Maximum concurrent control-socket connections. | [Controlling services](~peios/peinit/controlling-services) |
| `MaxRequestSize` | dword | 65536 | Maximum control-socket request size (bytes). | [Controlling services](~peios/peinit/controlling-services) |
| `ConnectionTimeout` | dword | 30 | Seconds before an idle control connection is closed. | [Controlling services](~peios/peinit/controlling-services) |
| `MaxLogLineLength` | dword | 8192 | Maximum bytes per service output line before truncation. | [Service output and logging](~peios/peinit/output-and-logging) |
| `MaxLogBufferPerService` | dword | 65536 | Maximum bytes buffered per service pipe before back-pressure. | [Service output and logging](~peios/peinit/output-and-logging) |
| `EnvVars\` | (parent key) | empty | Default environment variables injected into Phase 2 services (value name = variable, `REG_SZ` data = value). The descriptor here is security-critical. | [The execution environment](~peios/peinit/execution-environment) |
| `ProvisionedPaths\` | (parent key) | empty | Boot-time path provisioning: each child key names one directory or file that peinit creates and secures after registryd starts and before Phase 2 — the registry-backed equivalent of tmpfiles.d. | [Boot and boot modes](~peios/peinit/boot-and-boot-modes) |
| `ProvisionedPaths\<name>\Kind` | string | *(required)* | `directory` or `file` — what to create at `Path`. | [Boot and boot modes](~peios/peinit/boot-and-boot-modes) |
| `ProvisionedPaths\<name>\Path` | string | *(required)* | Absolute path to create or verify. | [Boot and boot modes](~peios/peinit/boot-and-boot-modes) |
| `ProvisionedPaths\<name>\Security` | binary | SYSTEM + Administrators full, users read/traverse | Peios file security descriptor to apply to the object. | [Boot and boot modes](~peios/peinit/boot-and-boot-modes) |
| `ProvisionedPaths\<name>\Required` | dword | 0 | If 1, a failure to provision this entry sends boot to [Recovery mode](~peios/peinit/boot-and-boot-modes) before Phase 2 starts. | [Boot and boot modes](~peios/peinit/boot-and-boot-modes) |

> [!NOTE]
> A few `ProvisionedPaths` rules worth knowing before you rely on them: `Kind=file` never truncates an existing file (it only makes sure the file is present), and peinit does *not* create missing parent directories for you — define each directory you need as its own entry, or depend on the package that owns the parent. A malformed entry is logged and skipped rather than blocking boot; only an entry you mark `Required=1` can send boot to [Recovery mode](~peios/peinit/boot-and-boot-modes), and only when it genuinely can't be created or secured.

## Keys peinit reads from other subsystems

| Key | Type | Purpose | See |
|---|---|---|---|
| `Machine\System\eventd\LogSocketPath` | string | Path of eventd's log datagram socket, where peinit forwards service output. | [Service output and logging](~peios/peinit/output-and-logging) |

## Where to start

For how these fields combine into a working definition and when changes take effect, read [Defining a service](~peios/peinit/defining-a-service).

To look up the meaning, valid range, and effect-timing of any key on a live system, use [`regman`](~peios/the-registry/regman).
