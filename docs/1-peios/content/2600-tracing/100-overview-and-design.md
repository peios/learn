---
title: Tracing and Profiling — Overview and Design
type: concept
description: How Peios layers Linux's tracing and profiling subsystems alongside KMES — two structurally separate event pipelines, with BPF as the only legitimate bridge.
related:
  - peios/tracing/instrumentation-primitives
  - peios/tracing/ftrace
  - peios/tracing/perf-events
  - peios/tracing/ptrace
  - peios/tracing/privileges-and-controls
  - peios/auditing/overview-and-design
  - peios/ebpf/overview-and-design
---

Peios honours Linux's full tracing and profiling surface — ftrace, perf, ptrace, and the underlying instrumentation primitives (tracepoints, kprobes, uprobes, fprobes, user trace events). This section covers what each subsystem does, how they compose, and where they sit in the Peios access-control model.

The most important thing to understand up front is the **two-pipeline split**.

## Two pipelines, not one

Peios has two structurally different event pipelines, sized for different workloads:

| Pipeline | Purpose | Volume | Persistence | Schema |
|---|---|---|---|---|
| **KMES → eventd** | Structured, durable, security-relevant events. The system's audit and observability backbone. | ~100k/s comfortable, ~500k/s ceiling. | Persisted via eventd (SQLite). Survives reboots. | Stable, versioned, msgpack-typed. |
| **ftrace / perf ring buffers** | Ad-hoc kernel debugging and performance profiling. Owned by the consumer that opened the fd. | Millions/s on busy systems. | Ephemeral. Drained by the consumer or lost on overflow. | Whatever the consumer asks for. |

The volume difference is two to three orders of magnitude. ftrace's `function` tracer alone fires 10M+ events/s on idle systems. `sched_switch` on a busy server is 1M+/s. Routing those through KMES would melt eventd in milliseconds. ftrace and perf live where they live — high-volume, ephemeral, consumer-owned ring buffers — for that reason.

KMES is the wrong shape for that workload (durable, structured, single-pipeline). ftrace and perf are the wrong shape for KMES's workload (ephemeral, no schema stability, no eventd correlation).

The two pipelines coexist with no shared plumbing. They share **attach points** as event sources (tracepoints, kprobes, uprobes), but the events flow into completely separate ring buffers, are consumed by different programs, and have completely different lifecycles.

## The bridge — BPF

The single legitimate path from a tracing primitive into KMES is a **BPF program**. The pattern:

1. A BPF program is loaded under `SeLoadDriverPrivilege`.
2. It attaches to a tracepoint, kprobe, uprobe, or fentry.
3. In its handler, it filters the events it cares about and calls `bpf_kmes_emit()` to forward the schema-typed event into KMES.

Why BPF and not a more direct "tracepoint-to-KMES" knob:

- **Filtering.** Most tracepoints fire at volumes KMES cannot sustain. The BPF program filters first ("only emit on `sched_setaffinity` from non-system principals"). Without filtering, the bridge is a footgun.
- **Schema translation.** Tracepoints emit raw kernel structs. KMES events are stable schemas. The BPF program is the natural place to do the translation.
- **Authority.** Attaching is already gated by `SeLoadDriverPrivilege`, and audit-the-attach gives a record of who is bridging what.

A direct tracepoint-to-KMES bridge would be either useless (no filtering means melted pipeline) or BPF-flavoured anyway (some inline filter expression). Peios does not ship one. BPF is the bridge.

See [eBPF — Peios integration](../ebpf/peios-integration) for the BPF helpers (`bpf_kmes_emit`, `bpf_kacs_*`, etc.).

## What displaces what

Where the Linux ecosystem haphazardly emits security/audit events through tracepoints (LSM probes fed into perf, kernel events scraped by journald), Peios's first-class subsystems emit to KMES directly:

- KACS access checks → KMES (origin_class=KACS).
- LCS registry mutations → KMES (origin_class=LCS).
- KMES self-events → KMES (origin_class=KMES).
- Kernel modules that want audit-class behaviour → emit to KMES via the kernel-side helper.

KMES displaces the *audit-via-tracepoint pattern* but does not replace tracepoints themselves. Tracepoints remain the right tool when an author wants ad-hoc instrumentation any consumer can pick up. Peios subsystems should expose tracepoints alongside their KMES emits — the two are at different layers:

- **Tracepoints** expose internal state-machine transitions for kernel-developer debugging.
- **KMES events** expose stable, security-relevant outcomes for operator and audit consumption.

These should never be the same events. A KACS access-check has a stable KMES event ("decision rendered, principal=X, target=Y, granted=Z") and may also have several internal tracepoints ("entered fast path", "fell through to slow path", "consulted SACL", "applied PIP override"). Different audiences, different stability guarantees.

## Linux compatibility surface

Peios ships:

- All Linux instrumentation primitives — tracepoints, kprobes, kretprobes, uprobes, uretprobes, fprobes, user trace events.
- ftrace with all upstream tracers (function, function_graph, hwlat, irqsoff, preemptoff, mmiotrace, etc.).
- `perf_event_open()` with hardware PMU, software events, tracepoint, kprobe/uprobe, breakpoint, raw PMU sources.
- ptrace with the full operation set, including modern additions (`PTRACE_SEIZE`, `PTRACE_GET_SYSCALL_INFO`, `PTRACE_SET_SYSCALL_USER_DISPATCH`).
- Runtime Verification (RV) subsystem.
- SFrame stack-unwinding format.
- `DYNAMIC_FTRACE` always enabled.

Standard Linux tooling — `perf`, `bpftrace`, `strace`, `gdb`, `ftrace`-driven scripts, `sysprof`, `tracecompass` — works without modification. The differences are in *who* can do what (privilege model, registry-driven scoping), not *what* can be done.

## Where each piece is documented

| Page | Covers |
|---|---|
| [Instrumentation primitives](instrumentation-primitives) | Tracepoints, kprobes/kretprobes, uprobes/uretprobes, fprobes/fentry/fexit, user trace events. The attach surfaces. |
| [ftrace](ftrace) | The kernel's built-in tracer, tracefs, function/function_graph/latency tracers, RV. |
| [perf events](perf-events) | `perf_event_open()`, scoping, hardware PMU, sampling vs counting, paranoid level, callchains, SFrame. |
| [ptrace](ptrace) | The debugger interface, scope (`PtraceScope`), PIP interaction, sub-operations. |
| [Privileges and controls](privileges-and-controls) | Privilege summary, registry knobs, access-control matrix, audit posture. |

## What is *not* in this section

- **eBPF** — covered in [eBPF](../ebpf/overview-and-design). BPF attach points overlap heavily with tracing primitives, but BPF itself is a separate first-class extension mechanism with its own privilege model.
- **KMES** — covered in [auditing](../auditing/overview-and-design). KMES is the structured event pipeline; this section covers what *isn't* in it.
- **Audit** — covered in [auditing](../auditing/overview-and-design). The audit subsystem consumes KMES events; this section covers the tracing primitives that audit observability is *not* built on.

## See also

- [eBPF — Peios integration](../ebpf/peios-integration) — BPF as the bridge from tracing primitives into KMES.
- [Auditing](../auditing/overview-and-design) — KMES, the audit pipeline, and how it relates to tracing.
- [Privileges — `SeLoadDriverPrivilege`](../privileges/load-driver) — the unique below-the-access-check-layer authority that gates kernel-resident code installation.
