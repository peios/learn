---
title: Definition Schema
---

Every service is defined by a registry key under
`Machine\System\Services\<name>`. The key name is the service
name. This section defines every field in the service definition
and its semantics.

A schema version is stored at
`Machine\System\Services\SchemaVersion` (dword, currently 1).
peinit MUST be forward-compatible: unknown registry values MUST
be ignored. A newer schema version MUST NOT prevent boot -- peinit
logs a warning but continues. The schema evolves additively (new
optional fields) without breaking older peinit versions.

## Fields

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| ImagePath | string | yes | -- | Absolute path to the service binary. |
| Arguments | multi_string | no | -- | Command-line arguments passed to the binary. |
| Type | dword | no | 0 (Simple) | Service type. 0 = Simple, 1 = Oneshot. |
| Triggers | multi_string | no | -- | Trigger list. Each entry is `type` or `type:argument`. See the Overview section. If absent, service is demand-only. |
| Disabled | dword | no | 0 | If 1, triggers MUST NOT activate this service. Manual start via control interface is still permitted. |
| SafeMode | dword | no | 0 | If 1, peinit MUST attempt to start this service in Safe mode. Best-effort -- failure does not block Safe mode. ErrorControl=Critical implies SafeMode. |
| Identity | string | no | LocalService | Principal name for the service token. See the Identity section. |
| RequiredPrivileges | multi_string | no | -- | Privilege names. All other privileges are removed from the token before exec. If absent, the token's default privileges are used. |
| Requires | multi_string | no | -- | Hard dependencies. All MUST be satisfied before this service starts. If any fails, this service fails. |
| Wants | multi_string | no | -- | Soft dependencies. Started before this service if they exist. Failure does not prevent this service from starting. |
| BindsTo | multi_string | no | -- | Runtime coupling. If any of these stop (for any reason), this service is stopped. |
| Conflicts | multi_string | no | -- | Mutual exclusion. Starting this service stops conflicting services. |
| OnFailure | string | no | -- | Service name to start when this service enters Failed state. |
| ErrorControl | dword | no | 0 (Normal) | 0 = Normal (remain Failed). 1 = Critical (sync and reboot). |
| RemainAfterExit | dword | no | 0 | Oneshot only. If 1, service stays in Completed state after successful exit. |
| SuccessExitCodes | multi_string | no | -- | Non-zero exit codes treated as success. |
| ExecStartPre | multi_string | no | -- | Commands to run before the main binary. Run sequentially; any failure aborts service start. |
| ExecStartPost | multi_string | no | -- | Commands to run after readiness (Simple) or successful exit (Oneshot). |
| HookIdentity | string | no | -- | Principal name for ExecStartPre and ExecStartPost processes. If absent, hooks run as the service's Identity. |
| ExecReload | string | no | -- | Reload command or signal. Prefix with `signal:` for a signal (e.g., `signal:SIGHUP`); anything else is parsed as an argv command. If absent, reload sends SIGHUP. |
| StartTimeout | dword | no | 30 | Seconds. Covers the entire start sequence: pre-hooks, fork/exec, and readiness wait. |
| StopTimeout | dword | no | 10 | Seconds to wait after SIGTERM before sending SIGKILL. |
| WatchdogTimeout | dword | no | 0 | Seconds between expected `WATCHDOG=1` pings. 0 = disabled. |
| HealthCheck | string | no | -- | Command to run periodically as an active health check. Exit 0 = healthy. |
| HealthCheckInterval | dword | no | 30 | Seconds between health check runs. |
| HealthCheckTimeout | dword | no | 5 | Seconds before a health check is killed and considered failed. |
| HealthCheckRetries | dword | no | 3 | Consecutive failures before the service is considered unhealthy. |
| RestartPolicy | dword | no | 1 (OnFailure) | 0 = Never, 1 = OnFailure, 2 = Always. |
| RestartMaxRetries | dword | no | 5 | Maximum restarts within RestartWindow before entering Failed state. |
| RestartWindow | dword | no | 120 | Seconds. Restart counter resets if this window passes without a failure. |
| RestartDelay | dword | no | 1 | Seconds to wait before restarting. Doubles on each consecutive failure (exponential backoff), capped at 60 seconds. |
| Readiness | dword | no | 0 (Notify) | 0 = Notify (sd_notify READY=1), 1 = Alive (process exists). Ignored for Oneshot services. |
| NotifyAccess | dword | no | 0 (Main) | Who may send sd_notify messages. 0 = Main (tracked main PID only). |
| FdStoreMax | dword | no | 0 | Maximum number of file descriptors in the per-service fd store. 0 = fd store disabled. |
| TimerPersistent | dword | no | 1 | If 1, catch up missed timer runs after reboot. |
| TimerJitter | dword | no | 0 | Maximum random delay in seconds added to each timer firing. |
| Environment | multi_string | no | -- | KEY=VALUE pairs added to the service's environment. |
| WorkingDirectory | string | no | / | Working directory for the service process. |
| LimitNOFILE | dword | no | -- | RLIMIT_NOFILE (max open file descriptors). |
| LimitCORE | dword | no | -- | RLIMIT_CORE (core dump size in bytes). |
| Conditions | multi_string | no | -- | Start-time conditions. Each entry is `type:argument`. All MUST pass or the service is skipped. |
| Asserts | multi_string | no | -- | Start-time assertions. Same format as Conditions. If any fails, service enters Failed. |
| DisplayName | string | no | -- | Human-readable name for status display. |
| Description | string | no | -- | Description of what the service does. |
| ServiceSecurity | binary | no | inherit parent | Security Descriptor controlling runtime operations on this service. See the Security section. |

## Conditions and Asserts

Conditions and Asserts use the same `type:argument` format and the
same check types:

| Check type | Format | Passes when |
|---|---|---|
| path | `path:<path>` | Path exists (any type). |
| file | `file:<path>` | Regular file exists. |
| directory | `directory:<path>` | Directory exists. |
| registry | `registry:<key>` | Registry key exists. |

**Conditions:** if any condition fails, the service is skipped
(not failed). A skipped service satisfies its dependents -- it
"succeeded" by not needing to run. All entries are AND'd.

**Asserts:** if any assert fails, the service enters Failed state
with cause AssertionError. A failed assert means the service was
expected to run but a required precondition is missing.
All entries are AND'd.

Conditions are evaluated first. If all conditions pass, asserts are
evaluated. Evaluation happens before dependency resolution and
pre-exec hooks.

## Command string parsing

Fields that contain executable commands (ExecStartPre,
ExecStartPost, ExecReload, HealthCheck) are parsed as follows:
whitespace-split into argv, with double-quote grouping for
arguments containing spaces. No shell expansion, no variable
substitution, no glob expansion. peinit MUST NOT invoke a shell.

If a command requires shell features, a wrapper script MUST be
used.

## Registry value types

Service definition fields map to registry value types as follows:

| Spec type | Registry type | Description |
|---|---|---|
| string | REG_SZ | UTF-8 string. |
| multi_string | REG_MULTI_SZ | Ordered list of strings. |
| dword | REG_DWORD | 32-bit unsigned integer. |
| binary | REG_BINARY | Raw byte sequence. |
