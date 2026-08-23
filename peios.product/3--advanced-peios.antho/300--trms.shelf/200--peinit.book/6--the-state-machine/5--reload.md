---
title: Reload
description: Telling a service to re-read its configuration without restarting — choosing the signal or command path, auto-detection, and interruptions.
---

Reload tells a service to re-read its configuration without restarting.
peinit issues the reload, moves the service to Reloading, and resolves
it one of three ways.

A failed reload never takes a running service out of Active. And reload
never gets stuck: every path has a timeout.

## Choosing a path

`ExecReload` absent means SIGHUP to the main process. A `signal:<NAME>`
value means that signal instead. Anything else is a command, forked into
the service's `hooks/` sub-cgroup under the service's **own** identity —
never peinit's token, and `HookIdentity` does not apply.

## The signal path

There is no command exit to observe, so completion is inferred from the
main process's own notifications.

```
start the detection window (2 seconds)

on READY=1, at any time:
    -> Active, "confirmed"

on RELOADING=1 within the window:
    cancel the window
    start the extended wait (StartTimeout)

on the window expiring with no RELOADING=1:
    -> Active, "advisory"

on the extended wait expiring with no READY=1:
    -> Active, "advisory"
```

The two-second window is a constant and is not configurable through the
registry. It is bounded from above by the operation's own deadline, so a
service whose `StartTimeout` is under two seconds gets the shorter of
the two.

The extended-wait expiry means the service announced a reload and never
finished one. The outcome is carried in the operation's result, which a
`wait=true` caller receives; a reload issued without waiting — the
default — resolves silently.

## The command path

The command's exit gates failure; the main process's `READY=1` gates
confirmation.

```
on the command exiting non-zero:
    -> Active, "failed"

on the command exceeding StartTimeout:
    SIGKILL the hooks/ sub-cgroup, taking its descendants
    -> Active, "failed"

on the command exiting zero:
    -> Active, "confirmed" if the main process sent READY=1 during the
       reload, otherwise "advisory"
```

## Auto-detection

The protocol needs no per-service configuration. A service that
implements the notification handshake — `RELOADING=1` then `READY=1` —
gets real lifecycle tracking. One that does not gets a brief Reloading
state that resolves itself when the detection window expires. Neither
has to declare which it is.

## Interruptions

**The main process crashes while Reloading.** That is a `ProcessCrash`,
and the restart policy is consulted: Reloading to Backoff if a restart
is allowed and the budget holds, Reloading to Failed otherwise. Both
reload timers are cancelled and any in-flight reload command is killed.

This is a different event from an external reload *command* exiting
non-zero, which is the "failed" outcome above and leaves the main
process — and the service — running.

**A stop arrives while Reloading.** peinit cancels the reload
immediately: it drops the reload deadlines, kills any reload command's
cgroup, and sends SIGTERM in the same turn, without waiting out the
window or the extended wait. The service goes to Stopping and the reload
operation is aborted.
