---
title: CPU Affinity and Isolation
type: concept
description: How threads are pinned to specific CPUs, how CPUs are reserved at boot for latency-sensitive workloads, and how the per-thread, cgroup, and boot-time mechanisms compose.
related:
  - peios/process-management/understanding-scheduling
  - peios/process-management/understanding-the-thread-model
---

Two things shape which CPU a thread runs on. **Affinity** is the per-thread mask of which CPUs the scheduler is allowed to consider — set at runtime, narrowable, can change as the process runs. **Isolation** is a system-wide reservation of certain CPUs, made at boot, that excludes them from the kernel's normal balancing and (optionally) from the scheduler's tick interrupts. The two compose: affinity controls which CPUs an individual thread can run on; isolation controls which CPUs the system at large will run general work on.

This page covers both, the privilege model around them, and how cgroup-based cpuset assignment fits in.

## Affinity

Every thread carries a **CPU mask** — a bitmap of the logical CPUs it is allowed to run on. By default the mask covers all CPUs the system has. The scheduler, when picking a CPU for the thread, considers only CPUs set in the mask.

Affinity is per-thread, not per-process. A multi-threaded service can pin one thread to CPU 0, another to CPUs 1–3, and let the rest run anywhere. Threads created by `clone()` inherit the creator's affinity at creation time but can change it independently afterwards.

The syscalls are:

| Syscall | Use |
|---|---|
| `sched_setaffinity(pid, size, mask)` | Set the affinity mask for a thread. `pid = 0` targets the calling thread. |
| `sched_getaffinity(pid, size, mask)` | Read the current affinity mask for a thread. |

### Privilege model

A thread can change its **own** affinity to any subset of the CPUs it is currently allowed to run on, without privilege. "Currently allowed" means the intersection of:

- The thread's existing mask
- The cpuset of the cgroup the thread belongs to (see below)
- The set of non-isolated CPUs, except where the thread has been explicitly granted access to isolated ones

Going **outside the currently-allowed set** — for example, setting an affinity that includes a CPU the cgroup's cpuset does not — is rejected by the kernel regardless of privilege; cpuset narrowing is hard-enforced.

Setting affinity for **another thread** requires either being in the same process (threads can re-pin their siblings) or holding `SeIncreaseBasePriorityPrivilege` — the same umbrella that gates priority elevation. The scheduling subsystem treats "where can this thread run" and "how high a priority can it have" as the same kind of authority.

### What affinity does not do

Pinning a thread to a CPU does not give the thread exclusive use of that CPU. Other threads can still be scheduled there unless those threads are themselves pinned away or unless the CPU is isolated (next section). Affinity narrows the scheduler's options for the thread; it does not reserve the CPU for the thread.

## CPU isolation

Some workloads need a CPU that the kernel will not interrupt with bookkeeping work or with other threads stealing time. The Linux substrate provides two boot-time mechanisms:

| Parameter | What it does |
|---|---|
| `isolcpus=N,M` | Removes the listed CPUs from the kernel's normal load-balancing and IRQ routing. Threads that don't explicitly pin to those CPUs won't run on them. |
| `nohz_full=N,M` | Disables the periodic scheduler tick on the listed CPUs while only one thread is runnable on the CPU. Eliminates the per-millisecond tick interrupt that otherwise jitters latency-sensitive workloads. |

Both are kernel command-line parameters, interpreted before any userspace exists. They cannot be changed at runtime, only at boot.

Peios treats them as **image-time configuration** — set in the bootloader configuration that an image is built with, not via the registry. The registry's `ksyncd` machinery does not manage these because there is nothing for it to do once the kernel has parsed them. Changing isolation requires a reboot with a different command line.

A typical reservation of CPUs 4–7 on an 8-core system for low-latency workloads:

```
isolcpus=4-7 nohz_full=4-7 rcu_nocbs=4-7
```

The `rcu_nocbs=` companion moves RCU callback work off the isolated cores, completing the picture. Without it, the isolated CPUs would still run RCU callback work on behalf of the rest of the system.

## Composing affinity with isolation

