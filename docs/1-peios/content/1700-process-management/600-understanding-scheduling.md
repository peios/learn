---
title: Understanding Scheduling
type: concept
description: How the kernel decides which thread runs when — the scheduling classes Peios offers, when to use each, and the privileges required to elevate scheduling parameters.
related:
  - peios/process-management/understanding-the-thread-model
  - peios/process-management/cpu-affinity-and-isolation
---

A computer has a small number of CPU cores and a large number of threads competing for them. The kernel's **scheduler** decides, every few microseconds, which threads run on which cores and for how long. The decision rule depends on the **scheduling class** each thread belongs to — a small set of named policies that express different goals: throughput-with-fairness, real-time responsiveness, missable-but-CPU-hungry batch work, and so on.

This page covers what classes Peios offers, what each is for, and what authority is needed to change them.

## The classes at a glance

Every thread belongs to exactly one scheduling class at any time. The kernel evaluates classes in priority order: any thread in a higher-priority class runs before any thread in a lower-priority one is even considered.

| Class | Policy names | Use case |
|---|---|---|
| **Stop** | (kernel only) | Highest priority. Reserved for kernel-internal stop-machine operations. Not user-accessible. |
| **Deadline** | `SCHED_DEADLINE` | Threads with strict timing requirements expressed as runtime within a deadline within a period. The scheduler uses earliest-deadline-first ordering. |
| **Real-time** | `SCHED_FIFO`, `SCHED_RR` | Threads that must run when ready, regardless of fairness. Priorities 1–99. |
| **Normal** | `SCHED_OTHER` (default), `SCHED_BATCH`, `SCHED_IDLE` | The default time-sharing class — fairness across competing workloads using virtual-runtime accounting. |
| **Idle** | (kernel-internal) | The per-CPU idle thread. Runs when nothing else is runnable. |

A thread in `SCHED_FIFO` will preempt any `SCHED_OTHER` thread regardless of nice values; a `SCHED_DEADLINE` thread will preempt any `SCHED_FIFO` thread. The class is the first dimension of priority; values within a class are the second.

## The Normal class

`SCHED_OTHER` (also spelled `SCHED_NORMAL`) is the default class. Every newly-created thread starts here unless something explicitly says otherwise. The Normal class implements **fair time-sharing** — over time, runnable threads get CPU time roughly in proportion to their relative weights, where weight is derived from the nice value.

The implementation is the kernel's **EEVDF** scheduler (since kernel 6.6) — Earliest Eligible Virtual Deadline First. EEVDF replaced the earlier CFS (Completely Fair Scheduler). User-visible behaviour is similar: nice values control relative share, and the scheduler approximates "every runnable thread should get its fair slice over time." The internals are different but applications written for CFS continue to work without changes under EEVDF.

### Nice values

Nice is a per-thread integer in the range **−20 to +19** that scales the share of CPU a Normal-class thread receives:

| Nice | Effect |
|---|---|
| **−20** | Maximum share. Roughly 8× the share of a nice-0 thread. |
| **0** | Default. |
| **+19** | Minimum share. Roughly 1/15 the share of a nice-0 thread. |

A thread can lower its own priority freely (set nice to a higher value than current) — there is no privilege check for being polite. **Raising priority** (setting nice lower than current, including ever returning to a lower nice if it was previously raised) requires `SeIncreaseBasePriorityPrivilege`. The same privilege gates real-time elevation; see below.

`nice()`, `setpriority()`, and `getpriority()` are the syscalls. `setpriority()` accepts a thread, a process group, or a user as the target.

### `SCHED_BATCH`

`SCHED_BATCH` is a Normal-class variant that hints to the scheduler "I am CPU-bound and don't care about responsiveness." The scheduler reduces the rate at which the thread is preempted on wake-up, which improves throughput slightly at the cost of latency. Useful for compute jobs that don't interact with users.

`SCHED_BATCH` does not change the nice-based share; it only changes preemption behaviour. Setting it requires no special privilege — it is a self-imposed quality-of-service hint.

### `SCHED_IDLE`

