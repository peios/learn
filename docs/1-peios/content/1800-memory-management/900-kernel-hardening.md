---
title: Kernel Address Space Hardening
type: concept
description: Kernel-side memory hardening on Peios — KASLR, KPTI, and the Spectre family of speculative-execution mitigations. Image-built-in defences.
related:
  - peios/memory-management/understanding-the-address-space
  - peios/memory-management/userfaultfd
---

The userspace memory model has its own attackers — buffer overflows, use-after-frees, type confusion. The kernel has its own, larger and more consequential attack surface, and a corresponding family of defensive techniques aimed at making the kernel harder to compromise even when bugs exist. This page enumerates the hardening features Peios builds into its kernel and how they affect what userspace can observe.

These are not user-controlled. They are decided at kernel **build time** and at **boot** via early command-line parameters; the running system inherits whatever the image was configured with. From userspace, they are observable through `/sys/devices/system/cpu/vulnerabilities/` but not modifiable. The default Peios kernel image enables all production-recommended mitigations.

## KASLR

**Kernel Address Space Layout Randomization** randomises the location of the kernel's image in virtual memory at boot. Without KASLR, every boot puts the kernel at the same virtual address and an attacker who finds an info-leak revealing any kernel pointer can compute the offsets of every kernel function and structure. With KASLR, the kernel's base address shifts by a per-boot random value, and information leaks have to specifically reveal *that boot's* layout to be useful.

KASLR is enabled in the default image. The randomisation entropy is bounded by the kernel's virtual address space layout (around 30 bits of randomisation on x86-64), which is sufficient to defeat opportunistic remote attacks but insufficient against an attacker who can run code locally and probe.

Boot-time disable: `nokaslr` on the kernel command line. This is occasionally used for debugging — a kernel oops dump is much easier to read with known addresses — but production images forbid it.

## KPTI

**Kernel Page Table Isolation** is the Meltdown mitigation. Meltdown (CVE-2017-5754) allowed userspace to speculatively read kernel memory via cache-timing side channels on affected Intel CPUs. The fix isolates kernel page tables from userspace page tables: when userspace runs, the kernel's pages are not mapped at all, so a speculative read cannot reach them.

KPTI has a measurable performance cost (5–30% on syscall-heavy workloads) because every syscall now flips between two page tables. CPUs with hardware Meltdown immunity (post-Coffee Lake on Intel; AMD has always been immune) can disable KPTI safely; the kernel detects this and turns it off automatically on those CPUs.

Boot-time control: `pti=on`/`pti=off`/`pti=auto` (the default `auto` enables KPTI on vulnerable CPUs and skips it on immune ones). Production images use `auto`; only diagnostic kernels override.

## The Spectre family

**Spectre** is the umbrella name for a series of speculative-execution side-channel attacks that exploit the CPU's tendency to execute instructions before knowing whether they should be executed. The CPU eventually unwinds the speculative work, but cache state changes made during speculation persist, and timing those changes leaks information about what was speculatively accessed.

The attacks span several variants, each with its own mitigation:

| Variant | CVE | Mechanism | Mitigation |
|---|---|---|---|
| **Spectre v1** | CVE-2017-5753 | Bounds-check bypass: speculatively read past array bounds, then leak the read value via cache timing. | Source-code annotations (`array_index_nospec`) on bounds-checked arrays in security-sensitive paths. Compiler-assisted. |
| **Spectre v2** | CVE-2017-5715 | Branch target injection: train the branch predictor to mispredict an indirect branch into attacker-controlled gadgets. | **Retpoline** (replace indirect branches with a return-trampoline pattern) on older CPUs; **eIBRS / IBRS** (enhanced Indirect Branch Restricted Speculation, hardware) on newer CPUs; **IBPB** (Indirect Branch Predictor Barrier) on context switches between security domains. |
| **Spectre v4** | CVE-2018-3639 | Speculative store bypass: speculatively read stale data before a pending store completes. | **SSBD** (Speculative Store Bypass Disable) — opt-in per-process via `prctl(PR_SET_SPECULATION_CTRL)`. |

The default image enables Spectre v1 and v2 mitigations system-wide. Spectre v4 mitigation is opt-in because the performance cost is significant and most workloads aren't exposed (the threat model requires running attacker-controlled code in the same address space).

## MDS, TAA, L1TF, and the rest

A second wave of speculative-execution vulnerabilities targets specific microarchitectural buffers and structures:

