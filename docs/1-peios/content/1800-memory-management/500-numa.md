---
title: NUMA Support
type: concept
description: NUMA topology and memory policy on Peios — controlling where memory comes from on multi-socket systems, and the gates on cross-process migration.
related:
  - peios/memory-management/memory-mapping
  - peios/memory-management/huge-pages
  - peios/process-management/cpu-affinity-and-isolation
  - peios/process-security/process-security-descriptors
---

A **NUMA** (Non-Uniform Memory Access) system has multiple memory controllers, each attached to a subset of the CPUs. Memory access from a CPU to its **local node** is fast; access to a **remote node** crosses an interconnect (UPI on Intel, Infinity Fabric on AMD) and is slower. On a typical two-socket server, remote-node memory access is roughly 1.5–2× the latency of local-node access, and bandwidth between sockets is shared with cache-coherence traffic.

Workloads that don't account for NUMA can lose 20–40% of available performance to suboptimal placement. The kernel makes reasonable defaults (allocate on the local node, schedule on the node where memory was allocated), but applications with strong NUMA affinity benefit from explicit policy.

This page covers how processes inspect the topology, set memory-allocation policies, and migrate pages — including the access-control rules for cross-process operations.

## Topology

The kernel exposes the system topology through `/sys/devices/system/node/`:

```
/sys/devices/system/node/
├── node0/
│   ├── cpulist           # CPUs attached to this node
│   ├── meminfo           # memory totals for this node
│   ├── hugepages/
│   └── distance          # latency-weighted distance to other nodes
├── node1/
│   └── ...
└── ...
```

The `distance` file contains a small array — typically `[10 20]` for a two-node system, meaning node 0 is at distance 10 from itself and 20 from node 1. The numbers are kernel-internal hints; the absolute values aren't physically meaningful but the ratios are. A kernel that sees `[10 20]` will prefer local-node allocation strongly; a kernel seeing `[10 11]` (rare) will treat the nodes as nearly equivalent.

`numactl --hardware` and `lscpu` summarise the topology in a readable form. `/proc/<pid>/numa_maps` shows the per-VMA NUMA distribution for any process whose process SD permits introspection — same gating as `/proc/<pid>/maps` (see [Understanding the Address Space](understanding-the-address-space)).

## Memory policies

A process or thread tells the kernel where to allocate memory by setting a **memory policy**. The policy applies to future page-faults that need physical pages allocated.

| Policy | Behaviour |
|---|---|
| `MPOL_DEFAULT` | Use the local node. The default. |
| `MPOL_BIND` | Allocate only from the specified set of nodes. Fail allocation if none can satisfy. |
| `MPOL_PREFERRED` | Try the preferred node first; fall back to any node on failure. |
| `MPOL_PREFERRED_MANY` | Like `MPOL_PREFERRED` but with a set of preferred nodes (kernel 5.15+). |
| `MPOL_INTERLEAVE` | Round-robin allocations across the specified nodes. Even distribution; useful for workloads accessing memory uniformly. |
| `MPOL_LOCAL` | Like `MPOL_DEFAULT` but explicit. Allocate on the node the calling thread is currently running on. |
| `MPOL_WEIGHTED_INTERLEAVE` | Weighted round-robin (kernel 6.9+). |

The setting calls:

| Syscall | Scope |
|---|---|
| `set_mempolicy(mode, nodemask)` | Per-thread default policy. |
| `mbind(addr, len, mode, nodemask, flags)` | Policy on a specific memory range. Overrides per-thread. |
| `set_mempolicy_home_node(addr, len, node, flags)` | Set a "home node" hint for an existing range. |
| `get_mempolicy(...)` | Retrieve the current policy. |

`MPOL_BIND` with a single node is the strongest constraint: allocation fails outright if that node is exhausted. `MPOL_PREFERRED` is the middle ground: try one node first, fall back to any other if needed. `MPOL_INTERLEAVE` is the right choice for workloads with no spatial locality, where uniform distribution beats local-node allocation.

