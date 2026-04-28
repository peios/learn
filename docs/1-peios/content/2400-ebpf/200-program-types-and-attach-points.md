---
title: Program Types and Attach Points
type: concept
description: The taxonomy of BPF program types, the attach points each can hook, and the four functional categories — tracing, networking, policy, and scheduling.
related:
  - peios/ebpf/overview-and-design
  - peios/ebpf/the-verifier
  - peios/ebpf/peios-integration
  - peios/ebpf/privileges-and-trust
---

A BPF program is loaded with a declared **program type**, which determines the context it receives, the helpers and kfuncs it may call, and the attach points it can target. Every program type corresponds to a kernel-side hook (or family of hooks) where the program runs.

This page is the catalogue: what types exist, what they hook, what they're for.

## Functional categories

Program types fall into four broad categories by what they do:

| Category | Purpose | Examples | Privilege |
|---|---|---|---|
| **Tracing** | Observe kernel/userspace execution. Reads state; cannot enforce. | kprobe, tracepoint, fentry/fexit, perf_event, BPF iterator, uprobe | `SeLoadDriverPrivilege` |
| **Networking** | Process packets in the dataplane. Drops, modifies, redirects. | XDP, tc/cls_bpf, sock_filter, SOCK_OPS, netfilter | `SeLoadDriverPrivilege` |
| **Policy** | Make access/configuration decisions. Can deny operations. | LSM, cgroup attach types, sock_addr, struct_ops | `SeLoadDriverPrivilege` |
| **Scheduling** | Make scheduling decisions for tasks. Can replace the scheduler. | sched_ext (`struct_ops/sched_ext_ops`) | `SeLoadSchedulerPrivilege` |

The privilege model reflects blast radius. Tracing/networking/policy programs share `SeLoadDriverPrivilege` with kernel module loading because their failure modes (read kernel memory, drop packets, deny operations) are similar in magnitude to module loading. `sched_ext` is qualitatively different — every task's scheduling decision goes through the program, and bugs can deadlock the system — so it gets its own privilege. See [Privileges and trust](privileges-and-trust).

## Tracing

| Type | Hook | What it observes |
|---|---|---|
| **kprobe / kretprobe** | Arbitrary kernel function entry/return | Function arguments, return values |
| **tracepoint** | Static tracepoints throughout the kernel | Tracepoint-specific structured data |
| **raw_tracepoint** | Tracepoints with raw arguments | Lower overhead than tracepoint |
| **fentry / fexit** (BPF trampolines) | Function entry/exit with low overhead | Same as kprobe but ~10× faster (no INT3 trap) |
| **uprobe / uretprobe** | Userspace function entry/return | Userspace arguments and state |
| **uprobe session** | Paired entry/exit on a userspace function as a single attach | Entry and exit context together |
| **perf_event** | perf event source (CPU cycles, cache misses, etc.) | Sampled performance data |
| **BPF iterator** | Iterate kernel data structures (tasks, sockets, cgroups) on demand | Records yielded to userspace |

Tracing programs read state; they do not modify or deny. They are the observability foundation for `bpftrace`, perf, and userspace tracers. BPF trampolines (fentry/fexit) are the modern replacement for kprobes where available — same expressive power, much lower overhead.

## Networking

| Type | Hook | What it does |
|---|---|---|
| **XDP** | Earliest packet receive (driver level, before SKB allocation) | Drop, redirect, pass, modify |
| **tc / cls_bpf** | Traffic control egress/ingress | Same as XDP, plus integration with qdiscs |
| **BPF qdisc** (kernel 6.16+) | Implement an entire qdisc as a BPF program | Custom queueing disciplines |
| **sock_filter** (cBPF, classic) | Socket packet filter (legacy `SO_ATTACH_FILTER`) | Accept/reject packet at socket |
| **SOCK_OPS** | TCP socket events (connect, retransmit, congestion) | Tune TCP parameters per-connection |
| **sk_skb / sk_msg** | Socket-level skb/msg redirect | Redirect data between sockets |
| **netfilter** | Netfilter hook chain | Deny/accept/modify packets at firewall hooks |
| **lwt_in / lwt_out / lwt_xmit** | Lightweight tunnel encap/decap | Tunnel processing |

