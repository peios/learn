---
title: perf Events
type: concept
description: The perf_event_open() syscall, scoping (per-task / per-CPU / per-cgroup), hardware PMU and software events, sampling vs counting, the PerfParanoidLevel registry knob, callchains and SFrame.
related:
  - peios/tracing/overview-and-design
  - peios/tracing/instrumentation-primitives
  - peios/tracing/ftrace
  - peios/tracing/privileges-and-controls
  - peios/privileges/profile-single-process
  - peios/privileges/system-profile
---

`perf_event_open()` is the syscall behind the entire perf ecosystem (the `perf` userspace tool, `bpftrace`, `sysprof`, profilers in IDEs). It opens a single event source as an fd; the fd carries either a counter or a sampling stream consumed via an mmap'd ring buffer. It is **the only primitive in this section with a genuine unprivileged path**: own-task profiling at the default paranoid level requires no privilege.

## The syscall

```c
int perf_event_open(struct perf_event_attr *attr, pid_t pid, int cpu,
                    int group_fd, unsigned long flags);
```

The scoping is determined by `pid` and `cpu`:

| `pid` | `cpu` | Meaning |
|---|---|---|
| `0` | `-1` | Own task, all CPUs. |
| `0` | `>=0` | Own task, only when running on CPU N. |
| `>0` | `-1` | Specific PID, all CPUs (cross-task). |
| `>0` | `>=0` | Specific PID, on CPU N. |
| `-1` | `>=0` | All tasks on CPU N (per-CPU profiling). |
| `-1` | `-1` | Invalid. |

With the `PERF_FLAG_PID_CGROUP` flag, the `pid` argument carries a cgroup fd, scoping the event to all tasks in that cgroup.

The `attr.type` field selects the event source:

| Type | Source |
|---|---|
| `PERF_TYPE_HARDWARE` | Hardware PMU events (cycles, instructions, cache references, branch instructions, etc.). |
| `PERF_TYPE_SOFTWARE` | Kernel-maintained events (page faults, context switches, CPU clock, task clock). |
| `PERF_TYPE_TRACEPOINT` | A specific tracepoint as the event source. |
| `PERF_TYPE_HW_CACHE` | Detailed cache events (L1/L2/LLC/iTLB/dTLB/BPU/NODE × read/write/prefetch × access/miss). |
| `PERF_TYPE_RAW` | Raw PMU event codes (CPU-specific). |
| `PERF_TYPE_BREAKPOINT` | Hardware breakpoints. |
| Dynamic types | kprobe pmu, uprobe pmu (registered IDs). |

## Counting and sampling modes

Two fundamental modes:

- **Counting** — the kernel just increments a counter. The fd has no ring buffer; you `read()` to get the current count. Cheap. Used to answer "how many cache misses in this region?"
- **Sampling** — every N events (or every Hz, in the time-based case), the kernel writes a sample record into an mmap'd ring buffer. The sample carries program counter, callchain, registers, cgroup, timestamp, and other configurable fields.

Sampling is what drives profilers — `perf record` is "sample at 99 Hz, capture callchains, demangle later." Counting is what drives micro-benchmarks — "how many branch mispredicts in this loop."

## Hardware PMU and multiplexing

Hardware PMU counters are a finite resource — a typical x86 CPU has 4–8 general-purpose counters plus 3 fixed counters per core. Asking for more events than there are counters triggers **multiplexing**: the kernel rotates events through the available counters, scaling each measurement by `time_running / time_enabled` to estimate the full count. Multiplexed measurements are estimates with noise; profilers that need exact counts must stay within the counter budget.

Newer hardware adds precise sampling (Intel PEBS, AMD IBS, ARM SPE) — the CPU writes the sample buffer directly without an interrupt-then-read sequence, dramatically reducing skid. Peios honours these where available; no policy decision.

## The paranoid level

The `\System\Tracing\PerfParanoidLevel` registry knob controls what unprivileged callers can do. It maps directly to Linux's `perf_event_paranoid` levels:

| Level | What unprivileged callers can do |
|---|---|
| `0` | Tracepoints + own-task with all event types. CPU events allowed. |
| `1` | Own-task with all event types. Tracepoints allowed. CPU events require `SeSystemProfilePrivilege`. |
| `2` | Own-task user-mode events. Kernel events on own task require `SeSystemProfilePrivilege`. **Default.** |
| `3` | Own-task user-mode events only. Kernel events / kallsyms even on own task require `SeSystemProfilePrivilege`. |
| `4` | Nothing without `SeSystemProfilePrivilege` (very paranoid). |

Default `2` matches the upstream Linux default. Application developers profiling their own code work without privilege; system-wide profiling and kernel sampling require `SeSystemProfilePrivilege`.

