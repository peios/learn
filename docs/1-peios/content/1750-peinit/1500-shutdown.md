---
title: Shutdown
type: concept
description: "Shutdown is boot in reverse: peinit stops services in reverse dependency order, escalating from SIGTERM to SIGKILL, bounded by a global timeout, then unmounts, syncs, and powers off. This page covers the three ways shutdown is triggered, the graceful sequence, forced shutdown, how signals are handled, and the STOPPING=1 courtesy notification."
related:
  - peios/peinit/dependencies
  - peios/peinit/supervision
  - peios/peinit/the-service-lifecycle
  - peios/peinit/boot-and-boot-modes
---

Shutdown is [boot](~peios/peinit/boot-and-boot-modes) run in reverse. peinit stops services in **reverse [dependency](~peios/peinit/dependencies) order** — dependents before the things they depend on — escalating from a polite SIGTERM to a forced SIGKILL, all bounded by a global timeout, and then unmounts, syncs, and performs the final power action. This page covers how it is triggered and how it runs.

## How shutdown is triggered

There are three paths into shutdown, and they are not equal — two are graceful, one is not.

**A control command.** An administrator with `SYSTEM_SHUTDOWN` runs `peiosctl shutdown <type>`:

| Type | Result |
|---|---|
| `poweroff` | Stop everything, unmount, power off. |
| `reboot` | Stop everything, unmount, reboot. |
| `halt` | Stop everything, unmount, halt (CPU stopped, power stays on). |

**Signals.** As PID 1, peinit treats two signals as shutdown requests:

| Signal | Meaning |
|---|---|
| SIGINT | Reboot — the kernel sends this on Ctrl-Alt-Del. |
| SIGTERM | Poweroff. |

**A Critical service failure** — the ungraceful path. When an `ErrorControl=Critical` service exhausts its [restart budget](~peios/peinit/supervision), peinit **syncs and reboots immediately**. There is no service-stop ordering: the system is in an undefined state and the fastest route to a known one is a reboot. This is what feeds the [boot-attempt counter](~peios/peinit/boot-and-boot-modes), and a Critical service that fails identically every boot becomes a reboot loop that the counter eventually breaks by escalating to Recovery.

## The graceful sequence

For a `poweroff`, `reboot`, or `halt`, peinit runs an ordered sequence:

1. **Enter the shutdown state.** A flag is set, and while it holds: **no new services may start**, timer triggers are disarmed, and new control commands are rejected with `INVALID_STATE` — *except* `status` queries, which keep working so you can watch progress.
2. **Suspend Critical-failure semantics.** If a Critical service fails *during* shutdown, it is logged but does **not** trigger a reboot — the system is already going down, and rebooting would loop.
3. **Clear Completed services.** Oneshot services sitting in [Completed](~peios/peinit/the-service-lifecycle) (with `RemainAfterExit`) have no process; peinit moves them to Inactive so their dependents can be stopped cleanly.
4. **Stop services in reverse dependency order**, in waves. Each graceful-stop-eligible service (those in Active or Reloading) gets SIGTERM and `StopTimeout` seconds to exit; if it does not, peinit SIGKILLs its whole cgroup. A service is never stopped until everything that `Requires` or `BindsTo` it has already stopped. Services that are Starting are not stopped gracefully — their startup is cancelled and the cgroup SIGKILLed.
5. **Enforce the global timeout.** The whole sequence is bounded by `ShutdownTimeout` (default 90 s). When it expires, all remaining services are SIGKILLed; any whose cgroups do not empty become [Abandoned](~peios/peinit/the-service-lifecycle) (leaked), and shutdown continues regardless.
6. **Unmount filesystems.** peinit unmounts the virtual filesystems it mounted in Phase 1 (`/run`, `/dev/shm`, `/dev/pts`, `/sys/fs/cgroup`), leaves `/dev`, `/sys`, `/proc` for the kernel, and remounts the root read-only.
7. **Sync and finish.** `sync()` to flush pending writes, then the final action — power off, reboot, or halt.

The reverse ordering falls straight out of the [dependency graph](~peios/peinit/dependencies); there is no separate stop-order configuration. The last services to stop are the TCB daemons everything rests on — `eventd`, then `authd`, then `lpsd`, then `registryd` dead last, mirroring its position as the first ever started.

## STOPPING=1 and timeout extension

A service that begins shutting down on its own — say, in response to an internal error — can tell peinit by sending `STOPPING=1` via [sd_notify](~peios/peinit/service-types). peinit acknowledges it and, importantly, **stops sending SIGTERM** to that service: it is already on its way down, and a redundant signal could interfere.

`STOPPING=1` is a courtesy, **not** a timeout extension. The `StopTimeout` keeps running; if the process has not exited when it expires, peinit escalates to SIGKILL regardless. A service that genuinely needs longer must say so with `EXTEND_TIMEOUT_USEC` (see [Keeping services running](~peios/peinit/supervision)) — and during shutdown those extensions are capped not only by the per-service `StopTimeout` × 4 but also by the remaining global `ShutdownTimeout`, whichever is smaller.

## Forced shutdown

When something is wedged and you need the machine down *now*, **repeated SIGINT** forces it: three Ctrl-Alt-Del presses within five seconds skip the graceful sequence entirely — SIGKILL everything, sync, reboot. It is the escape hatch for a graceful shutdown that is itself stuck behind an unresponsive service.

## Shutdown during boot

A shutdown requested while peinit is still in Phase 2 boot takes effect immediately: services still Starting are SIGKILLed (they never reached Active, so there is nothing to stop gracefully), services that did reach Active are stopped per the normal sequence, and the boot is abandoned.

## How peinit handles signals

peinit handles **all** signals through a `signalfd` read from its event loop — every signal is blocked and read as data, so there are no async signal handlers and no async-safety hazards. PID 1 cannot be killed by any signal; the kernel protects it.

| Signal | Behaviour |
|---|---|
| SIGCHLD | Reap children; match exits to services and jobs. Also reaps orphaned processes the system reparented to PID 1. |
| SIGINT | Reboot request. Repeated within the window → forced reboot. |
| SIGTERM | Poweroff request. |
| SIGHUP | Ignored — PID 1 has no controlling terminal. |
| SIGPIPE | Ignored — a broken control-socket pipe must never crash PID 1. |

All other signals are ignored.

> [!NOTE]
> Reaping orphans matters: when any process anywhere on the system dies leaving children, those children are reparented to PID 1. peinit reaps them so they do not accumulate as zombies — even though they were never its services. This is part of the job of being PID 1, distinct from supervising services.

## Where to start

To understand the reverse ordering and which relationships gate it, read [Dependencies and ordering](~peios/peinit/dependencies).

To understand the Critical-failure path that bypasses graceful shutdown, read [Keeping services running](~peios/peinit/supervision).

For the boot side of the lifecycle and the reboot/recovery escalation, read [Boot and boot modes](~peios/peinit/boot-and-boot-modes).
