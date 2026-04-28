---
title: Controller Reference
type: reference
description: Exhaustive per-controller listing of every cgroup knob shipped on Peios — control files, counter files, and per-controller event interfaces. Covers cpu, memory, io, pids, cpuset, freezer, hugetlb, device, rdma, and misc.
related:
  - peios/resource-management/understanding-cgroups
  - peios/resource-management/working-with-cgroups
  - peios/resource-management/pressure-stall-information
---

This page enumerates every control and counter file each cgroup controller exposes. It complements [Understanding cgroups](understanding-cgroups), which describes the conceptual model, and [Working with cgroups](working-with-cgroups), which walks through common operations.

Every file has a Security Descriptor inherited from its parent cgroup directory. Reading a counter file requires `FILE_READ_DATA`; writing a control file requires `FILE_WRITE_DATA`. The files listed below all follow this rule unless explicitly noted.

## Common cgroup files

These files exist in every cgroup, regardless of which controllers are enabled.

| File | Type | Description |
|---|---|---|
| `cgroup.procs` | RW | Newline-separated list of PIDs in this cgroup. Writing a PID migrates that process here. Subject to the dual `FILE_WRITE_DATA` + `PROCESS_SET_QUOTA` check. |
| `cgroup.threads` | RW | TIDs in this cgroup, for threaded mode. Same dual check on writes (`PROCESS_SET_QUOTA` is on the owning process). |
| `cgroup.type` | RW | `domain` (standard) or `threaded` (threaded mode). Writing `threaded` switches the cgroup to threaded mode. |
| `cgroup.controllers` | RO | Space-separated list of controllers available in this cgroup (inherited from parent's `subtree_control`). |
| `cgroup.subtree_control` | RW | Space-separated list of controllers enabled for children. Writes use `+name` / `-name` syntax. |
| `cgroup.events` | RO | Key-value file with event flags. `populated 0/1` indicates whether the cgroup or any descendant contains processes. `frozen 0/1` indicates the cgroup's freeze state. Userspace tools `inotify`-watch this file for state changes. |
| `cgroup.stat` | RO | `nr_descendants` and `nr_dying_descendants` — counts of child cgroups. |
| `cgroup.freeze` | RW | Write `1` to freeze all processes in this cgroup; `0` to thaw. The frozen state is reflected in `cgroup.events`. |
| `cgroup.kill` | WO | Write `1` to send `SIGKILL` to every process in this cgroup atomically. |
| `cgroup.max.depth` | RW | Per-subtree override of maximum tree depth from this cgroup downward. Default inherited from `\System\Cgroups\DefaultMaxDepth`. Writing `max` removes the per-subtree override. |
| `cgroup.max.descendants` | RW | Per-subtree override of maximum descendants under this cgroup. Default inherited from `\System\Cgroups\DefaultMaxDescendants`. |
| `cgroup.pressure` | RW | Per-cgroup PSI enable/disable knob. Writing `0` disables PSI accounting for this cgroup (saving overhead); `1` re-enables. See [Pressure Stall Information](pressure-stall-information). |

## CPU controller (`cpu`)

Manages CPU bandwidth, weight, and scheduling-related hints.

### Control files

| File | Description |
|---|---|
| `cpu.weight` | Proportional CPU share, range `1-10000`, default `100`. Higher means more CPU when contended. |
| `cpu.weight.nice` | Nice-value-based weight (range `-20` to `19`). Sets `cpu.weight` to a value derived from the nice value. The two files are aliases — writing one updates the other. |
| `cpu.max` | Bandwidth limit, format `<quota> <period>` in microseconds. `max 100000` means unlimited; `200000 100000` means 2 CPUs of bandwidth per 100ms period. |
| `cpu.max.burst` | Maximum burst above quota, in microseconds. Allows transient spikes beyond `cpu.max`'s quota without throttling. Default `0` (no burst). |
| `cpu.uclamp.min` | Utilization clamp minimum, percentage `0` to `100`. The scheduler treats the cgroup's tasks as if they need at least this much utilization (drives frequency scaling). |
| `cpu.uclamp.max` | Utilization clamp maximum. Caps the perceived utilization, useful for preventing low-priority work from driving the CPU to high frequencies. |
| `cpu.idle` | Idle priority hint, `0` (normal) or `1` (idle). Idle cgroups only run when no other cgroup wants the CPU. Useful for batch / background workloads. |

### Counter files

| File | Description |
|---|---|
| `cpu.stat` | Aggregate usage. Fields: `usage_usec`, `user_usec`, `system_usec`, `nr_periods`, `nr_throttled`, `throttled_usec`, `nr_bursts`, `burst_usec`. |
| `cpu.pressure` | PSI metrics for CPU pressure (see [Pressure Stall Information](pressure-stall-information)). |
| `cpu.stat.local` | Per-CPU local stats (when available). |

## Memory controller (`memory`)

Manages memory limits, soft targets, swap, and accounting. See also [Memory management](../memory-management/memory-mapping) for the lower-level model.

### Control files

| File | Description |
|---|---|
| `memory.max` | Hard memory limit. Allocations beyond this trigger reclaim, then OOM-kill if reclaim fails. `max` means no limit. |
| `memory.high` | Soft target — when usage exceeds `high`, the kernel applies aggressive reclaim and throttles the cgroup's allocators to reduce growth. Stays below `max` if possible. |
| `memory.low` | Soft minimum — memory below this is protected from reclaim by other cgroups, best-effort. |
| `memory.min` | Hard minimum — memory below this is unconditionally protected. The protection counts against the parent's `memory.min` budget. |
| `memory.swap.max` | Maximum swap usage. `max` means unlimited (subject to system swap availability). |
| `memory.swap.high` | Swap soft target — throttle when exceeded. |
| `memory.zswap.max` | Maximum zswap (compressed swap) usage. |
| `memory.oom.group` | Write `1` to make this cgroup an OOM-kill unit — the kernel kills every process in the cgroup together when OOM-killing, rather than picking individual victims. Useful for workloads where killing one member of a group makes the rest useless. |
| `memory.reclaim` | Trigger immediate reclaim. Write a number of bytes to attempt to reclaim. |

### Counter and event files

| File | Description |
|---|---|
| `memory.current` | Current memory usage in bytes. |
| `memory.peak` | Peak memory usage observed in this cgroup's lifetime. |
| `memory.swap.current` / `memory.swap.peak` | Current and peak swap. |
| `memory.zswap.current` | Current zswap. |
| `memory.stat` | Detailed breakdown — anon, file, kernel, sock, slab, percpu, vmalloc, etc. Multi-line key-value format. |
| `memory.events` | Event counters: `low`, `high`, `max`, `oom`, `oom_kill`, `oom_group_kill`. Each is the count of times that event occurred. `inotify`-watchable. |
| `memory.events.local` | Like `memory.events` but only counts events for this cgroup's direct members, not descendants. |
| `memory.numa_stat` | Per-NUMA-node memory accounting. |
| `memory.pressure` | PSI metrics for memory pressure. |

## IO controller (`io`)

Manages block IO bandwidth, IOPS, latency, and scheduling per device. The controller is per-block-device — each line in a control file targets one device by major:minor.

### Control files

| File | Description |
|---|---|
| `io.weight` | Default proportional weight (range `1-10000`, default `100`) and per-device overrides. Format: `default 100\n8:0 200`. |
| `io.max` | Per-device bandwidth and IOPS caps. Format: `<major>:<minor> rbps=<n> wbps=<n> riops=<n> wiops=<n>`. Use `max` to remove a cap. |
| `io.latency` | Per-device latency target, in microseconds. The cgroup is treated as priority traffic; cgroups with no `io.latency` may be throttled to keep this cgroup's reads under the target. |
| `io.cost.qos` | Cost-based controller QoS parameters (when `io.cost.model` is enabled): per-device latency targets and target percentiles. |
| `io.cost.model` | Cost-based controller model parameters: device characteristics for the cost calculator. The cost-based controller is an alternative to weight-based scheduling that aims for predictable latency under contention. |
| `io.prio.class` | IO priority class for this cgroup (`promote`, `restrict`, etc.). Translates to `ioprio_set`-style priorities. |
| `io.bfq.weight` | (When BFQ scheduler is in use) BFQ-specific weight. |

### Counter files

| File | Description |
|---|---|
| `io.stat` | Per-device statistics. Fields: `rbytes`, `wbytes`, `rios`, `wios`, `dbytes`, `dios`. |
| `io.pressure` | PSI metrics for IO pressure. |

## PID controller (`pids`)

Bounds the number of processes a cgroup may have. Tiny but essential — without it, a fork-bomb in any cgroup can exhaust the system's PID space.

| File | Description |
|---|---|
| `pids.max` | Maximum number of PIDs (processes + kernel threads) in this cgroup. `max` means unlimited (subject to the system PID space). |
| `pids.current` | Current PID count. |
| `pids.peak` | Peak PID count observed. |
| `pids.events` | Event counter: `max` increments each time a fork was rejected because `pids.max` was reached. |

## cpuset controller (`cpuset`)

Pins a cgroup's tasks to specific CPUs and NUMA memory nodes. Used for performance isolation, real-time, and dedicated-core workloads.

### Control files

| File | Description |
|---|---|
| `cpuset.cpus` | Comma-separated list of CPU ranges (e.g., `0-3,8-11`) on which this cgroup's tasks may run. Empty means inherit from parent. |
| `cpuset.mems` | Comma-separated list of NUMA node ranges from which this cgroup may allocate memory. |
| `cpuset.cpus.exclusive` | A subset of `cpuset.cpus` that is exclusively this cgroup's — siblings cannot include these CPUs in their own `cpuset.cpus`. |
| `cpuset.cpus.partition` | Partition type. `member` (the default — share with siblings), `root` (start an exclusive partition rooted here), `isolated` (root partition with kernel housekeeping moved off these CPUs — for real-time / latency-critical workloads). |

### Counter files

| File | Description |
|---|---|
| `cpuset.cpus.effective` | The actual CPU set the cgroup's tasks are running on, after taking into account the parent's effective set, hot-plugged-out CPUs, etc. Read-only. |
| `cpuset.mems.effective` | The actual NUMA node set, after parent constraints and node hot-plug. |
| `cpuset.cpus.exclusive.effective` | The actual exclusive CPU set after partition resolution. |

## Freezer

The freezer functionality is provided by the common `cgroup.freeze` and `cgroup.events` files (see Common cgroup files above). There is no separate freezer controller in v2 — `cgroup.freeze` works in any cgroup.

The `cgroup.events` file's `frozen` field reflects the freeze state:

```
$ cat /sys/fs/cgroup/services/jellyfin/cgroup.events
populated 1
frozen 0
```

Userspace tools that need to track freeze state asynchronously `inotify`-watch `cgroup.events` for modify events.

## hugetlb controller

Bounds hugetlb-backed memory per page size. See [Memory management — Huge pages](../memory-management/huge-pages) for the broader hugetlb context.

The controller has one file per supported page size, named with the page size in suffix form:

| File | Description |
|---|---|
| `hugetlb.<size>.max` | Maximum hugetlb-backed memory at this page size. e.g., `hugetlb.2MB.max`, `hugetlb.1GB.max`. |
| `hugetlb.<size>.current` | Current usage. |
| `hugetlb.<size>.events` | Event counter: `max` increments when a hugetlb allocation was denied due to the limit. |
| `hugetlb.<size>.rsvd.max` | Reservation limit (memory reserved at mmap time, before fault). |
| `hugetlb.<size>.rsvd.current` | Current reservation usage. |

THP (transparent huge pages) is bounded by the regular memory controller, not this controller.

## Device controller

The device controller is the only controller whose decisions are made by attached eBPF programs rather than by reading control files. It is configured by attaching a BPF program of type `BPF_PROG_TYPE_CGROUP_DEVICE` to the cgroup; the program is consulted on every `open()` of a device file by a process in the cgroup.

The BPF program receives:

- **Type** — character device or block device
- **Major:minor** — the device numbers
- **Operation** — read (`BPF_DEVCG_ACC_READ`), write (`BPF_DEVCG_ACC_WRITE`), or mknod (`BPF_DEVCG_ACC_MKNOD`)

It returns `0` (deny) or `1` (allow). The kernel intersects this with the result of the standard KACS DACL check on the device file — both must allow.

Operations on the controller (attaching / detaching BPF programs) are not done via cgroupfs files; they go through `bpf(BPF_PROG_ATTACH, ...)` syscalls. Loading and attaching a BPF program requires the `SeLoadDriverPrivilege` (or the eBPF-specific privilege when introduced).

## RDMA controller

Bounds RDMA resources (verbs objects, queue pairs) per cgroup. Applies only to InfiniBand / RoCE workloads.

| File | Description |
|---|---|
| `rdma.max` | Per-device limits, format `<dev_name> hca_handle=<n> hca_object=<n>`. Limits the number of RDMA HCA handles and objects this cgroup may consume. |
| `rdma.current` | Current usage per device. |

The list of devices is determined by which RDMA hardware is present; tooling can query supported device names from the kernel.

## misc controller

Generic scalar resource limiter — drivers register named scalar resources, and the controller bounds per-cgroup consumption of each. Used by drivers that need per-cgroup quotas for resources outside the standard controller set (e.g., NVIDIA's confidential-computing ASID controller).

| File | Description |
|---|---|
| `misc.max` | Per-resource limits, one line per registered resource. Format: `<resource_name> <limit>`. |
| `misc.current` | Current usage per resource. |
| `misc.events` | Per-resource event counters: `max` increments when an allocation was denied. |
| `misc.capacity` | (root cgroup only) System-wide capacity per registered resource. |

The set of resources available depends on which drivers have registered them; an empty set is normal on systems without drivers that use this controller.

## Per-controller controllers reference summary

The set of controllers available in any cgroup is in `cgroup.controllers`. The set enabled for children is in `cgroup.subtree_control`. Standard controller short names:

| Short name | Controller |
|---|---|
| `cpu` | CPU bandwidth, weight, uclamp, idle |
| `memory` | Memory limits, soft targets, accounting |
| `io` | Block IO weight, bandwidth, IOPS, latency |
| `pids` | Process count limit |
| `cpuset` | CPU and NUMA pinning |
| `hugetlb` | Hugetlb-backed memory limits |
| `rdma` | RDMA resource limits |
| `misc` | Generic scalar resources (driver-registered) |

The freezer and PSI mechanisms are not controllers in this sense — they apply to all cgroups regardless of `subtree_control`.

The device cgroup is not enabled or disabled via `subtree_control` either; it is configured per-cgroup by attaching BPF programs and is unconditionally consulted on device opens for that cgroup.
