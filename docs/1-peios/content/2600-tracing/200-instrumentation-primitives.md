---
title: Instrumentation Primitives
type: concept
description: The five kernel instrumentation primitives — tracepoints, kprobes, uprobes, fprobes/fentry, and user trace events — and the access-control model for each.
related:
  - peios/tracing/overview-and-design
  - peios/tracing/ftrace
  - peios/tracing/perf-events
  - peios/tracing/privileges-and-controls
  - peios/ebpf/program-types-and-attach-points
  - peios/privileges/load-driver
---

The kernel exposes five primitives that produce trace events. Everything in §13 of the Linux feature surface — ftrace tracers, perf event sources, BPF attach points — terminates in one of these.

| Primitive | What it instruments | Placement | Stability |
|---|---|---|---|
| **Tracepoints** | Specific kernel events (`sched_switch`, `sys_enter_*`, `ext4_*`). | Compile-time, hand-placed in source. | Stable-ish ABI. |
| **kprobes / kretprobes** | Any kernel function entry / exit. | Runtime. Patches the function with a breakpoint or jump. | Unstable — function names and signatures change. |
| **uprobes / uretprobes** | Any userspace function in any binary. | Runtime. Kernel writes to the page-cache copy of the inode. | Depends on the binary. |
| **fprobes / fentry / fexit** | Kernel function entry / exit via the ftrace nop slot. | Runtime, ftrace-based. Cheaper than kprobes. | Same as kprobes. |
| **User trace events** | Userspace-defined tracepoints. | Runtime. App registers an event by writing a definition to tracefs. | App-defined. |

All five share an important property on Peios: **they install or expose kernel-side state that any consumer of the appropriate privilege can read**. That structural property — events go through a kernel trap, handler, or shared ring buffer — is why most of these primitives sit at the `SeLoadDriverPrivilege` tier.

## Tracepoints

`Tracepoints` are statically placed instrumentation in the kernel source. A tracepoint at `sched_switch` fires every time the scheduler switches tasks; a tracepoint at `sys_enter_open` fires on every `open` syscall. They are compile-time-baked, very low overhead when off (a single `nop` slot), and described by a stable-ish ABI.

Tracepoints have **no per-tracepoint ACLs**. They are gated entirely through their consumers:

| Path to tracepoint events | Gate |
|---|---|
| Via tracefs (`echo 1 > .../events/sched/sched_switch/enable`, then `cat trace`) | tracefs operations require `SeLoadDriverPrivilege` (see [ftrace](ftrace)). |
| Via `perf_event_open()` with `PERF_TYPE_TRACEPOINT` | `PerfParanoidLevel` registry knob (see [perf events](perf-events)). |
| Via BPF tracepoint attach | `SeLoadDriverPrivilege` (see [eBPF — privileges](../ebpf/privileges-and-trust)). |

Once a caller has tracepoint-read privilege at the relevant level, all enabled tracepoints are visible — there is no notion of "tracepoint X is more privileged than tracepoint Y." Authors of kernel subsystems should be aware that some tracepoints fire on shared paths and may carry sensitive data (`sys_enter_*` includes syscall arguments which can include paths, secrets, etc.).

Peios subsystems (KACS, LCS, KMES, FACS) expose tracepoints alongside their KMES emits. The tracepoints are for kernel-developer debugging; the KMES events are for stable, security-relevant operator and audit consumption. See [overview](overview-and-design) for the framing.

## kprobes and kretprobes

`kprobes` patch any kernel function at runtime. The kernel installs a breakpoint (or, where the ftrace nop slot is available, a jump) at the requested address; when execution hits the patched site, the kernel traps into the probe handler, runs it, and resumes. `kretprobes` rewrite the trapping task's return address so the handler also runs at function exit.

There is no "exposed API" subset — a kprobe can hook **any** kernel function. The handler can read every register at the trap site (and therefore any kernel memory the function held pointers to: credentials, keys, page tables, file paths) and read function arguments.

The three install paths:

| Path | Description |
|---|---|
| `kprobe_events` (tracefs) | Write text definitions to `/sys/kernel/tracing/kprobe_events`. Output goes to ftrace ring buffer. |
| `perf_event_open(PERF_TYPE_KPROBE...)` | Syscall-driven, perf consumes via mmap'd ring buffer. |
| BPF kprobe-attach | A BPF program runs in the probe handler. |

All three install the same underlying kprobe; they differ in who consumes the events.

### Privilege model

