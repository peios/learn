---
title: Command Line
description: loregd is configured entirely by its argument vector — the hive declarations it takes, and how they are validated.
---

loregd is configured entirely by its argument vector. It takes one or
more hive declarations, each naming a hive and the SQLite database file
that backs it:

```
loregd <HiveName>=<DatabasePath> [<HiveName>=<DatabasePath> ...]
```

For example:

```
loregd Machine=/var/state/registry/machine.regdb Users=/var/state/registry/users.regdb
loregd Machine=/var/state/registry/machine.regdb Users=/var/state/registry/users.regdb Roles=/var/state/registry/roles.regdb
```

Each argument is split at its **first** `=`, so a database path may
itself contain `=`. Every declared hive is registered with the kernel at
startup (§2.2).

## Argument validation

loregd rejects the invocation and exits with a non-zero status if any of
the following hold:

| Condition | Reason |
|---|---|
| No hive arguments at all | At least one hive is required. |
| An argument with no `=` | Not a hive declaration. |
| An empty hive name or empty path | Neither is meaningful. |
| A relative database path | Paths are required to be absolute. |
| A hive name containing `\`, `/`, or NUL | These are path separators and terminators in the registry namespace. |
| The hive name `CurrentUser`, in any case | Reserved by the kernel as a per-token alias; no source may claim it. |
| Two declarations of the same hive name | Duplicates are detected on the **folded** name, so `Machine` and `MACHINE` collide. |

Hive-name comparison is case-insensitive throughout — for duplicate
detection here, and for routing requests later — but the case as written
on the command line is preserved and is what loregd presents to the
kernel when it registers.

## Configuration

loregd has no configuration file and reads no configuration from the
registry. This is deliberate: loregd *is* the configuration store, and a
store that had to read its own configuration in order to start could not
start.

Everything about how it behaves comes from three places: the command-line
arguments above, the contents of the SQLite databases they name, and
compiled-in constants (§4.1).

`NOTIFY_SOCKET` is the one environment variable loregd consults, and it
carries no behavioural setting. When it is set, loregd treats it as a
service-manager readiness socket: once the hives are registered and the
request loop is about to begin, it connects and sends `READY=1`. When it
is unset, the step is skipped.

loregd also opens `/dev/console` for writing at startup and, if that
succeeds, redirects its own diagnostic log there. This is what makes
loregd's failures visible during early boot, before any log daemon
exists.