XDP is the highest-performance attach point — programs run before SKB allocation, on the driver's RX path. tc is more flexible but slightly more expensive. BPF qdisc (kernel 6.16+) lets a program implement an entire queueing discipline.

## Policy

| Type | Hook | What it gates |
|---|---|---|
| **BPF LSM** | LSM hooks (`security_*()` calls — `security_file_open`, `security_inode_permission`, etc.) | Linux-style access decisions on files, sockets, IPC |
| **cgroup_skb / cgroup_sock** | cgroup network attach | Per-cgroup network policy |
| **cgroup_device** | cgroup device cgroup hook | Per-cgroup device access |
| **cgroup_sysctl** | sysctl read/write within a cgroup | Restrict sysctl access per cgroup |
| **sock_addr** | bind/connect/sendto address calls | Mutate addresses, redirect connects |
| **struct_ops** | Replace a kernel struct of function pointers with BPF implementations | Subsystem-defined; e.g. TCP congestion control algorithms |

BPF LSM programs see Linux-shaped state (file modes, UIDs, paths). For Peios-native access decisions (KACS AccessCheck against SDs), Peios provides separate KACS attach points — see [Peios integration](peios-integration).

## Scheduling

| Type | Hook | What it does |
|---|---|---|
| **sched_ext** (`struct_ops/sched_ext_ops`) | The CPU scheduler itself | Implements task selection, enqueue/dequeue, idle loop |

`sched_ext` lets a BPF program implement an entire scheduling class, replacing the kernel's CFS/EEVDF scheduler for participating tasks. See [Understanding scheduling](../process-management/understanding-scheduling) for the Peios-specific design (privilege gate, audit posture, kernel-fallback behaviour on watchdog timeout).

## The bpf() syscall

Programs are loaded and attached through the `bpf()` syscall, which multiplexes a wide range of operations:

| Operation | Purpose |
|---|---|
| `BPF_PROG_LOAD` | Load and verify a program; returns a program fd |
| `BPF_PROG_ATTACH` / `BPF_LINK_CREATE` | Attach a program to a hook, returning an attach fd or link fd |
| `BPF_MAP_CREATE` | Create a map; returns a map fd |
| `BPF_MAP_*_ELEM` | Manipulate map elements |
| `BPF_PROG_TEST_RUN` | Run a program against synthetic input for testing |
| `BPF_OBJ_PIN` / `BPF_OBJ_GET` | Pin/retrieve programs and maps in bpffs |
| `BPF_BTF_LOAD` | Load BTF type information |
| `BPF_TOKEN_CREATE` | Create a delegated permission token (kernel 6.9+) |

`bpf()` is gated by privilege, not file mode. See [Privileges and trust](privileges-and-trust).

## Pinning programs and maps

Programs and maps are normally fd-scoped — they vanish when the last fd referencing them is closed. To make them persist across processes, they can be **pinned** in the BPF filesystem (`bpffs`, mounted at `/sys/fs/bpf/`). A pinned object lives until explicitly unpinned, even after every process that loaded it has exited.

Pinning is the standard mechanism for "this BPF program runs as part of the system, not as part of a user session" — daemons that load programs at startup pin them so the programs survive the daemon's restart. See [Privileges and trust](privileges-and-trust) for the bpffs SD model.

## Sleepable programs

Some attach points permit a program to sleep — to call helpers that may block (e.g. for I/O, allocation). Sleepable programs are declared at load time and the verifier permits a different helper allowlist. As of kernel 7.0, sleepable programs may tail-call other sleepable programs, enabling more flexible composition.

## See also

- [The verifier](the-verifier) — what makes BPF programs safe to attach to these hooks.
- [Maps and helpers](maps-and-helpers) — the data structures and helpers that programs at any of these attach points can use.
- [Peios integration](peios-integration) — KACS-native attach points and Peios helpers.
- [Understanding scheduling](../process-management/understanding-scheduling) — sched_ext details.