kprobes (and kretprobes) are gated by `SeLoadDriverPrivilege` regardless of install path. The reasoning:

- The handler runs in the kernel, below the access-check layer. It is not subject to PIP — a kprobe handler observing `vfs_read` sees data from PIP-protected processes that the installer's userspace context could not.
- This is the unique property of kernel-resident code. `SeLoadDriverPrivilege` is the privilege that gates "install code that runs inside the kernel" — kernel modules, kprobes, uprobes, BPF on tracing/LSM/networking attach points.

See [`SeLoadDriverPrivilege`](../privileges/load-driver) for the framing — this is the most powerful privilege in the system and the only one that bypasses PIP.

### Kallsyms exposure

Kernel symbol addresses (visible via `/proc/kallsyms` and several other interfaces) are needed to attach kprobes by name. Linux gates this with `kptr_restrict`; Peios uses the registry knob `\System\Audit\KallsymsRestrict`:

| Value | Behaviour |
|---|---|
| `0` | All callers see real addresses (legacy, unsafe). |
| `1` | `SeLoadDriverPrivilege` holders see real addresses; others see `0x0`. **Default.** |
| `2` | Nobody sees real addresses (lockdown-style). |

Note that `SeDebugPrivilege` does **not** unlock kallsyms — `SeDebugPrivilege` is a userspace-debugger privilege; kernel-symbol exposure is in the kernel-introspection class.

### Audit-the-attach

Every successful kprobe / kretprobe registration emits a KMES audit-class event with: target function name, attaching principal, attach path (`kprobe_events` / `perf` / `BPF`), and the attached fd or BPF program identifier where applicable.

## uprobes and uretprobes

`uprobes` patch arbitrary functions in userspace binaries. The kernel writes to the **inode-backed page cache** of the target binary at the requested offset; every process that has that page mapped — current and future — traps when execution hits it. `uretprobes` additionally rewrite the return address on the trapping task's stack to also trap on exit.

The probe is keyed by `inode + offset`, not by process. A uprobe on `libc.so:malloc` traps every process using that libc on every `malloc` call. You cannot scope a uprobe to "only process X's libc" at install time; you can filter at the *handler* level (BPF program checks `bpf_get_current_pid_tgid()`), but the probe is always system-wide.

The three install paths:

| Path | Description |
|---|---|
| `uprobe_events` (tracefs) | Write definitions to `/sys/kernel/tracing/uprobe_events`. Output goes to ftrace ring buffer. |
| `perf_event_open(PERF_TYPE_UPROBE...)` | Syscall-driven, perf consumes via mmap'd ring buffer. |
| BPF uprobe-attach | A BPF program runs in the probe handler. |

### Privilege model

uprobes (and uretprobes) are gated by `SeLoadDriverPrivilege` regardless of install path. The reasoning is structurally the same as kprobes — the probe handler runs in the kernel and observes data PIP would protect — but with the additional consideration that uprobes are *system-wide read primitives*. A uprobe on `libssl::SSL_write` exposes plaintext for every process linking that library. A uprobe on `crypto_*` exposes every key operation.

There is **no per-binary-ownership exception**. Even uprobing a binary you wrote and own affects the page cache, which is shared with every other process mapping that file. Ownership of the binary file is not the right gate; the gate is "are you allowed to install a system-wide read primitive."

For self-instrumentation without privilege, the path is `PTRACE_TRACEME` plus self-modifying code — see [ptrace](ptrace). uprobes are not for self-instrumentation.

### Shadow-stack interaction

`uretprobe` rewrites return addresses on the trapping task's stack. This conflicts with hardware shadow stacks (Intel CET, ARM BTI). The kernel handles this by special-casing uretprobe return addresses in the shadow-stack check. No user-visible policy decision; honoured at the kernel level.

### User-namespace awareness

Recent kernels added some user-namespace awareness for uprobes. Peios v1 rejects `CLONE_NEWUSER` (see [process silos](../process-silos/silos-and-namespaces)). The flag is honoured at the syscall level for ABI compatibility but has no effect.

### Audit-the-attach

Every successful uprobe / uretprobe registration emits a KMES audit-class event with: target inode (path + dev/ino), offset, resolved symbol name (where available), attaching principal, and attach path.

## fprobes / fentry / fexit

`fprobes` are kernel-internal probe attachments that use the ftrace nop slot already compiled into every traceable kernel function. They are cheaper than kprobes because they reuse the ftrace infrastructure rather than installing a breakpoint trap. `fentry` and `fexit` are the BPF-specific attach types built on this mechanism.