`SCHED_IDLE` is the lowest-priority Normal-class variant. It runs only when nothing in `SCHED_OTHER` or `SCHED_BATCH` is runnable. Use it for background work that should never compete with anything important — file indexing, opportunistic cache warming, optional housekeeping.

`SCHED_IDLE` does not require privilege to enter. It cannot be combined with elevated nice — its share is fixed below the entire Normal-class range.

## Real-time classes

When a workload has hard timing requirements — audio processing, control loops, network packet handling at sub-millisecond latency — fairness is the wrong goal. Real-time scheduling abandons fairness in favour of "this thread runs the moment it is ready."

### `SCHED_FIFO`

`SCHED_FIFO` runs at a fixed real-time priority (1–99) and continues running until it voluntarily yields, blocks, or is preempted by a higher-priority thread. There is no time-slicing within a priority level. Two `SCHED_FIFO` threads at priority 50 will see one of them run continuously to completion; the other waits until the first yields.

This is the scheduling model audio interrupt handlers, sensor pollers, and packet-pumping threads usually want.

### `SCHED_RR`

`SCHED_RR` is `SCHED_FIFO` with **round-robin time-slicing within a priority level**. When two `SCHED_RR` threads at the same priority are both runnable, the scheduler rotates them on a fixed quantum (`sched_rr_get_interval()` returns the quantum). Higher-priority RR or FIFO threads still preempt them; lower-priority threads still wait.

`SCHED_RR` is useful when several equally-urgent threads share a priority level and no one of them should monopolise the CPU.

### `SCHED_DEADLINE`

`SCHED_DEADLINE` is the most expressive real-time policy. A thread declares three numbers:

- **runtime** — how much CPU time it needs, per period
- **deadline** — by when, relative to period start, it must finish
- **period** — the cadence at which it runs

The kernel admits the thread only if it can guarantee these numbers will be met given the existing deadline workload. If admitted, the scheduler runs the thread no later than its deadline using earliest-deadline-first ordering. If the kernel cannot guarantee admission, `sched_setattr()` fails — the thread is not silently degraded into a best-effort job.

Use `SCHED_DEADLINE` when you have well-characterised periodic work and need analytical timing guarantees, not just "high priority."

### Privilege

Switching a thread to any real-time class — including `SCHED_DEADLINE` — requires **`SeIncreaseBasePriorityPrivilege`**. The same privilege gates raising nice into negative values, raising real-time priority within the class, and switching between real-time policies. There is no separate "real-time privilege"; real-time is conceptually "elevating priority" and the spec maps it to the same gate as nice elevation, the same way Windows uses `SeIncreaseBasePriorityPrivilege` for `REALTIME_PRIORITY_CLASS` and Linux uses `CAP_SYS_NICE` for both.

### Layered defences

Real-time threads can starve everything if misbehaving — including the kernel itself. Peios honours the substrate's per-process rate-limit defences:

| Mechanism | What it caps |
|---|---|
| `RLIMIT_RTPRIO` | The maximum real-time priority a process can request without holding `SeIncreaseBasePriorityPrivilege`. Raising this rlimit grants narrow real-time capability without granting full priority elevation. |
| `RLIMIT_RTTIME` | The CPU time a real-time thread can consume in a single block before being downgraded to `SCHED_OTHER`. Defends against runaway tight loops. |
| `kernel.sched_rt_runtime_us` / `kernel.sched_rt_period_us` | System-wide cap on aggregate real-time CPU consumption per period. The kernel reserves the remainder for non-RT work. |

