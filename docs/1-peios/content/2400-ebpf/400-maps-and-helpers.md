---
title: Maps and Helpers
type: concept
description: The data structures BPF programs use for state and userspace communication, and the helper/kfunc functions programs can call.
related:
  - peios/ebpf/overview-and-design
  - peios/ebpf/the-verifier
  - peios/ebpf/peios-integration
---

BPF programs are stateless on their own — every invocation receives only the context the attach point provides. Persistent state and communication with userspace happen through **maps**, a family of in-kernel data structures shared between programs and userspace. Programs interact with the kernel through **helpers** and **kfuncs**, function-call interfaces that the verifier permits per program type.

## Maps

A map is created with `BPF_MAP_CREATE` and accessed by both BPF programs (via map helpers) and userspace (via `bpf(BPF_MAP_*_ELEM, ...)`). The map type determines layout and access semantics.

| Type | Purpose |
|---|---|
| **`BPF_MAP_TYPE_HASH`** | Generic hashmap, key/value of fixed type |
| **`BPF_MAP_TYPE_ARRAY`** | Fixed-size array, integer-indexed |
| **`BPF_MAP_TYPE_PERCPU_HASH`** / **`PERCPU_ARRAY`** | Per-CPU variant; each CPU has its own copy. Avoids contention. |
| **`BPF_MAP_TYPE_LRU_HASH`** | Hashmap with LRU eviction; useful for connection tracking |
| **`BPF_MAP_TYPE_RINGBUF`** | Multi-producer single-consumer ring buffer for streaming events to userspace |
| **`BPF_MAP_TYPE_QUEUE`** / **`STACK`** | FIFO/LIFO data structures |
| **`BPF_MAP_TYPE_BLOOM_FILTER`** | Probabilistic membership testing |
| **`BPF_MAP_TYPE_STACK_TRACE`** | Capture and store kernel/userspace stack traces |
| **`BPF_MAP_TYPE_PROG_ARRAY`** | Array of program fds, used for tail calls |
| **`BPF_MAP_TYPE_SOCKHASH`** / **`SOCKMAP`** | Socket-keyed maps for socket redirection |
| **`BPF_MAP_TYPE_DEVMAP`** / **`CPUMAP`** | Per-device or per-CPU redirection targets for XDP |
| **`BPF_MAP_TYPE_TASK_STORAGE`** / **`SK_STORAGE`** / **`INODE_STORAGE`** / **`CGROUP_STORAGE`** | Per-object storage attached to a kernel object's lifetime |
| **`BPF_MAP_TYPE_ARENA`** | Shared memory region between BPF and userspace (kernel 6.9+) |

Map operations from BPF programs are bounded-time and lock-free where possible (per-CPU maps), or use kernel locking primitives (hash maps, queues).

## BPF ringbuf

The ring buffer (`BPF_MAP_TYPE_RINGBUF`) is the standard mechanism for streaming events from BPF programs to userspace. It supports:

- Multi-producer (multiple programs/CPUs writing concurrently)
- Single-consumer (one userspace reader per ring)
- Reservation API (`bpf_ringbuf_reserve` / `bpf_ringbuf_submit`) for zero-copy event construction
- Backpressure when full (programs detect and skip rather than block)

Ring buffers are how BPF programs send notification streams to userspace without the syscall overhead of perf events. For Peios subsystems that need authoritative event delivery (KMES origin classes), see [Peios integration](peios-integration) — programs can route through `bpf_kmes_emit` to surface events into the standard Peios event pipeline rather than a private ring buffer.

## BPF arena

As of kernel 6.9, **BPF arena** (`BPF_MAP_TYPE_ARENA`) provides a shared memory region between BPF programs and userspace. Userspace `mmap`s the arena; BPF programs access it through the same virtual addresses. This is useful for large shared data structures that don't fit map semantics — graphs, dynamic-size buffers, etc.

The verifier ensures BPF accesses to the arena stay within the arena's bounds. Arena memory is not paged out, and the maximum arena size is bounded.

## BPF timers

BPF programs can register **timers** that invoke a callback after a delay (`bpf_timer_init`, `bpf_timer_set_callback`, `bpf_timer_start`). Timer callbacks are themselves BPF programs (subprograms of the parent). This is how a program can defer work or implement periodic behaviour without an external trigger.

As of kernel 6.18, the **`bpf_task_work` interface** provides deferred execution in task context (rather than softirq context), which is useful for callbacks that need a sleepable execution environment.

## BPF spin locks

The verifier permits a small `bpf_spin_lock` primitive that programs can use to synchronize access to map values. Locks are tied to a map element and acquired/released via `bpf_spin_lock` / `bpf_spin_unlock` helpers. The verifier statically validates lock/unlock pairing.