The Linux `-1` level (no restrictions) is **not supported** on Peios. There is no legitimate use case for disabling the gate entirely; principals needing system-wide perf access should be granted `SeSystemProfilePrivilege`.

## Privilege model

| Authority | Privilege |
|---|---|
| Own-task profiling at default paranoid level | None — any principal. |
| Cross-task profiling (specific other process) | `SeProfileSingleProcessPrivilege`. PIP-respecting — cannot profile a PIP-protected target without dominance. |
| System-wide profiling, per-CPU profiling, kernel-mode events | `SeSystemProfilePrivilege`. Operator-class privilege — granted to monitoring services rather than interactive users. |
| Per-cgroup profiling | Cgroup SD-based — read access on the cgroup container is sufficient. |
| Tracepoint as event source | Inherits from the above (own-task / cross-task / system-wide). |
| kprobe/uprobe as event source | `SeLoadDriverPrivilege` for the attach (covered by [instrumentation primitives](instrumentation-primitives)) regardless of which other privilege gates the perf consumption. |

Notably, `SeSystemProfilePrivilege` is **not** PIP-respecting at the per-sample level — once granted, system-wide samples include PIP-protected tasks (the perf machinery does not filter samples by integrity). This is the same property as `SeLoadDriverPrivilege` but at lower blast radius: perf samples reveal program counters and counter values, not function arguments. Operators granting `SeSystemProfilePrivilege` should treat the holder as trusted with system-wide observation including across the integrity boundary.

## Resource limits

The perf subsystem is a real resource pressure point — sampling events accumulate in mmap'd ring buffers, and high sample rates can swamp a CPU. Registry knobs:

| Knob | Effect | Default |
|---|---|---|
| `\System\Tracing\PerfMaxSampleRateHz` | Cap on samples / sec / CPU. | 100000 |
| `\System\Tracing\PerfMaxStackDepth` | Maximum callchain depth recorded per sample. | 127 |
| `\System\Tracing\PerfMlockKbPerPrincipal` | mlock'd ringbuf budget per principal. | 516 (KiB) |
| `\System\Tracing\PerfMaxOpenEventsPerPrincipal` | Concurrent perf fds per principal. | 1024 |

Holders of `SeSystemProfilePrivilege` can override the per-principal limits where the kernel allows; the knobs primarily bound unprivileged callers.

## Callchains and SFrame

Sampling profilers want callchains — the stack trace at each sample. The kernel walks the stack from the trapping context and records the return-address chain. Walking userspace stacks requires unwind information; the traditional source is `.eh_frame` (DWARF-encoded, verbose).

Kernel 6.19 adds **SFrame** support — a compact stack-unwinding format, an alternative to `.eh_frame` for unwinding. SFrame is significantly smaller and faster to consume, materially reducing the cost of callchain capture in perf and BPF callgraph mode. Peios honours SFrame where binaries provide it; no policy decision.

For kernel-mode callchains, kallsyms is needed to resolve addresses to function names. At paranoid level 2 and above, unprivileged callers see zero addresses, making kernel-mode samples uninterpretable without `SeSystemProfilePrivilege`. This is intentional — kernel sampling without symbol resolution is much less useful, degrading the attack value for unprivileged callers without breaking profiling for authorized ones.

## Latency profiling via context switches

Kernel 6.15 added latency-profiling support via `sched_switch` as the event source. Conventional perf sampling captures *on-CPU* time at PMU events; latency profiling captures *off-CPU* time by sampling on scheduler switches and recording the wakeup callchain. This makes I/O-bound and lock-contention bottlenecks visible.

Subject to the same privilege gates as any tracepoint-driven sampling — own-task at default paranoid level is unprivileged; system-wide requires `SeSystemProfilePrivilege`.

## fdinfo introspection

Kernel 6.17 adds perf-event fields to `/proc/[pid]/fdinfo/[fd]`. Reading own-task fdinfo for own perf fds is unprivileged. Reading another principal's fdinfo follows the standard /proc access check.

## The `perf` userspace tool

The `perf` tool wraps `perf_event_open()` plus userspace post-processing (callchain symbol resolution, demangling, aggregation, flame-graph generation). It runs entirely as the invoking principal; the kernel-side authority is determined by `perf_event_open()` per the rules above.

Peios ships the standard `perf` tool from the kernel-tools package. New 7.0 additions (`perf sched stats` for scheduling-statistics analysis) are included.

## See also

- [Instrumentation primitives](instrumentation-primitives) — the event sources perf consumes.
- [`SeProfileSingleProcessPrivilege`](../privileges/profile-single-process) — cross-task profiling.
- [`SeSystemProfilePrivilege`](../privileges/system-profile) — system-wide profiling.
- [ftrace](ftrace) — the alternative consumer surface, no own-task path, system-wide-only privilege.
