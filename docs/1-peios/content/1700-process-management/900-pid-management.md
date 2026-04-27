---
title: PID Management
type: concept
description: How processes are numbered, how the PID space is sized, what makes PID 1 special, and how PID namespaces fit into the larger containerisation story.
related:
  - peios/process-management/understanding-process-creation
  - peios/process-management/process-lifecycle
  - peios/process-management/understanding-the-thread-model
---

A **PID** (Process ID) is a small integer the kernel assigns to each process when it is created. PIDs are the traditional Unix handle for naming a process — used by `kill`, `ps`, `/proc/<pid>/`, and most legacy diagnostic tooling. They are short-lived, reusable, and exist in a flat namespace within their PID namespace.

Peios uses PIDs from the substrate unchanged. The Peios-native identifier for a process is the **process GUID**, not the PID — see [Understanding the Thread Model](understanding-the-thread-model) for the distinction. PIDs continue to exist for Linux compatibility, for tools that expect them, and as the index into `/proc`. They are not the authoritative identity of a process.

## PID allocation

The kernel maintains a per-PID-namespace allocator that hands out the next available PID when a process is created. The strategy is a **linear scan with wrap-around**: starting from the most recently allocated PID, the kernel walks forward looking for an unused number. When it reaches `pid_max`, it wraps back to a small starting value and continues.

The wrap-around behaviour is the source of PID reuse. A given integer like 12345 may name one process today, get freed when that process is reaped, and name a different process tomorrow. This is why **pidfds are preferred over PIDs for any code that needs a stable handle to a specific process**: a pidfd refers to a single process for the entire lifetime of the pidfd, regardless of PID reuse, and goes through the kernel's existing AccessCheck on the target's process SD when first issued. See [Process Lifecycle](process-lifecycle) for the pidfd model.

## `pid_max`

The maximum PID value is configurable via the `kernel.pid_max` sysctl. Larger values reduce wrap-around frequency (and thus reuse races) at the cost of slightly larger per-process kernel data structures. The default is the kernel's compile-time default, which is large enough for most workloads.

Peios manages `pid_max` via the registry under `\System\Process\PidMax`. The registry value is applied to the running kernel by `ksyncd` at boot and on subsequent registry changes — the same pattern used for other kernel-tunable sysctls. Tuning `pid_max` is rarely necessary; the default is correct for the vast majority of systems.

## PID 1

The first userspace process to start has special status. By convention and by kernel mechanism, PID 1 is **peinit** — the supervisor process that the kernel exec's into during boot.

Three properties make PID 1 different from any other process:

- **Signal protection.** The kernel refuses to deliver `SIGKILL` to PID 1 within its own PID namespace. PID 1 cannot be terminated by an unhandled fatal signal, because the kernel will not send unsolicited fatal signals to it; PID 1 can only exit if it explicitly chooses to. This is the substrate's defence against accidentally killing init.
- **Orphan reaping.** When any process exits before its children, those children are reparented to the nearest still-living subreaper or, failing that, to PID 1. peinit is structurally guaranteed to wait for any orphan that lands on it, so the system never accumulates zombies regardless of how careless individual parents are. See [Process Lifecycle](process-lifecycle) for the full reparenting and subreaper model.
- **Signal handler defaults.** Signals without explicit handlers installed on PID 1 are silently dropped, rather than triggering the default action. peinit installs handlers for the signals it cares about — `SIGTERM` for graceful shutdown, `SIGCHLD` for reaping — and ignores everything else by default.

Together these properties give peinit the resilience needed to be the system's last-resort supervisor. A misbehaving service cannot kill peinit, cannot block its reaping role, and cannot accumulate zombies that would eventually exhaust the PID space.

## PID namespaces

A **PID namespace** is a kernel-level isolation primitive that gives a subset of processes their own private PID number space. Inside the namespace, processes see numbered PIDs starting from 1; the process that becomes PID 1 within a child namespace inherits the same signal protection and reaping guarantees that peinit has in the root namespace.

Peios uses Linux PID namespaces approximately as the substrate provides them — they are the primitive on which any container or sandbox functionality is built. The full model, including how PID namespaces compose with the other seven Linux namespace types (mount, net, UTS, IPC, user, cgroup, time), the KACS confinement mechanism, and any container-runtime story, is covered in the **Containerisation** category, not here. PID namespaces from the perspective of process management are: a PID is meaningful only within its namespace, and PID 1 within a child namespace plays the same role peinit plays in the root.

A few namespace-related details worth knowing in passing:

- **PID translation across namespace boundaries.** A process in a parent namespace can see processes in child namespaces under translated PIDs (the parent's view assigns its own numbers). A process in a child namespace cannot see, signal, or otherwise reference processes outside its namespace.
- **`CLONE_NEWPID`** is the flag passed to `clone()` to create a new PID namespace. The newly-cloned process becomes PID 1 in the new namespace.
- **`/proc/<pid>/ns/pid`** is the namespace handle file. Holding a reference to it keeps the namespace alive.

For PID-management purposes that is all that's relevant. The container-shaped story belongs with the rest of the namespace primitives.

## `/proc/sys/kernel/ns_last_pid`

Container runtimes occasionally need to control which PID will be assigned to the next process — for deterministic numbering across restarts, or to recreate a specific process tree's identifiers. The `ns_last_pid` sysctl exposes the allocator's "last assigned PID" cursor for the namespace it is read from; writing it forces the next allocation to start scanning from the written value.

Writing `ns_last_pid` is gated on `SeTcbPrivilege` (mapped from Linux's `CAP_SYS_ADMIN`). This is because ns_last_pid lets a privileged caller manipulate which PIDs subsequent processes will receive, which is a system-state change the unprivileged process should not be making. Reading is unprivileged within the namespace.

This sysctl is rarely useful outside of container-runtime internals. Most code should never touch it.