| Family | Mitigation summary |
|---|---|
| **MDS** (Microarchitectural Data Sampling — CVE-2018-12126/12130/12127, CVE-2019-11091) | CPU buffers (store buffers, load ports, fill buffers) leak data across security domains. Mitigation: clear the affected buffers on every kernel-to-user transition (`VERW` instruction on x86-64). |
| **TAA** (TSX Asynchronous Abort — CVE-2019-11135) | Same families of buffers, leaked via the TSX transactional-memory feature. Mitigation: same buffer-clearing as MDS, plus disabling TSX on vulnerable CPUs. |
| **L1TF** (L1 Terminal Fault — CVE-2018-3615/3620/3646) | Reads from non-present PTEs speculatively retrieve cached L1 data. Mitigation: never set non-present PTEs to physical addresses pointing at sensitive data. Affects KVM hypervisors most heavily. |
| **MMIO Stale Data** (CVE-2022-21123/21125/21127/21166) | Stale data in CPU buffers leaked through memory-mapped-I/O reads. Mitigation: same VERW-on-transition pattern. |
| **Retbleed** (CVE-2022-29900/29901) | Return instructions can be predicted using indirect-branch-prediction state. Mitigation: enhanced retpoline patterns; on AMD, IBPB on context switch. |
| **Downfall (GDS)** (CVE-2022-40982) | The `GATHER` instruction leaks data from internal vector register buffers. Mitigation: serialising GATHER, microcode update. |
| **Inception (SRSO)** (CVE-2023-20569) | AMD-specific: speculative return-stack-buffer poisoning. Mitigation: explicit return-stack-buffer flushing. |

The pattern across all of these: a CPU microarchitectural feature speculatively does something useful for performance, an attacker observes the side effect of that speculation, and the mitigation either disables the feature or clears the affected state at every boundary crossing. Each mitigation has its own performance cost (often 1–10% for IPC-heavy workloads), and each is independently enabled.

The default Peios kernel enables every production-recommended mitigation. Some specialised images (for example, sealed appliances on dedicated hardware where no untrusted code ever runs) may disable specific mitigations to reclaim performance, but this is a deliberate image-policy choice with a documented security trade-off.

## Observing mitigation state

`/sys/devices/system/cpu/vulnerabilities/` exposes one file per known vulnerability, listing the kernel's view of whether the CPU is vulnerable and what mitigation is active. Sample contents on a hardened system:

```
$ ls /sys/devices/system/cpu/vulnerabilities/
gather_data_sampling  l1tf  mds  meltdown  mmio_stale_data
retbleed  spec_store_bypass  spectre_v1  spectre_v2  srbds  tsx_async_abort

$ cat /sys/devices/system/cpu/vulnerabilities/spectre_v2
Mitigation: Enhanced IBRS, IBPB: conditional, RSB filling
```

Reading these files is unprivileged — the information is not sensitive in itself, and observing what mitigations are active is part of every legitimate security audit.

The mitigation state cannot be modified at runtime by writing to these files. They are advisory; the kernel's mitigation choices are made at boot and locked in until the next boot.

## Per-process speculation control

A process can opt itself into stronger speculation isolation through `prctl(PR_SET_SPECULATION_CTRL)`:

| Speculation control | Purpose |
|---|---|
| `PR_SPEC_STORE_BYPASS` | Enable Spectre v4 SSBD for this process. |
| `PR_SPEC_INDIRECT_BRANCH` | Enable per-process indirect branch barrier on context switch into this process. |
| `PR_SPEC_L1D_FLUSH` | Flush L1D cache on every context switch into this process. |

These are `prctl` knobs on the calling process; they apply to the process and its descendants until cleared. Browsers, sandboxes, and other software running attacker-controlled code in the same address space typically opt in. Most other processes don't bother, because the per-process performance cost outweighs the benefit when the process isn't running untrusted code.

These prctls are unprivileged — a process is asking for *more* speculation containment for itself, not less.

## Stack-smashing protection

Compiler-side stack canaries are not a kernel feature, but they're worth mentioning as part of the same defence-in-depth picture: the Peios userspace toolchain enables stack canaries by default for compiled binaries. The kernel itself is built with stack canaries on every function. A successful stack overflow that overwrites the canary triggers an immediate panic on detection.

## See also

- [Understanding the Address Space](understanding-the-address-space) — KASLR's effect on kernel address visibility.
- [userfaultfd](userfaultfd) — the userspace primitive that historically widened kernel-side race windows; relevant to the broader "kernel hardening against userspace" picture.
