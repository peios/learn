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
| Triggers | multi_string | no | -- | Trigger list. Each entry is `type` or `type:argument`. See §3.1. If absent, service is demand-only. |
| Disabled | dword | no | 0 | If 1, triggers MUST NOT activate this service. Manual start via control interface is still permitted. |
| SafeMode | dword | no | 0 | If 1, peinit MUST attempt to start this service in Safe mode. Best-effort -- failure does not block Safe mode. ErrorControl=Critical implies SafeMode. |
| Identity | string | no | LocalService | Principal name for the service token. See §3.3. |
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
| PreStartCheckTimeout | dword | no | 5 | Seconds before a filesystem-backed Condition/Assert helper is killed and its checks are considered not satisfied. |
| StartTimeout | dword | no | 30 | Seconds. Covers the entire start sequence: pre-hooks, fork/exec, and readiness wait. |
| StopTimeout | dword | no | 10 | Seconds to wait after SIGTERM before sending SIGKILL. |
| WatchdogTimeout | dword | no | 0 | Seconds between expected `WATCHDOG=1` pings. 0 = disabled. |
| HealthCheck | string | no | -- | Command to run periodically as an active health check. Exit 0 = healthy. |
| HealthCheckInterval | dword | no | 30 | Seconds between health check runs. |
| HealthCheckTimeout | dword | no | 5 | Seconds before a health check is killed and considered failed. |
| HealthCheckRetries | dword | no | 3 | Consecutive failures before the service is considered unhealthy. |
| RestartPolicy | dword | no | 1 (OnFailure) | 0 = Never, 1 = OnFailure, 2 = Always. |
| RestartMaxRetries | dword | no | 5 | Maximum consecutive restarts before entering Failed state. The counter resets after the service sustains RestartWindow of Active health (see RestartWindow). |
| RestartWindow | dword | no | 120 | Seconds. The restart counter resets to zero once the service stays Active this long without failing. |
| RestartDelay | dword | no | 1 | Seconds to wait before restarting. Doubles on each consecutive failure (exponential backoff), capped at 60 seconds. |
| Readiness | dword | no | 0 (Notify) | 0 = Notify (sd_notify READY=1), 1 = Alive (process exists). Ignored for Oneshot services. |
| NotifyAccess | dword | no | 0 (Main) | Who may send sd_notify messages. 0 = Main (tracked main PID only). |
| FdStoreMax | dword | no | 0 | Maximum number of file descriptors in the per-service fd store. 0 = fd store disabled. |
| TimerPersistent | dword | no | 1 | If 1, catch up missed timer runs after reboot. |
| TimerJitter | dword | no | 0 | Maximum random delay in seconds added to each timer firing. |
| Environment | multi_string | no | -- | KEY=VALUE pairs added to the service's environment. |
| WorkingDirectory | string | no | / | Working directory for the service process. |
| RuntimeDirectories | multi_string | no | -- | Service-private runtime directories under `/run`, created before the service's main process starts. |
| LimitNOFILE | dword | no | -- | RLIMIT_NOFILE (max open file descriptors). |
| LimitCORE | dword | no | -- | RLIMIT_CORE (core dump size in bytes). |
| Conditions | multi_string | no | -- | Start-time conditions. Each entry is `type:argument`. All MUST pass or the service is skipped. |
| Asserts | multi_string | no | -- | Start-time assertions. Same format as Conditions. If any fails, service enters Failed. |
| DisplayName | string | no | -- | Human-readable name for status display. |
| Description | string | no | -- | Description of what the service does. |
| ServiceSecurity | binary | no | inherit parent | Security Descriptor controlling runtime operations on this service. See §3.4. |

Known service-definition fields MUST NOT appear more than once in
a collected definition. Duplicate known fields are validation
errors. This is a defensive Peinit ingestion rule even when the LCS
registry representation ordinarily provides at most one value per
name. Unknown registry values are still ignored for forward
compatibility.

## Field value formats

- **String fields** -- when present, string fields MUST be
  non-empty unless this section explicitly defines empty-string
  handling for the field. An empty string for `Identity` is treated
  the same as an absent `Identity` and defaults to `LocalService`.
  An empty string for `HookIdentity` is treated the same as an
  absent `HookIdentity` and falls back to the service's `Identity`.
  `DisplayName` and `Description` use empty string as absence.
- **WorkingDirectory** -- when present, MUST be a non-empty
  absolute path. If absent, it defaults to `/`. Filesystem
  existence, type, and access checks are performed by the later
  validation or runtime rules that consume the working directory.
