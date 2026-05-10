---
title: Privileges and Controls
type: how-to
description: Privilege summary, registry-knob index, access-control matrix, and audit posture for the tracing and profiling subsystems.
related:
  - peios/tracing/overview-and-design
  - peios/tracing/instrumentation-primitives
  - peios/tracing/ftrace
  - peios/tracing/perf-events
  - peios/tracing/ptrace
  - peios/privileges/load-driver
  - peios/privileges/debug
  - peios/privileges/profile-single-process
  - peios/privileges/system-profile
---

A consolidated reference for the privileges and registry knobs that gate Peios's tracing and profiling subsystems. This page is the single source of truth for "what privilege do I need to do X" and "what knob controls Y."

## Privilege summary

| Privilege | Gates | PIP-respecting? |
|---|---|---|
| `SeLoadDriverPrivilege` | All kernel-resident code installation: kernel modules, kprobes, kretprobes, uprobes, uretprobes, BPF on tracing/LSM/networking attach points, RV monitor registration, system-wide ftrace operations (tracefs reads/writes, kprobe_events / uprobe_events). Bypasses PIP — handlers run inside the kernel, below the access-check layer. | **No.** The unique below-the-access-check-layer privilege. |
| `SeDebugPrivilege` | Cross-process ptrace beyond the `PtraceScope` default. `PTRACE_SECCOMP_GET_FILTER` always (regardless of attach status). | Yes. Cannot debug a PIP-protected target without dominance. |
| `SeProfileSingleProcessPrivilege` | `perf_event_open()` attached to a specific other process (cross-task profiling). | Yes. Cannot profile a PIP-protected target without dominance. |
| `SeSystemProfilePrivilege` | System-wide `perf_event_open()`: per-CPU events, all-task sampling, kernel-mode events, the cross-paranoid-level capabilities of the syscall. | Not at the per-sample level — system-wide samples include PIP-protected tasks. Privilege itself is checked in userspace. |

No tracing-specific privilege is needed for own-task profiling at the default paranoid level.

## Registry knob index

### Tracing master controls

| Knob | Effect | Default |
|---|---|---|
| `\System\Tracing\TracefsEnabled` | Mount and operate tracefs at boot. | `true` |
| `\System\Tracing\TracefsMountPoint` | Mount point for tracefs. | `/sys/kernel/tracing` |
| `\System\Tracing\PtraceEnabled` | Master ptrace kill switch. | `true` |
| `\System\Tracing\RuntimeVerificationEnabled` | RV subsystem available. No monitors active by default. | `true` |

### Scope and paranoid controls

| Knob | Effect | Default |
|---|---|---|
| `\System\Tracing\PtraceScope` | Default scope for cross-process ptrace. 0 = same-principal + descendants, 1 = descendants only, 2 = `SeDebugPrivilege` only, 3 = disabled. | `1` |
| `\System\Tracing\PerfParanoidLevel` | Unprivileged-caller scope for `perf_event_open()`. 0 = lax, 4 = paranoid. | `2` |

### perf resource limits

| Knob | Effect | Default |
|---|---|---|
| `\System\Tracing\PerfMaxSampleRateHz` | Cap on samples / sec / CPU. | 100000 |
| `\System\Tracing\PerfMaxStackDepth` | Maximum callchain depth recorded per sample. | 127 |
| `\System\Tracing\PerfMlockKbPerPrincipal` | mlock'd ringbuf budget per principal (KiB). | 516 |
| `\System\Tracing\PerfMaxOpenEventsPerPrincipal` | Concurrent perf fds per principal. | 1024 |

### User trace events

| Knob | Effect | Default |
|---|---|---|
| `\System\Tracing\UserTraceEventsEnabled` | Master kill switch for `user_events`. | `true` |
| `\System\Tracing\UserTraceEventsMaxPerPrincipal` | Cap on registered events per principal. | 256 |
| `\System\Tracing\UserTraceEventsMaxTotalBytes` | Cap on total kernel state for registrations per principal. | 65536 |

### Audit / kernel-symbol exposure

| Knob | Effect | Default |
|---|---|---|
| `\System\Audit\KallsymsRestrict` | Kernel symbol address exposure. 0 = visible to all, 1 = `SeLoadDriverPrivilege` only, 2 = nobody. | `1` |

