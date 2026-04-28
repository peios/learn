---
title: Understanding cgroups
type: concept
description: cgroups are the kernel primitive for bounding and accounting a group of processes' resource consumption — CPU, memory, IO, PIDs, and more. Each cgroup is a node in a hierarchical pseudo-filesystem; access to set limits and attach processes is gated by the standard KACS DACL on each node.
related:
  - peios/process-silos/understanding-process-silos
  - peios/access-control/how-accesscheck-works
  - peios/process-management/processes
---

A **cgroup** (control group) is a kernel primitive for bounding and accounting the resource consumption of a group of processes. A cgroup gives the kernel a name to attach limits and counters to: how much CPU these processes may use, how much memory they may allocate, how many file-backed I/O bytes they may issue, how many processes they may fork. Pressure metrics, freeze/thaw operations, and bulk kill are also addressed at the cgroup.

cgroups are a **resource boundary**, not an identity boundary. They have no SID and do not appear in DACLs as principals. They are securable — each cgroup is a node in a pseudo-filesystem and has a Security Descriptor controlling who can change its limits and attach processes — but they do not participate in AccessCheck for non-cgroup objects.

## Why cgroups exist

Workload isolation requires more than a name and a private view of the system. A noisy service on a multi-tenant host can consume all available CPU or memory and starve every other workload, regardless of identity-based separation. A runaway process can fork-bomb the system. A storage backend without I/O limits can saturate a disk and degrade every other service sharing it.

[Process Silos](../process-silos/understanding-process-silos) deliberately do not bound resources — they provide identity and visibility, no more. cgroups are the complementary primitive: they bound and account for resource consumption. A typical workload-isolation pattern composes a silo (identity, visibility) with a cgroup (bounds, accounting).

The pattern that emerges in most server deployments is:

- **peinit** places each service in its own cgroup so resource limits, accounting, and lifecycle operations (freeze, kill, restart) are addressable per service.
- **Container runtimes** create one cgroup per container so the container's CPU/memory/IO budget is enforceable.
- **Monitoring and autoscaling** read cgroup pressure stall metrics and accounting counters to make scaling decisions.

End-user applications rarely interact with cgroups directly. The audience is supervisory layers: init systems, container runtimes, monitoring agents, and self-introspecting runtimes (databases, JVMs) that read their own limits to size internal resources correctly.

## What a cgroup is

A cgroup is a **directory** in a pseudo-filesystem mounted at `/sys/fs/cgroup`. Each directory:

- Contains files that expose the cgroup's controls (`cpu.max`, `memory.max`, `io.weight`) and counters (`cpu.stat`, `memory.current`, `cpu.pressure`).
- Contains a `cgroup.procs` file listing the processes currently in this cgroup; writing a PID to it migrates that process into the cgroup.
- Has a Security Descriptor controlling who can read counters, write limits, and attach processes.
- May contain child cgroup directories, forming a tree.

Creating a cgroup is `mkdir`. Removing one is `rmdir`. Setting a limit is `echo 100000 > cpu.max`. Reading usage is `cat cpu.stat`. The whole control surface is filesystem operations.

## The unified hierarchy

cgroups form a single tree rooted at `/sys/fs/cgroup`. Every process is in exactly one cgroup. Processes inherit their parent's cgroup at fork; they remain in that cgroup until explicitly migrated.

A child cgroup's effective limits are the **intersection** of its own limits and every ancestor's limits up to the root. A child cannot grant itself more than its parent allows. This means delegating a subtree to a less-privileged owner is safe: the owner can carve up their allotment among children but cannot expand it.

Each cgroup has a set of **enabled controllers** — which resource types this subtree manages. The root cgroup enables a default set; intermediate cgroups can disable controllers they don't need. A controller cannot be enabled in a child if its parent has not enabled it.

### The no-internal-process constraint

Processes can only live in **leaf cgroups** — cgroups with no children that have controllers enabled. An interior node holds child cgroups, not processes. This constraint exists because resource accounting becomes ambiguous if processes live alongside child cgroups (which sub-budget gets charged?).

The **threaded mode** exception lets a cgroup's threads be split across child cgroups while the cgroup itself still appears to hold them collectively. Threaded mode is uncommon — most workloads use the standard domain mode.

## Access control: DACLs on the pseudo-filesystem

Every file and directory in the cgroup pseudo-filesystem has a Security Descriptor. Standard [KACS AccessCheck](../access-control/how-accesscheck-works) gates every operation:

| Operation | Access right | On which object |
|---|---|---|
| Read a counter (`cpu.stat`, `memory.current`) | `FILE_READ_DATA` | The counter file |
| Set a limit (`echo 100000 > cpu.max`) | `FILE_WRITE_DATA` | The limit file |
| Create a child cgroup (`mkdir`) | `FILE_ADD_SUBDIRECTORY` | The parent directory |
| Remove a cgroup (`rmdir`) | `DELETE` | The cgroup directory |
| List cgroup members (`cat cgroup.procs`) | `FILE_READ_DATA` | `cgroup.procs` |
| Attach a process to this cgroup | `FILE_WRITE_DATA` on `cgroup.procs` **and** `PROCESS_SET_QUOTA` on the target process | Both must pass |

The Security Descriptor on a new cgroup is inherited from its parent under standard container inheritance rules. An administrator who delegates a subtree by adding an ACE to a directory is implicitly granting that ACE to every cgroup created within the subtree.

This collapses what Linux traditionally treats as two separate concerns — file permissions on cgroupfs entries and "should this process be allowed to manage this cgroup" — into a single uniform mechanism. The same SDs that control access to regular files control access to cgroups.

## Process attachment

Moving a process into a cgroup is the most security-sensitive cgroup operation: it constrains the target process's resource consumption. Two checks gate it:

1. **`FILE_WRITE_DATA` on the destination cgroup's `cgroup.procs`.** You must have authority to modify this cgroup's membership.
2. **`PROCESS_SET_QUOTA` on the target process's SD.** You must have authority to apply resource constraints to that specific process.

Both must pass. The default process SD grants its owner full rights, so attaching your own processes works. Attaching another principal's process requires either an ACE on its SD granting `PROCESS_SET_QUOTA`, or a privilege bypass like `SeTcbPrivilege`.

This two-check model prevents a common class of escape: a process that holds write authority over a permissive cgroup (`/sys/fs/cgroup/unbounded`) cannot drag arbitrary other processes into it as a way of removing their constraints. The target's SD has the final say.

## Privilege gate for top-level cgroups

Creating a cgroup directly under the root is gated by **`SeCreateResourceGroupPrivilege`**. Without this privilege, no `mkdir` succeeds at the root level regardless of DACL grants on the root directory.

Creating cgroups within an existing subtree is purely DACL-gated — the inherited SD on the parent determines who can `mkdir`. This is the **delegation pattern**: a privileged setup creates a top-level cgroup, sets a DACL granting write access to a subtree owner, and from that point the subtree owner can manage their allotment without any privilege.

`SeCreateResourceGroupPrivilege` is held by default by:

- TCB components (peinit, the kernel itself for boot-time cgroups)
- Service-management daemons explicitly granted it
- Container runtime daemons granted it during installation

Default-grant policy is restrictive — ad-hoc unprivileged creation of top-level cgroups is rejected.

## Controllers

Each controller manages a specific resource. Peios ships every controller present in cgroup v2:

| Controller | What it bounds / accounts | Notes |
|---|---|---|
| **cpu** | Proportional weight (`cpu.weight`), bandwidth limit (`cpu.max` quota/period), utilization clamping (`cpu.uclamp.min/max`), idle hints. | Universal. Every service-management story uses this. |
| **memory** | Memory limit (`memory.max`), soft targets (`memory.high`, `memory.low`, `memory.min`), swap (`memory.swap.max`), accounting, OOM control. | Universal. The other half of any workload-isolation story. |
| **io** | Per-device proportional weight (`io.weight`), bandwidth and IOPS caps (`io.max`), latency targets (`io.latency`), priority class. | Noisy-neighbor protection for shared storage. |
| **pids** | Maximum number of processes (`pids.max`), current count, peak. | Fork-bomb protection. Tiny but essential. |
| **cpuset** | CPU and NUMA node pinning (`cpuset.cpus`, `cpuset.mems`), exclusive partitioning. | Required for HPC, real-time, NUMA-aware workloads, and dedicated-core patterns. |
| **freezer** | Atomic freeze/thaw of all processes in the cgroup (`cgroup.freeze`). | Useful for snapshots, container pause, debugging, planned shutdowns. |
| **PSI** | Pressure stall information (`cpu.pressure`, `memory.pressure`, `io.pressure`, `irq.pressure`) — fraction of time tasks were stalled waiting for the resource. | Critical for autoscaling and oncall — no good substitute. |
| **hugetlb** | Per-cgroup limit on [hugetlb-backed memory](../memory-management/huge-pages), per page size. | Active for workloads that explicitly request huge pages. THP is not bounded by this controller. |
| **device** | Per-cgroup access policy for device files, implemented via eBPF programs attached to the cgroup. | Composes with KACS device DACLs — see below. |
| **rdma** | Per-cgroup limits on RDMA resources (verbs objects, queue pairs). | Specialized — applies to InfiniBand / RoCE workloads. |
| **misc** | Generic scalar resource limiter — drivers register named scalar resources and per-cgroup caps. | Used by drivers like NVIDIA's confidential-computing ASID controller. |

