---
title: Resource Limits
type: concept
description: Per-process and system-wide resource limits for the FD subsystem and notification subsystems — RLIMIT_NOFILE, file-max, and the inotify and fanotify registry knobs.
related:
  - peios/file-io/overview-and-design
  - peios/file-io/notifications
---

The FD subsystem and notification subsystems each carry resource ceilings that bound their footprint on the system. Some are per-process; others are system-wide. This page documents each, the Peios default, and the configuration interface.

## Per-process FD limit (RLIMIT_NOFILE)

The maximum number of open fds a process may hold is `RLIMIT_NOFILE`, set via `setrlimit(RLIMIT_NOFILE, ...)`. The hard limit cannot be raised beyond a system-wide cap; the soft limit can be raised up to the hard limit.

Peios defaults match Linux conventions:

| Limit | Default soft | Default hard |
|---|---|---|
| `RLIMIT_NOFILE` (interactive sessions) | 1024 | 524288 |
| `RLIMIT_NOFILE` (services) | 65536 | 524288 |

Service principals running through the standard service infrastructure get the higher soft default. Interactive sessions inherit the lower default. Either can be raised via standard `prlimit` / `ulimit` mechanisms (subject to the hard cap, which is changed only by `SeIncreaseQuotaPrivilege`).

## System-wide FD limit (file-max)

The kernel-wide cap on open files across all processes is `/proc/sys/fs/file-max`. The current count is `/proc/sys/fs/file-nr` (returns three numbers: allocated handles, free handles, and the maximum).

| Knob | Effect | Default |
|---|---|---|
| `\System\Filesystem\FileMax` | Maximum total open file descriptions across all processes | Computed at boot (~10% of available memory expressed as fd count) |

The default is computed dynamically — the kernel picks a value scaled to system memory. Set the registry value to override. Lowering it below the current usage will cause new opens to fail with `ENFILE` until usage drops; raising it has no immediate cost.

## inotify resource limits

inotify accounts watches and queue depth per user. The defaults are conservative — applications that watch many paths (file-syncing tools, IDE indexers, build watchers) routinely hit them.

| Knob | Effect | Default |
|---|---|---|
| `\System\Filesystem\InotifyMaxUserWatches` | Maximum total watches (across all instances) per user | 8192 |
| `\System\Filesystem\InotifyMaxUserInstances` | Maximum inotify instances (`inotify_init` calls) per user | 128 |
| `\System\Filesystem\InotifyMaxQueuedEvents` | Maximum events queued per inotify fd before older events are dropped (with `IN_Q_OVERFLOW`) | 16384 |

Defaults match Linux. Operators running large file-syncing workloads (e.g. large source trees with file-watching IDEs) typically raise `InotifyMaxUserWatches` to 524288 or higher.

## fanotify resource limits

fanotify has analogous per-user limits.

| Knob | Effect | Default |
|---|---|---|
| `\System\Filesystem\FanotifyMaxUserMarks` | Maximum total marks per user | 8192 |
| `\System\Filesystem\FanotifyMaxUserInstances` | Maximum fanotify instances per user | 128 |
| `\System\Filesystem\FanotifyMaxQueuedEvents` | Maximum events queued per fanotify fd | 16384 |

Holders of `SeFilterFileSystemPrivilege` may set `FAN_UNLIMITED_QUEUE` and `FAN_UNLIMITED_MARKS` at fanotify_init time, bypassing these limits. Unprivileged callers are bound by the configured values.

## fanotify permission-event watchdog

The fanotify permission-event watchdog (kernel 6.18+) detects unresponsive permission-event listeners. If a listener doesn't respond within the configured timeout, the kernel logs a diagnostic and proceeds with the operation rather than blocking indefinitely.

| Knob | Effect | Default |
|---|---|---|
| `\System\Filesystem\FanotifyPermEventWatchdogMs` | Timeout in milliseconds before an unresponsive permission-event listener is treated as failed | 30000 (30 seconds) |
| `\System\Filesystem\FanotifyPermEventOnTimeout` | Action when the watchdog fires: `allow` (proceed with the operation) or `deny` (fail the operation) | `allow` |

The default `allow` posture matches Linux semantics — a hung permission-event listener should not lock up the entire system. Operators with stricter requirements (e.g. critical security policy enforcement) may set the timeout action to `deny`, but this is risky: a crashed antivirus daemon would then deny all file access.

## DoS posture

The notification-subsystem limits are a real DoS vector. Each watched path costs kernel memory; a process that creates millions of inotify watches can exhaust kernel memory or crowd out legitimate users. The per-user limits are the primary defense — a single compromised user account cannot exhaust system-wide resources.

For environments where DoS protection is critical:

- Lower per-user defaults via the registry knobs above.
- Use cgroup memory limits to bound the kernel memory attributable to a workload.
- For multi-tenant systems, consider per-tenant limit overrides via the registry layered configuration.

For environments where capability matters more than DoS protection (build farms, IDE-heavy developer machines), raise the limits as needed.

## File lease timeout

The kernel's file-lease break timeout (the time a lease holder has to respond before the kernel forcibly breaks the lease) is configurable.

| Knob | Effect | Default |
|---|---|---|
| `\System\Filesystem\LeaseBreakTimeSeconds` | Maximum time a lease holder has to respond to a lease break before the kernel proceeds | 45 |

Samba relies on this timeout for cache coherency. The default matches Linux. Raising it gives lease holders more time to flush state but makes conflicting opens take longer; lowering it speeds up conflicting opens but risks lease holders timing out on legitimate work.

## See also

- [Notifications](notifications) — inotify, fanotify, dnotify, and the permission-event subsystem.
- [Locking and leases](locking-and-leases) — file leases and the lease-break protocol.
- [Overview and design](overview-and-design) — the FD subsystem at a glance.