## Access-control matrix

| Operation | Authority required |
|---|---|
| Read own-task tracepoints via perf at default paranoid | None. |
| Read system-wide tracepoints via tracefs | `SeLoadDriverPrivilege`. |
| Read system-wide tracepoints via perf | `SeSystemProfilePrivilege`. |
| Attach kprobe / kretprobe (any path) | `SeLoadDriverPrivilege`. |
| Attach uprobe / uretprobe (any path) | `SeLoadDriverPrivilege`. |
| Attach BPF fentry / fexit | `SeLoadDriverPrivilege`. |
| Operate ftrace tracers (function, function_graph, etc.) | `SeLoadDriverPrivilege`. |
| Read `/proc/kallsyms` real addresses | `SeLoadDriverPrivilege` (at default `KallsymsRestrict=1`). |
| Register an RV monitor | `SeLoadDriverPrivilege`. |
| Register a `user_events` event | None (subject to per-principal quotas). |
| Subscribe to your own `user_events` events | None. |
| Subscribe to others' `user_events` events system-wide | `SeLoadDriverPrivilege`. |
| Profile own task with hardware PMU events | None at default paranoid; `SeSystemProfilePrivilege` at paranoid 4. |
| Profile own task with kernel events | None at paranoid 0/1; `SeSystemProfilePrivilege` at paranoid 2/3/4. |
| Profile a specific other process | `SeProfileSingleProcessPrivilege` + PIP dominance. |
| Profile system-wide / per-CPU / kernel-mode | `SeSystemProfilePrivilege`. |
| Profile a cgroup | Cgroup SD (read access on cgroup container). |
| `PTRACE_TRACEME` | None — self-trace is always allowed. |
| `PTRACE_ATTACH` / `PTRACE_SEIZE` to descendant | None at default `PtraceScope=1` + PIP dominance + target SD. |
| `PTRACE_ATTACH` / `PTRACE_SEIZE` to non-descendant same-principal | None at `PtraceScope=0`; `SeDebugPrivilege` at `PtraceScope=1` or `2`; PIP dominance always; target SD always. |
| `PTRACE_ATTACH` / `PTRACE_SEIZE` cross-principal | `SeDebugPrivilege` + PIP dominance + target SD. |
| `PTRACE_SECCOMP_GET_FILTER` | `SeDebugPrivilege` regardless of attach status. |
| Read `/proc/[pid]/syscall` | Process SD `PROCESS_QUERY_INFORMATION` + PIP dominance. |

## Audit posture

The KMES audit pipeline carries the security-relevant events from the tracing subsystems. Two classes:

### Audit-class (cannot be filtered out)

| Event | Carries |
|---|---|
| kprobe / kretprobe / fentry / fexit attach | Target function name, principal, attach path. |
| uprobe / uretprobe attach | Target inode (path + dev/ino), offset, resolved symbol, principal, attach path. |
| Tracer / tracepoint enable via tracefs | Target tracepoint or tracer, principal. |
| RV monitor registration | Monitor type, principal, spec source. |
| `PTRACE_ATTACH` / `PTRACE_SEIZE` | Tracer principal, tracee GUID, attach type, authorization path. |
| `PTRACE_SECCOMP_GET_FILTER` | Tracer principal, tracee GUID, requested filter index, result. |
| System-wide perf attach with kernel events | Principal, event spec, scope. |

### Forensic-class (subject to declarative filters)

| Event | Carries |
|---|---|
| `user_events` event registration | Principal, event name, format string. |
| Own-task perf attach | Principal, event spec. |
| Cross-task perf attach | Tracer principal, target GUID, event spec. |
| RV monitor violation | Monitor identifier, violation context (forwarded to tracefs by default; bridge to KMES via BPF if needed). |

Sub-operations on an attached ptrace tracee, individual tracepoint reads, and individual perf samples are not separately audited — the attach / registration is the gateable moment, and downstream consumption is the natural authority of the tracer-consumer relationship.

## Threat model summary