For more complex synchronization, see [The verifier](the-verifier) on resilient queued spinlocks.

## Helpers

A **helper** is a kernel function exposed to BPF programs through a stable numeric ID. The verifier checks that a program only calls helpers permitted for its program type. Common helpers:

| Helper | Purpose |
|---|---|
| `bpf_map_lookup_elem` / `bpf_map_update_elem` / `bpf_map_delete_elem` | Map access |
| `bpf_get_current_pid_tgid` | Calling task's pid/tgid |
| `bpf_get_current_uid_gid` | Calling task's uid/gid (Linux compat — see [Peios integration](peios-integration) for Peios-native identity helpers) |
| `bpf_ktime_get_ns` | Monotonic time in nanoseconds |
| `bpf_probe_read_kernel` / `bpf_probe_read_user` | Safe arbitrary memory read |
| `bpf_trace_printk` | Log a message to the trace buffer |
| `bpf_perf_event_output` | Submit an event to a perf event ring |
| `bpf_ringbuf_reserve` / `bpf_ringbuf_submit` | Ring buffer event submission |

Helpers are stable kernel ABI — once exposed at a numeric ID, the kernel honours that ABI. New helpers are added; existing ones are not removed.

## kfuncs

A **kfunc** is a kernel function exposed to BPF programs by name (rather than numeric ID), with type information from BTF. kfuncs are the modern preferred mechanism for new BPF-callable APIs because:

- Type-safe (the verifier uses BTF to check arguments and return types)
- Easier to add (no new helper ID required)
- Can be marked `__sleepable`, `__must_check`, etc. with semantic effects on the verifier
- Versioned per-subsystem rather than as a single helper namespace

Recent kfunc additions:

| kfunc | Purpose |
|---|---|
| `bpf_dynptr_memset` (6.17) | Initialize a dynamic pointer's region |
| `bpf_strcasecmp` / `bpf_strncasecmp` (6.18 / 7.0) | Case-insensitive string comparison |
| `bpf_cgroup_read_xattr` (6.17) | Read extended attributes on a cgroup |
| `bpf_local_irq_save` / `bpf_local_irq_restore` (6.14) | IRQ state management for programs that need uninterrupted critical sections |
| `bpf_stream_print_stack` (7.0) | Stack dumping into a BPF stream |

Peios-native kfuncs live under prefixes that identify their subsystem (`bpf_kacs_*`, `bpf_lcs_*`, `bpf_kmes_*`, `bpf_process_*`). See [Peios integration](peios-integration).

## BPF I/O streams

As of kernel 6.17, BPF programs can write to **standard I/O streams** (BPF stdout/stderr) that surface to userspace through bpffs. This is a more structured replacement for `bpf_trace_printk` for diagnostic output.

## BPF iterators

A BPF iterator is a program type that walks a kernel data structure (tasks, sockets, cgroups, kernel symbols) and emits records to userspace. Userspace opens an iterator's file descriptor and reads sequential records. Iterators are how programs surface kernel state to userspace without syscall-by-syscall enumeration. As of kernel 7.0, `BPF_CGROUP_ITER_CHILDREN` iterates a cgroup's immediate children.

## BPF map cookies

As of kernel 6.17, maps can carry a **cookie** — an opaque identifier the kernel assigns at map creation. Cookies let userspace identify maps across operations without relying on file descriptors, useful for attaching metadata to maps in tooling.

## Memory accounting and program lifecycle

Programs and maps consume kernel memory; this memory is accounted to the loading process's cgroup (memcg) as of kernel 6.17. When the cgroup hits its memory limit, BPF program loads in that cgroup fail with `ENOMEM`. This makes BPF resource usage visible in standard cgroup accounting.

## Per-CPU map access flags

As of kernel 7.0, `bpf_f_cpu` and `bpf_f_all_cpus` flags on per-CPU map operations let userspace target a specific CPU's value or read/write all CPUs' values atomically — refining the per-CPU map access patterns that previously required separate syscalls per CPU.

## RB-tree and list helpers

BPF programs can use kernel-style red-black trees and intrusive lists through dedicated helpers. As of kernel 6.16, programs can **traverse** RB-trees and **peek** at lists in addition to inserting/removing.

## See also

- [The verifier](the-verifier) — how the verifier validates map and helper accesses.
- [Peios integration](peios-integration) — Peios-native helpers and kfuncs (`bpf_kacs_*`, `bpf_lcs_*`, `bpf_kmes_*`, `bpf_process_*`).
- [Privileges and trust](privileges-and-trust) — bpffs, BPF tokens, the persistence model.
