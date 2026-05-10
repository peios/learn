---
title: ftrace and tracefs
type: concept
description: The kernel's built-in tracer — function and function_graph tracers, latency tracers, the tracefs interface, and the Runtime Verification subsystem layered on top.
related:
  - peios/tracing/overview-and-design
  - peios/tracing/instrumentation-primitives
  - peios/tracing/perf-events
  - peios/tracing/privileges-and-controls
  - peios/privileges/load-driver
---

ftrace is the kernel's built-in tracer. It exposes function-level kernel tracing, latency tracers, and a tracepoint-management interface through a filesystem (`tracefs`). It is a privileged subsystem on Peios — every operation requires `SeLoadDriverPrivilege`. The reasoning: ftrace's `function` and `function_graph` tracers are equivalent in blast radius to "kprobes on every kernel function," and the same below-PIP-layer property applies.

## tracefs

The ftrace control surface is a pseudo-filesystem mounted at:

| Mount | Purpose |
|---|---|
| `/sys/kernel/tracing` | Modern path (kernel 4.1+). The canonical tracefs mount. |
| `/sys/kernel/debug/tracing` | Legacy path under debugfs. Shipped for compatibility; same privilege. |

Both expose the same control files. peinit mounts `/sys/kernel/tracing` at boot.

The registry knob `\System\Tracing\TracefsEnabled` (default `true`) is the master kill switch; setting it to `false` prevents tracefs from being mounted. `\System\Tracing\TracefsMountPoint` overrides the mount point if needed.

## Tracers

The `current_tracer` file selects the active tracer:

| Tracer | What it does |
|---|---|
| `nop` | No active tracer (default). |
| `function` | Trace every kernel function entry. Output via `trace` and `trace_pipe`. |
| `function_graph` | Trace function call hierarchy with timing. |
| `irqsoff` / `preemptoff` / `preemptirqsoff` | Latency tracers — record the longest interval with IRQs / preemption disabled. |
| `wakeup` / `wakeup_rt` / `wakeup_dl` | Latency tracers — record scheduling-wakeup latency. |
| `hwlat` | Hardware latency tracer — detect SMI / hypervisor stalls. |
| `mmiotrace` | Trace every MMIO read/write — driver-internal data exposure. |
| `blk` | Block-layer tracer (used by `blktrace`). |

Switching `current_tracer` changes system-wide behaviour. The `function` and `function_graph` tracers in particular are wholesale system-wide reads — every kernel function entry, with arguments visible in the trace records. Same blast radius as kprobes. Same privilege.

`DYNAMIC_FTRACE` is always enabled on Peios (matching the kernel 6.17 default). The runtime cost of unused ftrace nop slots is negligible, and dynamic ftrace is required for fentry/fexit BPF attach.

## Tracepoint management via tracefs

Tracepoints are enumerated under `/sys/kernel/tracing/events/`. Each subsystem has a directory; each tracepoint has an `enable` file. The shape:

```
events/
  sched/
    sched_switch/
      enable
      filter
      trigger
      format
    ...
  syscalls/
    sys_enter_open/
    sys_exit_open/
    ...
```

Writing `1` to `enable` activates the tracepoint; events flow to the global ring buffer (or to the active per-instance buffer — see below). The `filter` file accepts predicate expressions that drop non-matching events at the kernel level. The `trigger` file attaches actions (snapshots, stack dumps, histogram updates) to firing tracepoints.

The `set_event` file accepts shorthand syntax for bulk enables, including the `:mod:` syntax (kernel 6.14+) for module-specific scoping:

- `set_event :mod:nf_conntrack` — enable all tracepoints in the `nf_conntrack` module.

The kernel command line accepts `:mod:` filtering as well, so tracing can be scoped from boot.

## kprobe_events and uprobe_events

Two tracefs files allow installing kprobes and uprobes by writing textual definitions:

- `/sys/kernel/tracing/kprobe_events` — install a kprobe. See [instrumentation primitives — kprobes](instrumentation-primitives).
- `/sys/kernel/tracing/uprobe_events` — install a uprobe. See [instrumentation primitives — uprobes](instrumentation-primitives).

Both paths are gated by `SeLoadDriverPrivilege` (which is required to operate on tracefs at all). Audit-the-attach applies — every successful registration emits a KMES audit-class event.

These coexist with the BPF and perf attach paths. All three install the same underlying probe; they differ only in who consumes the events.