- **RuntimeDirectories** -- each entry names one directory directly
  under `/run`. Entries MUST be non-empty relative names and MUST
  NOT contain `/`, `\`, `.`, `..`, NUL, or control characters. For
  an entry `foo`, peinit creates `/run/foo` immediately before
  launching the service's main process. The directory is protected
  with a Peios file SD granting full access to SYSTEM,
  Administrators, and the service SID for this service. Hook
  processes inherit the service environment and identity rules but
  do not cause runtime-directory provisioning; provisioning belongs
  to the main service start. If directory creation or SD assignment
  fails, the service start fails with `ParentSetupFailure`. peinit
  does not remove runtime directories when the service stops; `/run`
  is a boot-scoped tmpfs and is cleared by the next boot.

- **SuccessExitCodes** -- each entry is a decimal integer in the
  range 0-255 (a process exit code). Signal names and ranges are
  NOT accepted. Code 0 is always success implicitly and need not be
  listed.
- **Identity** / **HookIdentity** -- either a well-known principal
  name (`SYSTEM`, `LocalService`, `NetworkService`, …), matched
  case-insensitively, or a literal SID string (`S-1-5-18`). authd
  resolves any other name (§3.3).

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

### Evaluation constraints

peinit is single-threaded PID 1 and MUST NOT block its event loop
while evaluating checks. Two constraints follow:

- **`registry:` checks are cache-only.** A `registry:<key>` check
  may only reference a key peinit already caches (under
  `Machine\System\Services\` or `Machine\System\Init\`, §3.5); it is
  evaluated against the in-memory model, never via a live registry
  read. A `registry:` check naming any other key is a **validation
  error** -- the definition is rejected at load (cause
  ValidationError).
- **Filesystem checks (`path:`/`file:`/`directory:`) are evaluated
  off the main loop.** A `stat()` can block uninterruptibly on hung
  I/O, so peinit evaluates these in a bounded forked helper rather
  than calling `stat()` from its event loop (see §4.1).

A filesystem check that cannot complete within
`PreStartCheckTimeout` seconds is treated as **not satisfied**
(fail-safe): the Condition skips the service, and the Assert fails
it with cause AssertionError. peinit kills the helper cgroup and
unregisters the helper result fd before continuing.

## Command string parsing

Fields that contain executable commands (ExecStartPre,
ExecStartPost, ExecReload, HealthCheck) are parsed as follows:
whitespace-split into argv, with double-quote grouping for
arguments containing spaces. No shell expansion, no variable
substitution, no glob expansion. peinit MUST NOT invoke a shell.

For command parsing, whitespace means ASCII space, horizontal tab,
line feed, carriage return, form feed, and vertical tab. Other
Unicode whitespace code points are ordinary argument characters.

Double quotes group text into a single argv element and are not
retained in the resulting argument. Quote grouping MAY occur inside
an argument; for example, `--name="hello world"` becomes one argv
entry with the value `--name=hello world`. Empty quoted strings are
preserved as empty argv entries.

Backslash has no escape semantics and is copied literally. Single
quote is an ordinary character.

An empty or whitespace-only command string is invalid. An unclosed
double quote is invalid. Invalid command strings are definition
validation errors.

Command string parsing only produces argv. Executable path
validation, if any, is performed by the service-definition
validation or runtime execution rules that consume the parsed argv.

For service-definition executable command fields (`ExecStartPre`,
`ExecStartPost`, command-form `ExecReload`, and `HealthCheck`),
the first argv element is the executable path and MUST be an absolute
path beginning with `/`. Relative executable names, empty executable
names, and PATH-search execution are invalid definition-validation
errors. Arguments after argv[0] are opaque strings and are not path
validated by this rule.

### ExecReload signal names

When `ExecReload` uses the `signal:<name>` form, `<name>` MUST be
an exact canonical Linux standard signal name. Numeric signal
values, realtime signal expressions, aliases, lowercase spellings,
and names with surrounding whitespace are invalid. `SIGKILL` and
`SIGSTOP` are invalid for reload because they cannot be handled by
the service as a configuration reload signal.

peinit MUST map the accepted names to the host signal numbers before
runtime delivery. At minimum, peinit MUST accept the standard
non-realtime Linux signal names other than `SIGKILL` and `SIGSTOP`
(`SIGHUP`, `SIGINT`, `SIGQUIT`, `SIGILL`, `SIGTRAP`, `SIGABRT`,
`SIGBUS`, `SIGFPE`, `SIGUSR1`, `SIGSEGV`, `SIGUSR2`, `SIGPIPE`,
`SIGALRM`, `SIGTERM`, `SIGSTKFLT`, `SIGCHLD`, `SIGCONT`,
`SIGTSTP`, `SIGTTIN`, `SIGTTOU`, `SIGURG`, `SIGXCPU`, `SIGXFSZ`,
`SIGVTALRM`, `SIGPROF`, `SIGWINCH`, `SIGIO`, `SIGPWR`, and
`SIGSYS`).

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