| Threat | Defense |
|---|---|
| Unprivileged caller installs kprobe to steal credentials from `vfs_read` | `SeLoadDriverPrivilege` required for all kprobe attach paths. |
| Unprivileged caller uprobes `libssl::SSL_write` to read plaintext | `SeLoadDriverPrivilege` required for all uprobe attach paths; no per-binary-ownership exception. |
| Unprivileged caller uses kallsyms to attack KASLR | `KallsymsRestrict=1` default — non-`SeLoadDriverPrivilege` callers see zeros. |
| Same-uid malware ptrace-dumps your browser's ssh-agent state | `PtraceScope=1` default — descendants only. Malware needs your shell to fork it before it can attack other same-principal processes. |
| Attacker extracts seccomp filter to plan a syscall-misuse attack | `SeDebugPrivilege` required for `PTRACE_SECCOMP_GET_FILTER` regardless of attach status. |
| Attacker holds `SeDebugPrivilege`, tries to debug a higher-integrity process | PIP dominance check fails. `SeDebugPrivilege` is PIP-respecting. |
| Attacker holds `SeSystemProfilePrivilege`, observes PIP-protected processes via system-wide samples | Accepted risk. `SeSystemProfilePrivilege` is operator-class — granted only to monitoring services trusted with cross-integrity observation. Reveals PCs and counter values, not function arguments. |
| User-trace-events DoS by registering millions of events | `UserTraceEventsMaxPerPrincipal` and `UserTraceEventsMaxTotalBytes` quotas. |
| Perf DoS by sampling at unbounded rate | `PerfMaxSampleRateHz` and `PerfMaxOpenEventsPerPrincipal` quotas. |
| Perf DoS by allocating huge ringbufs | `PerfMlockKbPerPrincipal` quota. |
| User trace events as a privacy leak (events visible to system-wide tracers) | Documented model: events are visible to anyone with system-wide tracepoint-read privilege. Apps should use KMES emit for sensitive paths. |

## Tooling matrix

Standard Linux tracing tooling and the privileges they need under default Peios policy:

| Tool | Typical use | Privilege needed |
|---|---|---|
| `perf record` (own task) | App developer profiles their own code | None (paranoid 2 default). |
| `perf record -p $PID` (other process) | Profile a specific process | `SeProfileSingleProcessPrivilege` + PIP dominance. |
| `perf record -a` (system-wide) | System-wide profiling | `SeSystemProfilePrivilege`. |
| `perf top` | Live system-wide top | `SeSystemProfilePrivilege`. |
| `perf trace` | strace-equivalent via perf | Per-task: none for own; cross-task: `SeProfileSingleProcessPrivilege`; system-wide: `SeSystemProfilePrivilege`. |
| `bpftrace` (one-liners with kprobes/uprobes) | Ad-hoc kernel observability | `SeLoadDriverPrivilege` (BPF + kprobe/uprobe). |
| `strace` (run + trace child) | Trace own subprocesses | None (descendant). |
| `strace -p $PID` (attach) | Trace running process | None at `PtraceScope=0`; `SeDebugPrivilege` at default. |
| `gdb` (run binary under) | Debug own subprocess | None (descendant). |
| `gdb --pid=$PID` (attach) | Attach to running process | None at `PtraceScope=0`; `SeDebugPrivilege` at default. |
| `trace-cmd` / direct tracefs | Kernel debugging via ftrace | `SeLoadDriverPrivilege`. |
| `rv-mon` (RV control) | Run a runtime-verification monitor | `SeLoadDriverPrivilege`. |
| `sysprof` (system profiler GUI) | Visual profiling | Per-task: none; system-wide: `SeSystemProfilePrivilege`. |

## See also

- [Overview and design](overview-and-design) — the two-pipeline model and the BPF bridge.
- [Instrumentation primitives](instrumentation-primitives) — what fires.
- [ftrace](ftrace) — the in-kernel tracer.
- [perf events](perf-events) — the syscall-driven profiler.
- [ptrace](ptrace) — the debugger interface.
- [Auditing](../auditing/overview-and-design) — KMES, the audit pipeline, and how it relates to tracing.
- [eBPF — Peios integration](../ebpf/peios-integration) — the bridge from tracing primitives into KMES.
