---
title: eBPF — Overview and Design
type: concept
description: What eBPF is on Peios, the design posture as a first-class kernel extension mechanism alongside kernel modules, and how Peios-native subsystems integrate.
related:
  - peios/ebpf/program-types-and-attach-points
  - peios/ebpf/the-verifier
  - peios/ebpf/peios-integration
  - peios/ebpf/privileges-and-trust
  - peios/kernel-modules/overview-and-design
---

**eBPF** (extended Berkeley Packet Filter) is a programmable in-kernel bytecode mechanism: small programs are loaded from userspace, statically verified for safety, JIT-compiled to native code, and attached to specific kernel hook points where they run in response to events.

Peios treats eBPF as a **first-class kernel extension mechanism**, alongside kernel modules. Where a module injects native code, eBPF injects verified bytecode. The two mechanisms cover different parts of the extension surface and have different threat profiles.

## Two extension mechanisms

Peios offers two ways to extend the running kernel:

| Mechanism | Code form | Safety model | Typical use |
|---|---|---|---|
| **Kernel modules** | Compiled native code (`.ko`) | None — full kernel privilege | Drivers, filesystems, network protocols |
| **eBPF** | Bytecode, verified and JIT-compiled | Verifier-enforced safety properties | Observability, policy hooks, networking dataplanes, scheduling |

Modules are how you teach the kernel about new hardware or protocols. eBPF is how you express programmable policy and observation at points the kernel already understands.

The two mechanisms have different threat profiles. A loaded module has unrestricted access to kernel memory and CPU; the only defense is the load gate (privilege + signature). An eBPF program is constrained at runtime: the verifier enforces memory safety, bounded execution, and access only to explicitly exposed helpers and kfuncs. eBPF is not safe in an absolute sense — verifier bugs, buggy kfuncs, and attach points that expose too much state are real concerns — but the safety floor is far higher than for modules.

## Why first-class

Modern kernel extension is converging on eBPF. Networking dataplanes (Cilium, XDP-based load balancers), runtime security tooling (Tetragon, Falco, BPF LSM), pluggable scheduling (sched_ext), and observability (perf+BPF, tracing) are increasingly built as eBPF rather than modules. The verifier provides a much safer code-injection model, and the BTF/CO-RE infrastructure makes programs portable across kernel versions.

Peios commits to eBPF as a primary extension surface for two reasons:

1. **Inheriting Linux's investment.** The verifier, JIT, BTF, CO-RE, and kfunc machinery are mature. Building a bespoke alternative would lose years of work and cut off the Linux tooling ecosystem.
2. **Programmable Peios primitives.** Peios exposes its own kernel primitives (KACS access checks, LCS registry operations, KMES events, GUID-based identity) as helpers and attach points usable from BPF programs. This makes eBPF the natural surface for programmable Peios policy, not just Linux compatibility.

## Posture

The standard Peios server build:

- **Ships the Linux BPF subsystem intact.** The verifier, JIT, all standard program types, all standard attach points, all standard helpers, BPF LSM, and the `bpf()` syscall are present and behave as upstream Linux. Linux-native BPF tooling works.
- **Adds Peios-native helpers and attach points additively.** Functions like `bpf_kacs_access_check()`, `bpf_lcs_get_value()`, `bpf_kmes_emit()`, and KACS-native attach points are layered on top. They are documented as Peios extensions; programs that use only Linux helpers remain portable.
- **Gates loading and attachment behind privileges.** Most attach points (tracing, networking, policy, KMES filtering, BPF LSM) require `SeLoadDriverPrivilege` — the same privilege that gates kernel module loading. The blast radius is similar (kernel code injection), so the gate is the same. `sched_ext` requires the more restrictive `SeLoadSchedulerPrivilege` — its blast radius is whole-system scheduling correctness.
- **Audits attachment loudly.** Every BPF program load and attachment emits a security event identifying the principal, the program type, the attach point, and the program identifier. The visibility of intent comes from auditing the attach itself, not from runtime invariants on what programs may do.
- **Defers federated distribution to post-v1.** When BPF programs become deployable artifacts (signed, GPO-pushable to all domain machines), the distribution primitive will share infrastructure with kernel updates, livepatch, and module distribution. v1 ships operator-loads-locally.

## What lives on which page

| Topic | Page |
|---|---|
| Program types, attach points, the four functional categories | [Program types and attach points](program-types-and-attach-points) |
| The verifier, BTF, CO-RE, safety guarantees | [The verifier](the-verifier) |
| Maps, ring buffers, BPF arena, helpers, kfuncs | [Maps and helpers](maps-and-helpers) |
| Peios-native helpers, KACS attach points, KMES integration, ABI tiering | [Peios integration](peios-integration) |
| Privileges, signing, bpffs, BPF tokens, audit, distribution | [Privileges and trust](privileges-and-trust) |

## See also

- [Kernel modules — Overview and Design](../kernel-modules/overview-and-design) — the other kernel extension mechanism.
- [SeLoadDriverPrivilege](../privileges/load-driver) — gates BPF program loading and attachment for most attach points.
- [Linux compatibility](../linux-compatibility) — the Linux BPF subsystem ships intact.