| Mechanism | Description | Path |
|---|---|---|
| **fprobe** | Generic ftrace-nop probe. | Kernel-internal API; used by ftrace's function tracer and a few specialised tools. No userspace-textual install path equivalent to `kprobe_events`. |
| **fentry** (BPF) | BPF program at function entry via ftrace nop. | BPF-only attach (`BPF_TRACE_FENTRY`). |
| **fexit** (BPF) | BPF program at function exit via ftrace return trampoline. | BPF-only attach (`BPF_TRACE_FEXIT`). |

`DYNAMIC_FTRACE` is always enabled on Peios (matching kernel 6.17+), which provides the underlying nop-slot infrastructure unconditionally.

### Privilege model

Identical to kprobes. The fact that fentry is faster than kprobes does not reduce the blast radius; it just makes it cheaper to deploy. `SeLoadDriverPrivilege` gates BPF fentry / fexit attach (already covered by the BPF privilege model — see [eBPF — privileges](../ebpf/privileges-and-trust)). Internal kernel use of fprobes is gated by the consumer's privilege.

### Audit-the-attach

KMES audit-class event with the same shape as kprobes — target function name, principal, attach path. The path field distinguishes `fentry` / `fexit` / `kprobe` / `kretprobe` for forensic purposes.

## User trace events

`user_events` (kernel 6.4+) lets a userspace application register and emit its own tracepoints. The lifecycle:

1. App opens `/sys/kernel/tracing/user_events_data`.
2. App `ioctl`s `DIAG_IOCSREG` with an event name and a format string (e.g. `myapp_request u32 request_id; char[64] path`).
3. Kernel registers the event and returns a write index.
4. App writes binary event records to the fd with the write index in the header.
5. Tracepoint consumers (anywhere in the system) can subscribe to `user_events:myapp_request` and receive the records.

There is also a `user_events_status` file that lets the app check whether anyone is listening — useful for skipping emission entirely when nobody cares.

### Stance: ship for compat, do not promote

Peios already has a much better answer to "userspace app wants to emit structured kernel-mediated events": KMES. KMES has stable schemas, kernel-mediated audit, durable event flow through eventd, and SD-based routing. user_events is the inferior cousin — events are ephemeral, schema is a format string with no versioning, no audit semantics, and visibility is all-or-nothing through the tracepoint privilege.

Native Peios apps should reach for KMES emit. user_events exists for Linux apps that already use it (newer userspace tracing libraries, ports of code that uses LTTng-UST or USDT-style instrumentation that has been migrated to user_events).

### Privilege model

Registration is **unprivileged**, subject to per-principal quotas:

| Knob | Effect | Default |
|---|---|---|
| `\System\Tracing\UserTraceEventsEnabled` | Master kill switch. | `true` |
| `\System\Tracing\UserTraceEventsMaxPerPrincipal` | Cap on registered events per principal. | 256 |
| `\System\Tracing\UserTraceEventsMaxTotalBytes` | Cap on total kernel state for registrations per principal. | 65536 (64 KiB) |

Emission requires only the registered fd — the fd itself is the capability.

Subscribing to events:

- **Own-principal subscribe is unprivileged.** The principal that registered an event can always subscribe to it. This makes user_events genuinely useful for in-app self-instrumentation without leaking anything.
- **Cross-principal / system-wide subscribe** inherits from the tracepoint subscribe gates — `SeLoadDriverPrivilege` for system-wide via tracefs/perf/BPF, or the appropriate `PerfParanoidLevel` for perf-mediated subscription.

There is no per-event SD. Events are visible to anyone with system-wide tracepoint-read privilege; document the visibility model rather than gate per-event.

### Cross-binary name collisions

Events are namespaced by registering principal + name. No cross-principal name collisions; multiple principals can register an event named `myapp_request` independently.

### Audit posture

Registration emits a KMES forensic-class event (not audit-class — it is a breadcrumb, not a security decision). Subject to declarative audit filters.

## See also

- [`SeLoadDriverPrivilege`](../privileges/load-driver) — the privilege gating kprobes, uprobes, fprobes, BPF tracing attach.
- [eBPF — Peios integration](../ebpf/peios-integration) — BPF as the bridge from these primitives into KMES.
- [ftrace](ftrace) — the consumer surface for tracepoints, kprobes, function tracers.
- [perf events](perf-events) — the syscall-driven consumer surface and the `PerfParanoidLevel` knob.
