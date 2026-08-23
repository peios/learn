---
title: The Base Environment
description: Every service environment is built from scratch in four layers, lowest precedence first, with nothing inherited.
---

peinit constructs every service and hook process's environment from
scratch, in four layers, lowest precedence first. Nothing is inherited:
peinit's own startup environment holds `TERM` and nothing else (§2.1),
and none of it is passed through.

## Layer 1: the compiled-in base

One variable:

| Variable | Value |
|---|---|
| `PATH` | `/sbin:/bin` |

Executables are addressed through the root-level StrataFS runtime views.
Package storage paths under `/usr` are deliberately not on the default
search path.

## Layer 2: global environment variables

Each value under `Machine\System\Init\EnvVars\` becomes a variable: the
value name is the variable name, the `REG_SZ` data is the value. An
`EnvVars\PATH` overrides the compiled-in `PATH`; every other name adds.

A malformed entry — an empty name, or a name containing `=` — fails the
whole layer, which at boot means recovery mode.

**registryd does not receive this layer.** The exemption is a trust
rule, not an availability one. Write access to `EnvVars\` is equivalent
to compromising every service peinit starts: `LD_PRELOAD`,
`LD_LIBRARY_PATH` and their relatives are not filtered, because the
key's Security Descriptor is meant to be the control boundary. A key
that could inject into the daemon that enforces who may write it would
make that boundary self-referential.

The exemption is narrow, and matches on two things at once: the job's
resolved identity is `SYSTEM` and its service name is `registryd`. A
non-platform service that happens to be called `registryd` receives the
ordinary layering. It matches on the *job*, so a hook of registryd's
running under a non-SYSTEM `HookIdentity` would receive the layer; and
it matches the resolved identity string, so a definition naming
`S-1-5-18` literally rather than `SYSTEM` would not be exempt.

registryd is launched in Phase 1, before `EnvVars` has been read at all,
so the exemption is only observable on a restart.

## Layer 3: the service's own Environment

The definition's `Environment` entries, overriding both layers below.

## Layer 4: protocol variables

`NOTIFY_SOCKET`, always. `LISTEN_FDS` and `LISTEN_FDNAMES`, only when
descriptors are being injected from the fd store.

These have the highest precedence and are inserted after both
configurable layers, so a service cannot override `NOTIFY_SOCKET` and
break its own notification protocol. The guard is insertion order rather
than a reserved-name check, which means the two fd-store variables are
protected only when they are actually being set — with no descriptors to
inject they are not inserted, and a value from either configurable layer
reaches the child unchanged.

`LISTEN_PID`, which a conforming `sd_listen_fds` implementation checks
against its own PID before trusting `LISTEN_FDS`, is not set.

## What peinit does not set

Not `HOME`, `USER`, `LOGNAME`, `SHELL` or `TERM`. Peios identity is a
KACS token — a SID — rather than a passwd entry, so there is no
canonical home directory or login shell to populate. A service that
needs one supplies it through `EnvVars\` or its own `Environment`.

## Hooks and probes

Hooks, health checks and reload commands are built through the same
path, so they receive the identical environment: the same layers, the
same `NOTIFY_SOCKET`, and the service's `WorkingDirectory`,
`LimitNOFILE`, `LimitCORE` and `RequiredPrivileges`. They never receive
`LISTEN_FDS` — stored descriptors go to the main process only.

## When changes apply

The global layer is a snapshot refreshed at boot and on reload-config,
and both it and the per-service `Environment` take effect at a service's
next start. Neither is applied to a running process.

> [!NOTE]
> Write access to `Machine\System\Init\EnvVars\` is equivalent to
> compromising every service on the system. peinit does not filter
> variable names, consistent with the registry's write-authority threat
> model — the key's descriptor is the boundary. The recommended default
> is SYSTEM full control and Administrators read-only.
