---
title: The execution environment
type: concept
description: "What a service process looks like the instant it starts: a clean context with only the file descriptors peinit hands it, its own cgroup tree, a constructed environment, configured limits, and — before any of that — the pre-exec hooks and the condition and assert checks that gate the start. This page covers cgroups, stdio, environment layering, working directory, limits, hooks, command parsing, conditions and asserts, and the fd store."
related:
  - peios/peinit/defining-a-service
  - peios/peinit/identity-and-privileges
  - peios/peinit/the-service-lifecycle
  - peios/peinit/output-and-logging
  - peios/the-registry/configuration-and-meaning
---

When peinit starts a service, the process it hands you is built deliberately — a clean context with a known identity, a known environment, and only the resources peinit chose to give it. This page covers everything about that context except the [token](~peios/peinit/identity-and-privileges) (its own page): the cgroup the process lives in, its standard streams, the environment it sees, the limits on it, and the hooks and checks that run *around* the start.

## A clean context

A service inherits **only** what peinit explicitly hands it — its standard streams and any [stored file descriptors](#the-fd-store). Every other descriptor peinit holds — the control socket, the notify socket, the event-loop fd, the registry and authd and eventd connections — is opened close-on-exec, so it closes automatically at exec and can never leak into a service. peinit also resets the child's signal state to defaults (it runs with all signals blocked for its own [signalfd](~peios/peinit/shutdown); a service must not inherit that). The guarantee is that a service starts from a clean slate, not from peinit's privileged one.

## The cgroup tree

Every service runs in its own [cgroup](~peios/threads-and-processes/process-lifecycle) tree under `/sys/fs/cgroup/peinit/`, with separate sub-cgroups for the main process, hooks, and health checks:

```
/sys/fs/cgroup/peinit/<service>/
                       ├── main/     the main process
                       ├── hooks/    pre/post hooks
                       └── health/   health checks
```

peinit uses cgroups for two things only: **tracking** every process a service spawns (so a child that forks its own children is still accounted to the service), and **clean kill** (terminating the entire tree at once, so nothing is orphaned). It does *not* use cgroups for resource accounting or limits.

The split into sub-cgroups serves a real purpose: it satisfies cgroup v2's "no internal processes" rule, and it lets peinit kill a service's *hooks* or *health checks* without touching the main process.

When an old tree cannot be removed — because a process survived SIGKILL in [D-state](~peios/peinit/the-service-lifecycle) and leaked it — peinit creates a fresh **generational** tree (`<service>.gen<N>`) for the next start, so a stuck old instance never blocks a new one. Leaks are surfaced in the service's `warnings`; they are a sign of an underlying I/O fault, covered in [Keeping services running](~peios/peinit/supervision).

## Standard streams

peinit wires a service's standard streams before exec:

- **stdin** is redirected to `/dev/null`. peinit never gives a service an interactive input channel; a service that needs input must obtain it explicitly (a socket, a stored fd).
- **stdout** and **stderr** are redirected to pipes peinit holds, so it can capture and forward every line. This is the subject of [Service output and logging](~peios/peinit/output-and-logging).

## The environment

peinit constructs each service's environment in layers, lowest precedence first — it does **not** pass through its own near-empty startup environment.

1. **Compiled-in base.** A fixed floor peinit always provides — currently just `PATH`:
   `/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`.
2. **Global `EnvVars`.** Each value under `Machine\System\Init\EnvVars\` becomes a variable (value name → variable name). `EnvVars\PATH` overrides the base `PATH`; other names add. Because this key is served by registryd, it reaches only Phase 2 services — the early platform daemons get the compiled-in base only.
3. **Per-service `Environment`.** The definition's own `KEY=VALUE` entries, which override layers 1–2.
4. **Protocol variables.** `NOTIFY_SOCKET` (always) and `LISTEN_FDS` / `LISTEN_FDNAMES` (only when [stored fds](#the-fd-store) are injected). These have the **highest** precedence and cannot be overridden — a service that clobbered `NOTIFY_SOCKET` would break [sd_notify](~peios/peinit/service-types).

A change to `EnvVars\` takes effect on a service's *next start*, like the per-service `Environment` field — it is not pushed into running services.

peinit deliberately does **not** set `HOME`, `USER`, `LOGNAME`, `SHELL`, or `TERM`. Peios identity is a [token](~peios/peinit/identity-and-privileges) (a SID), not a passwd entry, so there is no canonical home directory or login shell to fill in. A service that needs any of these supplies it through `EnvVars\` or its own `Environment`.

> [!WARNING]
> Write access to `Machine\System\Init\EnvVars\` is equivalent to compromising **every service peinit starts** — a principal who can set it can inject `LD_PRELOAD`, `LD_LIBRARY_PATH`, and the like into all of them. peinit deliberately does not filter variable names; the key's [security descriptor](~peios/the-registry/access-control) is the control boundary. Keep it tight — the recommended default is SYSTEM full, Administrators read-only.

## Working directory and limits

| Field | Effect |
|---|---|
| `WorkingDirectory` | The process's working directory. Must be a non-empty absolute path; defaults to `/`. |
| `LimitNOFILE` | `RLIMIT_NOFILE` — the maximum number of open file descriptors. |
| `LimitCORE` | `RLIMIT_CORE` — the maximum core-dump size, in bytes. |

peinit also sets `oom_score_adj`: `-1000` (OOM-immune) for `ErrorControl=Critical` services, and the default `0` for everyone else — so the kernel never picks a Critical platform daemon as an out-of-memory victim.

## Pre-exec and post-exec hooks

Hooks let a service do work *around* its main process without baking it into the binary.

- **`ExecStartPre`** runs *before* the main binary. Each command runs in sequence, in the `hooks/` sub-cgroup; **any** hook exiting non-zero aborts the start (the whole cgroup is killed and the service Fails with `PreHookFailure`). Use it for prerequisites that must hold before the service starts — creating a runtime directory, waiting on a precondition.
- **`ExecStartPost`** runs *after* readiness (Simple) or *after a successful exit* (Oneshot). A post-hook failure is **logged but does not fail the service** — by the time it runs, the service is already up. (A Oneshot that *fails* never runs its post-hooks.)

Hooks run under [`HookIdentity`](~peios/peinit/identity-and-privileges) if set, otherwise the service's own identity. Their output is captured and tagged like the main process's, labelled with the hook (e.g. `jellyfin/ExecStartPre[0]`).

### Command string parsing

The command fields — `ExecStartPre`, `ExecStartPost`, `ExecReload`, `HealthCheck` — are parsed into an argument list with simple, predictable rules. **peinit never invokes a shell.**

- Whitespace splits the command into arguments; double quotes group text containing spaces into one argument and are not retained (`--name="hello world"` → one argument `--name=hello world`).
- There is **no** shell expansion, variable substitution, or globbing. Backslash is literal; a single quote is an ordinary character.
- The first argument is the executable and **must be an absolute path** beginning with `/`. Relative names and PATH search are validation errors.
- An empty or whitespace-only command, or an unclosed quote, is a validation error.

If a command genuinely needs shell features, wrap it in a script and point the field at the script.

`ExecReload` can also be a signal, written `signal:<NAME>` — for example `signal:SIGHUP`. The name must be an exact, canonical Linux signal name (uppercase, no aliases, no numbers); `SIGKILL` and `SIGSTOP` are rejected because they cannot be handled as a reload. With no `ExecReload` at all, reload sends `SIGHUP`. The reload lifecycle is covered in [Controlling services](~peios/peinit/controlling-services).

## Conditions and asserts

Before peinit runs any hook or the main process, it evaluates **conditions** and **asserts** — start-time checks in the same `type:argument` form. The difference is what failure *means*:

- A failed **Condition** *skips* the service — it transitions to [Skipped](~peios/peinit/the-service-lifecycle), which **satisfies its dependents** (it succeeded by not needing to run). Conditions express "only run here if it makes sense."
- A failed **Assert** *fails* the service — it transitions to Failed with `AssertionError`. Asserts express "this was expected to run, and a precondition is missing."

Conditions are checked first; only if all pass are asserts checked. All entries are AND-ed. The check types:

| Type | Form | Passes when |
|---|---|---|
| `path` | `path:<path>` | the path exists (any type) |
| `file` | `file:<path>` | a regular file exists |
| `directory` | `directory:<path>` | a directory exists |
| `registry` | `registry:<key>` | the registry key exists |

Two constraints follow from peinit being single-threaded PID 1, which [must never block](~peios/peinit/overview):

- **`registry:` checks are cache-only.** A `registry:` check may only name a key peinit already caches (under `Machine\System\Services\` or `Machine\System\Init\`); it is evaluated against the in-memory model, never a live read. Naming any other key is a validation error.
- **Filesystem checks run off the main loop.** `path:`/`file:`/`directory:` checks are performed by a short-lived forked helper, not a `stat()` on the event loop, because `stat()` can wedge on a hung mount.

A check that cannot complete within its timeout is treated as **not satisfied** — fail-safe — so a Condition skips and an Assert fails rather than the event loop hanging.

## The fd store

The fd store lets a service preserve file descriptors **across restarts** — most usefully a listening socket, so a stateful daemon can restart without dropping connections. It is opt-in: `FdStoreMax` (default 0) sets the maximum number of fds peinit will hold; 0 disables it.

The mechanics ride on [sd_notify](~peios/peinit/service-types):

- A service stores an fd by sending `FDSTORE=1` with the fd attached (and optionally `FDNAME=<name>`; the default name is `stored`). peinit holds it.
- It removes one with `FDSTOREREMOVE=1` and `FDNAME=<name>`.
- On the **next start**, peinit injects the stored fds starting at fd 3, sets `LISTEN_FDS` to the count and `LISTEN_FDNAMES` to the colon-separated names, then clears the store. (This is the same `LISTEN_FDS` convention systemd uses, so software with existing fd-passing support works unmodified.)

The store **survives an automatic restart** (crash → restart policy → new start) — that is the whole point. It is **cleared** on an *explicit* stop or shutdown (the service is not coming back), and when a [removed definition](~peios/peinit/defining-a-service) is finally discarded.

## Where to start

For the identity half of the launch — how the token is chosen and installed — read [Service identity and privileges](~peios/peinit/identity-and-privileges).

For what happens to the stdout/stderr pipes peinit holds, read [Service output and logging](~peios/peinit/output-and-logging).

For how conditions, asserts, and hooks fit into the start sequence and its states, read [The service lifecycle](~peios/peinit/the-service-lifecycle).