There are no privilege requirements for setting policy on **your own** memory — a process is free to specify whatever it wants, subject to the constraint that you can't allocate from a node that doesn't exist.

## NUMA balancing

The kernel runs a background mechanism called **NUMA balancing** that periodically samples a process's memory accesses (by faulting some pages and watching which CPU triggers the re-fault). When it detects that a process is accessing pages on a remote node, it migrates those pages to the local node.

This is automatic and transparent. Processes that explicitly set policies override balancing for the affected ranges; balancing only operates on memory under the default policy.

Balancing has overhead — the periodic faulting costs a few percent of execution time — and is sometimes disabled on workloads that have manually tuned NUMA placement and don't want the kernel second-guessing them. The on/off and aggressiveness knobs are admin sysctls, registry-driven via ksyncd:

| Tunable | Purpose |
|---|---|
| `numa_balancing` | 0 = off, 1 = on. |
| `numa_balancing_scan_*` | Various aggressiveness knobs. |

## Migrating existing pages

`set_mempolicy` and `mbind` only affect **future** allocations. To move memory that's already allocated, use one of the migration calls.

| Syscall | Effect |
|---|---|
| `migrate_pages(pid, old_nodes, new_nodes)` | Move all of a process's pages from one set of nodes to another. |
| `move_pages(pid, count, pages, nodes, status, flags)` | Move specific pages, identified by their virtual addresses. |

Both can target another process by passing a non-zero `pid`. When the target is another process, the operation is gated on the **target's process SD**:

- `migrate_pages` and `move_pages` against another process require **`PROCESS_VM_WRITE`** on the target's process SD plus **PIP dominance**.
- The same gates apply to `process_madvise` setting NUMA-relevant advice on another process — see [Memory Mapping](memory-mapping).

Self-migration (`pid = 0` or own pid) is unrestricted — moving your own pages between nodes you have access to is always fine.

The privilege model recognises that NUMA migration affects performance in ways that can be adversarial: a process forced to migrate its hot pages onto a slow remote node has been DoS'd, even though no security boundary was crossed. The process SD gate is the right control.

## Practical NUMA tuning

A few patterns are worth knowing:

**Pin and allocate locally.** A latency-sensitive process pins itself to one node's CPUs (see [CPU Affinity and Isolation](../process-management/cpu-affinity-and-isolation)) and uses `MPOL_BIND` to allocate only from that node's memory. This eliminates remote-node access entirely at the cost of capacity (you only have access to one node's RAM).

**Interleave for throughput.** A scientific workload that touches all of memory roughly equally benefits from `MPOL_INTERLEAVE` — even distribution means peak bandwidth equals the sum of all nodes' bandwidth, not just one node's.

**Per-thread policies in multithreaded workloads.** Each worker thread sets its own policy via `set_mempolicy`, allocating from the node where it's pinned. The kernel respects per-thread policies independently, so a multi-threaded process can have different threads allocating from different nodes simultaneously.

**Disable autobalancing for tuned workloads.** A process that has manually placed its memory wants to stop the kernel from second-guessing it. Either set policies on every region (which suppresses balancing), or admin-disable autobalancing globally if the whole system is tuned.

## Hugepages and NUMA

Hugepage pools are per-node — `/sys/devices/system/node/node<N>/hugepages/` controls each node's reservation. A workload using `MAP_HUGETLB` allocates from the local node's pool by default; `mbind`-ing the mapping with `MPOL_BIND` to a specific node draws from that node's pool. Imbalanced pools (lots of huge pages on one node, none on another) can cause hugepage allocations to fail even when total system free memory is plentiful.

## See also

- [Memory mapping](memory-mapping) — `mmap`, `mbind`, and the `process_*` cross-process variants.
- [Huge Pages](huge-pages) — per-node hugepage pools.
- [CPU Affinity and Isolation](../process-management/cpu-affinity-and-isolation) — pinning threads to specific NUMA nodes' CPUs.