## Per-instance tracing

tracefs supports creating sub-instances under `instances/`, so multiple privileged consumers can have independent ring buffers without colliding:

```
mkdir /sys/kernel/tracing/instances/myinstance
echo function > /sys/kernel/tracing/instances/myinstance/current_tracer
cat /sys/kernel/tracing/instances/myinstance/trace
```

Each instance has its own `current_tracer`, `trace`, `trace_pipe`, `events/`, and filters. This is an isolation feature among privileged consumers — it does **not** reduce the privilege required. Creating an instance and using it both require `SeLoadDriverPrivilege`.

## Filters, triggers, and histograms

ftrace supports rich in-kernel processing:

- **Filters** — predicate expressions that drop non-matching events before they hit the ring buffer. Reduce volume.
- **Triggers** — actions attached to a firing tracepoint. Examples: take a stack snapshot, increment a histogram, fire another tracepoint, stop tracing.
- **Histograms** — aggregate event counts by field (e.g., `hist:keys=common_pid:vals=hitcount`). Read out of the `hist` file.

These are kernel-side analytics — useful for reducing volume without leaving kernel space. None change the privilege model.

## Output

The trace ring buffer is read out of:

- `trace` — formatted text, snapshot of the buffer.
- `trace_pipe` — formatted text, blocking stream (consumes events as they fire).
- `trace_pipe_raw` — raw binary, blocking stream.
- `per_cpu/cpuN/trace` and `per_cpu/cpuN/trace_pipe` — per-CPU views.
- `per_cpu/cpuN/stats` — overrun / dropped / written counts.

All require the same `SeLoadDriverPrivilege` — there is no own-task-only ftrace path. Applications wanting own-task tracing should use `perf_event_open()` instead (see [perf events](perf-events)).

## Runtime Verification

Linux's Runtime Verification (RV) subsystem (kernel 6.15+ scheduler monitors, 6.17+ LTL monitors) sits under tracefs. RV registers kernel-side state machines that observe scheduler / IRQ / locking transitions and report violations of a temporal-logic specification.

| Monitor type | Description |
|---|---|
| **Scheduler specification monitors** (6.15+) | Pre-built specs for scheduler invariants (e.g. `preempt_disable` balanced with `preempt_enable`). |
| **LTL monitors** (6.17+) | User-defined specs in Linear Temporal Logic. Compiled to a kernel monitor at registration time. |

RV is a kernel-development tool more than a production observability tool, but is shipped on Peios for the same reason ftrace is — debugging tools are useful and the kernel cost is negligible when no monitors are active.

### Privilege model

RV monitor registration is gated by `SeLoadDriverPrivilege`. The reasoning is the same as kprobes and BPF — RV monitors are kernel-resident state machines that observe state PIP would otherwise hide. They are read-only (just observing, not changing behaviour), but the read scope is system-wide.

The registry knob `\System\Tracing\RuntimeVerificationEnabled` (default `true`) is the master kill switch. The subsystem is available by default, but no monitors are active until explicitly registered.

### Audit posture

Monitor registration emits a KMES audit-class event with: monitor type (LTL / scheduler / etc.), registering principal, and the spec source where applicable. Monitor violations themselves are emitted via tracefs in the standard RV format and are subject to the consumer's read privilege; they are not separately routed into KMES (a userspace consumer is free to forward them via BPF if desired).

## tracefs lockdown integration

When the kernel is in `lockdown=integrity` or `lockdown=confidentiality` mode, additional restrictions apply:

- `kprobe_events` and `uprobe_events` may be read-only.
- Some tracers expose data classified by lockdown as off-limits; those become unavailable.

Peios honours the kernel-side lockdown model. The lockdown mode itself is set at boot.

## Kernel sched stats and `perf sched stats` (7.0)

Kernel 7.0 adds a `perf sched stats` user-mode tool that aggregates scheduling statistics from existing perf data. The tool is shipped as part of the perf package; no kernel-level policy decision required. Same privilege as the underlying perf events (typically `SeSystemProfilePrivilege` for system-wide scheduling stats).

## See also

- [Instrumentation primitives](instrumentation-primitives) — what fires inside ftrace.
- [perf events](perf-events) — the alternative consumer for tracepoint and kprobe events, with a more granular privilege model.
- [`SeLoadDriverPrivilege`](../privileges/load-driver) — the privilege gating tracefs operations.