Isolated CPUs are not used by default. A latency-sensitive service that wants to use the isolated set must explicitly pin its threads there with `sched_setaffinity`. Threads not pinned to isolated CPUs will not run on them; threads pinned there will not be moved off by the load balancer.

The composition is straightforward:

1. **Boot with `isolcpus=4-7`.** General work runs on CPUs 0–3.
2. **The latency-sensitive service starts.** Its threads inherit the all-CPUs mask but the kernel won't schedule them onto isolated CPUs spontaneously.
3. **The service narrows its threads to CPUs 4–7.** Now those threads run only on the reserved CPUs, with no competition from general work.

For maximum effect, combine with `SCHED_FIFO` or `SCHED_DEADLINE` for the threads in question — the scheduling class controls *when* they run, the affinity controls *where*, and the isolation ensures *who else doesn't*.

## cgroup-based cpusets

The substrate also offers cgroup v2 **cpusets** — a hierarchical, supervised mechanism for assigning subsets of CPUs to groups of processes. Cpusets layer on top of per-thread affinity: a thread's effective allowed CPUs are the intersection of its own affinity mask and the cpuset of the cgroup it belongs to.

| Cpuset property | Purpose |
|---|---|
| `cpuset.cpus` | The set of CPUs available to processes in this cgroup. |
| `cpuset.mems` | The set of NUMA memory nodes available — restricts allocations. |
| `cpuset.cpus.partition` | Marks a cpuset as an **exclusive partition** — the listed CPUs are removed from the parent cpuset's effective set. |

Cpusets are useful for declaring "this service tree gets CPUs 8–15" without each process inside the tree having to know that. The cgroup hierarchy provides a single point of policy.

The full cgroup model — how groups are created, how processes are placed, how the SD on the cgroup hierarchy gates membership management — is covered alongside the rest of resource control. From the affinity perspective, the rule is: **cpusets narrow, never widen**. A cgroup's cpuset cannot widen a thread's mask beyond what isolation has reserved unless the partition explicitly includes the isolated CPUs.

## NUMA awareness

On NUMA systems (multiple CPU sockets, each with their own attached memory), affinity has a memory dimension as well. A thread pinned to CPU 0 ideally allocates memory from CPU 0's local NUMA node, where access is faster than reaching across the socket interconnect.

The scheduler is NUMA-aware: it prefers to run a thread on a CPU near the memory it is using, and the page allocator prefers to allocate from the local node. These behaviours are automatic and require no application configuration.

For workloads that need explicit control, `set_mempolicy()`, `mbind()`, and the `numactl` tooling expose NUMA placement at the syscall level. Cpuset's `cpuset.mems` provides the cgroup-based equivalent.

## CPU topology

The kernel exposes scheduling-relevant CPU topology under `/sys/devices/system/cpu/`:

| Path | Information |
|---|---|
| `cpuN/topology/thread_siblings` | The set of CPUs that are SMT siblings of CPU N (same physical core). |
| `cpuN/topology/core_siblings` | The set of CPUs in the same package as CPU N. |
| `cpuN/topology/physical_package_id` | The package (socket) CPU N belongs to. |
| `cpuN/topology/core_id` | The physical core within the package. |

The scheduler uses this topology to make better placement decisions — preferring to keep work on the same package, distributing across SMT siblings only when needed, and so on. Affinity decisions can use the same information to express things like "pin this thread to one CPU per physical core, not per SMT sibling," which matters for workloads that do not benefit from SMT or actively want to avoid sharing core resources with other threads.

## Summary

The pieces fit together in a hierarchy:

1. **Boot-time isolation** decides which CPUs are reserved for opt-in latency-sensitive workloads. Image-time configuration, no runtime change.
2. **cgroup cpusets** carve the non-isolated set into named groups for service trees.
3. **Per-thread affinity** is the finest grain — a thread's actual allowed set is the intersection of its mask, its cgroup's cpuset, and (for isolated CPUs) explicit pinning.
4. **Scheduling class and priority** then decide *when* the thread runs on its allowed CPUs.

This composition handles the spectrum from default-everything-shared to dedicated-CPU latency-sensitive isolation through a small number of orthogonal mechanisms.