The system-wide values are sysctls, configured under `\System\Scheduling\` in the registry and applied by `ksyncd`. The per-process rlimits are set with `setrlimit()` or inherited from a supervisor.

## Setting scheduling parameters

Three syscall pairs cover scheduling-parameter manipulation:

| Syscall | Purpose |
|---|---|
| `sched_setscheduler()` / `sched_getscheduler()` | Set or get the scheduling class. |
| `sched_setparam()` / `sched_getparam()` | Set or get the priority within the current class (real-time priority; ignored for normal classes). |
| `sched_setattr()` / `sched_getattr()` | Extended interface taking a `struct sched_attr` covering class, priority, deadline parameters, latency-nice, and util-clamp values in one call. Required for `SCHED_DEADLINE`. |

`sched_setattr()` is the modern interface; new code should prefer it. The older calls remain functional for compatibility.

`sched_yield()` is unchanged from substrate — a thread voluntarily relinquishes the CPU. For real-time threads it has well-defined semantics (yield to others at the same priority); for normal threads it's a hint to the scheduler that other work might be runnable.

`sched_get_priority_min()` and `sched_get_priority_max()` return the legal priority range for a given class.

## Inheritance and `SCHED_RESET_ON_FORK`

Scheduling parameters are part of a thread's state. Like other thread state, they survive `clone()` (inherited by both threads and children) and survive `exec()` (the new program image runs under whatever scheduling parameters the thread had).

For real-time work this can be a hazard: a privileged service running `SCHED_FIFO` that forks children will have those children running at `SCHED_FIFO` too, even if the children don't need it. `SCHED_RESET_ON_FORK` is a flag attached to the parent's scheduling attributes that, when set, causes children created by `clone()` (without `CLONE_THREAD`) to revert to `SCHED_OTHER` at default nice. Real-time supervisors should set it on themselves so non-RT children don't inadvertently inherit RT scheduling.

`SCHED_RESET_ON_FORK` does not affect the parent itself, only its future children. `clone()` with `CLONE_THREAD` (creating threads in the same process) is unaffected — threads always share the process's primary token and scheduling attributes within their thread group.

## Latency hints and utilisation clamping

Two newer per-thread hints exist on top of the class system:

- **`sched_latency_nice`** — a hint to the Normal-class scheduler about preference for low latency vs throughput. Lower values prefer low latency (faster preemption on wake-up); higher values prefer throughput. Applies only to Normal-class threads.
- **`sched_util_min`** / **`sched_util_max`** — utilisation clamping. Tells the cpufreq governor "treat this thread as needing at least X% / at most Y% of CPU capacity." Used to coax the governor into scaling frequency more aggressively for latency-sensitive work, or to cap a hot loop.

Both are set via `sched_setattr()`. Setting either to a non-default value requires `SeIncreaseBasePriorityPrivilege`.

## Core scheduling and SMT co-scheduling

Modern x86 CPUs implement simultaneous multithreading (SMT) — two logical CPUs share the execution resources of a single physical core. Spectre-class side-channel attacks have shown that an untrusted thread on one SMT sibling can extract information from a sensitive thread on the other. The mainstream mitigation is **core scheduling** — the kernel guarantees that only threads belonging to the same trust domain run simultaneously on SMT-sibling CPUs.

Core scheduling is requested via `prctl(PR_SCHED_CORE, ...)`. A thread or process is assigned a **cookie**, an opaque identifier, and the kernel ensures that no SMT-sibling CPU runs a thread with a different cookie at the same time. Threads with the same cookie are co-schedulable; threads with different cookies are mutually exclusive on SMT siblings.

| Operation | Effect |
|---|---|
| `PR_SCHED_CORE_CREATE` | Create a new cookie for the calling thread or process. |
| `PR_SCHED_CORE_SHARE_FROM` | Adopt another thread's cookie (the calling thread joins the target's co-scheduling group). |
| `PR_SCHED_CORE_SHARE_TO` | Push the calling thread's cookie onto another thread. |
| `PR_SCHED_CORE_GET` | Read a thread's cookie. |

Setting a cookie on the calling thread requires no privilege. Setting a cookie on another process requires `PROCESS_QUERY_INFORMATION` on the target's process SD and is also subject to PIP dominance — a non-dominant caller cannot manipulate a Protected process's core-scheduling configuration. This is the same authority pattern used elsewhere when one process wants to manage another's properties: process SD for "may I touch this process at all," PIP for "may I cross this protection level."

Core scheduling is the recommended mitigation when running mutually-untrusting workloads on the same machine without disabling SMT entirely.

## Preemption model

The kernel's **preemption model** is the rule that decides when a running task can be involuntarily switched off the CPU. Linux exposes four named models, selected at kernel-build time:

| Model | Behaviour |
|---|---|
| `PREEMPT_NONE` | Voluntary preemption only at explicit `schedule()` points. Highest throughput; worst latency. Server-style. |
| `PREEMPT_VOLUNTARY` | Same as `PREEMPT_NONE` plus added preemption checkpoints. Better latency at modest throughput cost. |
| `PREEMPT_FULL` | Preempt anywhere not in a critical section. Desktop / interactive default. |
| `PREEMPT_RT` | Full real-time preemption. Almost everything is preemptible, including most kernel critical sections (replaced by mutexes). Required for hard real-time workloads. Mainline since 6.12. |

Like CPU isolation, the preemption model is **image-time configuration** — chosen when the kernel is compiled, not at runtime. The trade-off is throughput-vs-latency: an image targeting real-time work (audio, control loops, networking gateways) builds with `PREEMPT_RT`; an image targeting maximum compute throughput builds with `PREEMPT_NONE`. There is no runtime switch.

Peios provides reference images at multiple preemption levels; downstream image builders pick whichever matches their workload's requirements.

## Pressure stall information

Modern Linux exposes per-resource **Pressure Stall Information** (PSI) — files at `/proc/pressure/cpu`, `/proc/pressure/memory`, and `/proc/pressure/io` that report what fraction of recent time tasks were stalled waiting for the resource. Two metrics per file:

- `some` — fraction of time at least one runnable task was stalled
- `full` — fraction of time *all* runnable tasks were stalled (memory and io only)

Each metric is reported over three time windows: 10-second, 60-second, and 300-second moving averages.

PSI is the recommended observability surface for capacity planning and autoscaling decisions on Peios. It replaces older indicators like load average — load average conflates runnable, blocked, and uninterruptible-sleep tasks; PSI distinguishes them and reports actual contention. Per-cgroup PSI is also available under each cgroup's `cpu.pressure`, `memory.pressure`, `io.pressure` files, gated by the cgroup hierarchy's normal access controls.

Reading the global PSI files is unprivileged. Reading a cgroup's PSI is gated by the cgroup membership-management SD.

## Scheduler observability and tuning internals

A handful of additional substrate features appear in the inventory of completeness:

- **Autogroups (`CONFIG_SCHED_AUTOGROUP`).** Per-session automatic process grouping for the Normal class. When enabled, each interactive session is treated as a group and gets a fair share of CPU, preventing one user's heavy compute from starving another's interactive work. A kernel-build option Peios images may enable or disable depending on workload.
- **Energy-aware scheduling (EAS).** On heterogeneous-CPU hardware (big.LITTLE, P-core/E-core hybrids), EAS factors energy efficiency into placement decisions. Activates automatically when running on appropriate hardware; no user-facing API.
- **Load balancing.** The scheduler periodically rebalances runnable tasks across CPUs to keep them all busy. Substrate behaviour with no Peios-specific knobs beyond affinity (covered above) and isolation (covered in [CPU Affinity and Isolation](cpu-affinity-and-isolation)).
- **`/proc/schedstat`.** System-wide scheduler statistics — wakeup counts, balance counts, runtime distributions. Useful for tuning when investigating scheduler behaviour. Read access is unprivileged.
- **`/proc/[pid]/sched`.** Per-task scheduler debug information — virtual runtime, runqueue placement, and other internal counters. Read access is gated by the process SD (`PROCESS_QUERY_INFORMATION`) and by the PIP `/proc` default-deny rule for protected processes.

For day-to-day capacity decisions on Peios the recommended surface is PSI plus per-cgroup `cpu.stat`. The legacy `/proc/schedstat` and per-task `/proc/[pid]/sched` interfaces are retained for compatibility with existing Linux tooling.

## Where scheduling does not go

A few questions that look scheduling-shaped belong elsewhere:

- **CPU affinity** (which CPUs a thread can run on) is its own concept and lives in [CPU Affinity and Isolation](cpu-affinity-and-isolation).
- **CPU bandwidth limits for groups** (e.g. "this service tree gets at most 30% of one core") are part of the resource-control story in cgroup v2 and are covered alongside other resource limits in the resource-control area.
- **Process priority class as a process-wide property** does not exist on Peios — scheduling is per-thread, not per-process. A multi-threaded process can run different threads at different priorities and classes simultaneously.
