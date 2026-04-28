---
title: Pressure Stall Information
type: concept
description: Pressure Stall Information (PSI) is the kernel's metric for how much time tasks spent stalled waiting for CPU, memory, IO, or IRQ resources. PSI is exposed both per-cgroup and system-wide, and supports threshold-triggered notifications for autoscaling and oncall alerting.
related:
  - peios/resource-management/understanding-cgroups
  - peios/resource-management/controller-reference
  - peios/eventd/eventd-overview
---

**Pressure Stall Information** (PSI) measures how much of an interval the system or a cgroup was unable to make progress because it was waiting on a contended resource. Unlike utilization metrics — which tell you how busy a resource was — PSI tells you whether tasks were *suffering* because of that busyness. A CPU at 100% utilization is not necessarily a problem; a CPU at 100% utilization where every task is waiting on the runqueue most of the time is.

PSI is the autoscaling and oncall primitive Peios exposes for resource health. Modern Linux applications use PSI as the trigger signal for "scale up" / "the system is in trouble" decisions; Peios preserves the same surface and adds standard KACS access control on the pressure files.

## The two metrics: `some` and `full`

Each pressure measurement has two components:

- **`some`** — the fraction of time *at least one* runnable task was stalled waiting for the resource. This catches partial pressure: even if the system is mostly making progress, if one important task is starved, `some` rises.
- **`full`** — the fraction of time *all* non-idle tasks were stalled waiting for the resource. This catches complete pressure: nothing is making progress because everyone is waiting.

`full` is necessarily ≤ `some`. A `some` of 50% with `full` of 0% means half the time there was contention but the system was still making progress on something; a `full` of 50% means half the time the system was making no progress whatsoever.

For CPU pressure, `full` is meaningful only at the cgroup level (a single CPU can't have "all tasks stalled" system-wide — there's always something running on idle CPUs).

## Pressure file format

A pressure file (`cpu.pressure`, `memory.pressure`, etc.) contains two lines, one for `some` and one for `full`. Each line has windowed averages and a cumulative total:

```
$ cat /sys/fs/cgroup/services/jellyfin/cpu.pressure
some avg10=1.43 avg60=0.87 avg300=0.42 total=18374923
full avg10=0.21 avg60=0.10 avg300=0.05 total=2374891
```

| Field | Meaning |
|---|---|
| `avg10` | Percent of the last 10 seconds spent stalled. |
| `avg60` | Percent of the last 60 seconds. |
| `avg300` | Percent of the last 5 minutes. |
| `total` | Cumulative microseconds spent stalled since the cgroup was created. |

Reading the file is `FILE_READ_DATA` on the file. The cgroup's DACL controls who can read pressure metrics — typically the cgroup owner and any monitoring principals granted explicit access.

## The four resource categories

Each cgroup exposes pressure files for the resources tracked.

| File | What it measures |
|---|---|
| `cpu.pressure` | Time tasks waited to run on a CPU (runqueue stalls). |
| `memory.pressure` | Time tasks waited for memory — page reclaim, page-in from swap, allocation failures. |
| `io.pressure` | Time tasks waited for block IO. |
| `irq.pressure` | Time soft IRQ handlers were delayed by other soft IRQs. (Newer kernels; not all configurations include this.) |

The system-wide aggregate of each is exposed via `/proc/pressure/`:

| File | Scope |
|---|---|
| `/proc/pressure/cpu` | System-wide CPU pressure. |
| `/proc/pressure/memory` | System-wide memory pressure. |
| `/proc/pressure/io` | System-wide IO pressure. |
| `/proc/pressure/irq` | System-wide IRQ pressure (where supported). |

System-wide pressure files have their own SDs — typically readable by Administrators and monitoring service principals. The default DACL is configured in the registry under `\System\Audit\PSI\SystemSDs` and applied at boot.

## Disabling per-cgroup PSI

PSI accounting carries a small per-task overhead. For workloads that don't care about cgroup-level pressure (fire-and-forget batch jobs, short-lived test cgroups), the overhead can be elided by writing `0` to `cgroup.pressure`:

```bash
$ echo 0 > /sys/fs/cgroup/test-jobs/cgroup.pressure
```

The cgroup's pressure files become unreadable (return `-EOPNOTSUPP` on read). System-wide PSI is unaffected. Re-enable with `echo 1`.

## PSI triggers — threshold-based notification

For autoscaling and alerting, polling pressure files is wasteful. PSI supports **triggers**: kernel-side threshold detection that wakes a userspace consumer when pressure exceeds a configured level.

### Setting up a trigger

A trigger is configured by writing to a pressure file in a special format:

```
<some|full> <stall_target_us> <window_us>
```

For example, to be notified when memory pressure's `some` metric stalls for at least 150ms in any 1-second window:

```c
int fd = open("/sys/fs/cgroup/services/jellyfin/memory.pressure", O_RDWR | O_NONBLOCK);
write(fd, "some 150000 1000000", 19);
```

The kernel maintains the trigger as long as the file descriptor is open. When the threshold is crossed, the fd becomes readable for `poll()`/`epoll()`. The reader then re-reads the pressure file to see current values.

| Argument | Meaning |
|---|---|
| `some` or `full` | Which metric to watch. |
| `stall_target_us` | Microseconds of stall within the window that triggers notification. |
| `window_us` | The sliding window size (typically 500ms-10s). |

Closing the fd removes the trigger.

### Polling pattern

```c
int fd = open("memory.pressure", O_RDWR | O_NONBLOCK);
write(fd, "some 200000 2000000", 19);  // 200ms stall in 2s window

struct pollfd pfd = { .fd = fd, .events = POLLPRI };
while (1) {
    int n = poll(&pfd, 1, -1);
    if (n > 0 && (pfd.revents & POLLPRI)) {
        // Threshold crossed — read current pressure
        char buf[256];
        lseek(fd, 0, SEEK_SET);
        read(fd, buf, sizeof(buf));
        // ... handle the event
    }
}
```

`POLLPRI` (not `POLLIN`) is the right event flag — PSI uses priority-band notification to distinguish trigger fires from regular readability.

### Trigger limits

The number of active triggers per cgroup is bounded (`/proc/sys/kernel/psi_max_triggers`, default 256). Triggers cost a small amount of memory each; configurations with many cgroups and many triggers per cgroup should configure this limit accordingly.

Setting up a trigger requires `FILE_WRITE_DATA` on the pressure file — the same right needed to disable PSI via `cgroup.pressure`.

## Common patterns

**Autoscaling on memory pressure.** Watch `memory.pressure` `some avg60` on the workload's cgroup; if `avg60` exceeds (say) 10% sustained, add more memory or scale the workload horizontally.

**Oncall alerting on system-wide IO pressure.** Watch `/proc/pressure/io` `full avg300`; sustained `full` IO pressure means the storage subsystem is saturated and likely impacting every workload on the host.

**Backpressure for batch workloads.** A batch system can use a PSI trigger on memory `some` with a tight threshold to know when the host is stressed, and pause batch dispatch until pressure drops.

**Per-tenant SLA tracking.** Each tenant's cgroup exposes its own pressure files; the per-tenant pressure trace is durable evidence of whether SLAs were met for that tenant during a window.

## Audit and access control

Pressure files are filesystem-style securable objects. Audit on PSI reads / trigger configurations is the standard cgroupfs SACL audit path — there is no separate PSI audit channel.

Reading PSI is privacy-relevant in multi-tenant deployments — pressure data can reveal patterns about a tenant's workload (heavy IO at 3am, memory pressure during user-traffic peaks). Default DACLs grant pressure read access to the cgroup owner and explicit monitoring principals; cross-tenant pressure visibility requires an explicit grant.

## Relationship to eventd

Native Peios applications can subscribe to PSI events through [eventd](../eventd/eventd-overview) rather than configuring triggers directly on pressure files. eventd handles the trigger lifecycle (open the fd, write the trigger, poll, fan out the event) and delivers PSI threshold crossings as event records to subscribers. This is the preferred pattern for Peios-native monitoring; the direct trigger API exists for unmodified Linux applications that already speak it.