cgroup v1 is not supported. v1 paths (per-controller mount points, `tasks` files, `release_agent` notification, the v1-only controllers `net_cls`, `net_prio`, `perf_event`) are not present. Software written against v1 must use v2 paths.

## The device controller and KACS DACLs

The device controller is the only controller that participates in access decisions for non-cgroup objects. It is implemented via eBPF programs attached to the cgroup; on every device file open, the BPF program returns allow or deny.

Peios runs the device cgroup check **alongside** the standard KACS DACL check on the device file. Both must allow — the result is an intersection. This means:

- KACS DACLs are the Peios-native preferred mechanism. A silo with a capability ACE on `/dev/sdb` already has scoped device access via standard AccessCheck.
- The device cgroup is the Linux-compat surface. Container runtimes that configure device cgroups by default (Docker, runc) get the behaviour they expect.
- Neither mechanism alone can grant access — both must allow. This prevents the device cgroup from being bypassed by widening DACLs, and prevents DACLs from being bypassed by configuring permissive device cgroups.

A workload designed for Peios from scratch can use KACS DACLs alone. A workload running unmodified Linux container tooling will configure both, and both will be enforced.

## Composition with silos

Silos and cgroups are **orthogonal primitives**. A silo has no implicit cgroup; a cgroup has no implicit silo. Userspace orchestrators compose them:

- **peinit** places each service in a silo (for identity and namespace isolation) and a cgroup (for resource limits). Both are configured in the service's manifest.
- **Container runtimes** do the same for each container.
- **Standalone limits** — applying a cgroup to a process or process group without putting it in a silo — is supported. Cgroups don't require a silo.
- **Standalone silos** — running a silo without an associated cgroup — is supported but uncommon. Most operational silos want resource bounds.

The cgroup namespace ([one of the seven Peios namespace types](../process-silos/namespaces)) virtualizes the path view of `/sys/fs/cgroup` so a process inside the namespace sees the cgroup it was placed in as `/`, hiding ancestors. This is the only direct interaction between the silo machinery and the cgroup machinery — and it's via the namespace layer, not via the silo identity itself.

## Hierarchy limits

Hierarchy depth and descendant counts are bounded by a system default that each cgroup inherits, plus per-cgroup overrides for finer control.

| Mechanism | Effect |
|---|---|
| `\System\Cgroups\DefaultMaxDepth` (registry knob) | System-wide default maximum depth applied to new cgroups. |
| `\System\Cgroups\DefaultMaxDescendants` (registry knob) | System-wide default maximum descendants under any cgroup. |
| `cgroup.max.depth` (per-cgroup file) | Per-subtree override of maximum depth from this cgroup downward. |
| `cgroup.max.descendants` (per-cgroup file) | Per-subtree override of maximum descendants under this cgroup. |

A new cgroup inherits the registry default. An administrator delegating a subtree can tighten (or loosen, within their own limit) by writing to the per-cgroup files. The effective limit at any point is the most restrictive of the cgroup's own setting and every ancestor's setting.

Defaults are conservative — typical workloads never reach them. Violations return `EAGAIN` on `mkdir`. Common patterns:

- A delegated subtree owner restricts their tenants by writing a tighter `cgroup.max.descendants` to the subtree root.
- A test environment loosens the system default by raising `\System\Cgroups\DefaultMaxDepth` if test scaffolding generates deep cgroup hierarchies.

## Audit

cgroup operations are audited via standard filesystem audit on the cgroup pseudo-filesystem. The SACL on each cgroup directory or file controls what gets logged. The audit knob is `\System\Audit\Cgroups` (with the standard quartet: enabled / success-only / failure-only / disabled).

The default is **failure-only**. Successful cgroup creations and limit changes during normal operation are high-volume and uninteresting; the security-relevant events are denied operations (someone attempted to attach a process they couldn't, someone tried to expand a limit beyond their delegated subtree, someone tried to create a top-level cgroup without privilege).

Resource limit changes that succeed are visible in the **configuration audit** stream (changes to `cpu.max`, `memory.max`, etc. are config writes), not in the access-decision stream. This is the same separation as registry value changes vs registry access denials.

## What cgroups are not

- **cgroups are not identity.** They have SDs (because they're securable nodes in a pseudo-filesystem), but no SIDs. A process is not "tagged" with its cgroup membership in any way that participates in AccessCheck for other objects.
- **cgroups are not visibility isolation.** A process in cgroup A can see and signal a process in cgroup B if the standard process SD allows. Visibility isolation is the namespace's job (see [PID namespace](../process-silos/namespaces)).
- **cgroups are not a sandbox.** A process inside a cgroup with strict CPU and memory limits still has the access rights of its token. Sandboxing is [Confinement](../confinement/understanding-confinement) and [Process Silos](../process-silos/understanding-process-silos)'s job.

cgroups bound and account; that is their entire role. The other primitives compose with them to build the higher-level isolation patterns.
