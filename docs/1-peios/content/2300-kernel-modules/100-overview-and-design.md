---
title: Kernel Modules — Overview and Design
type: concept
description: What kernel modules are on Peios, the security premise behind the loading model, and the high-level policy posture.
related:
  - peios/kernel-modules/loading-and-unloading
  - peios/kernel-modules/signing-and-trust
  - peios/kernel-modules/auto-loading-and-lockdown
  - peios/privileges/load-driver
---

A **kernel module** is a chunk of compiled kernel code (a `.ko` file — "kernel object") that can be loaded into the running kernel at runtime. Once loaded, its code runs at the same privilege level as the rest of the kernel: full access to memory, hardware, and every kernel data structure. There is no sandbox.

This page describes the high-level design — what modules are, why the loading model has the security shape it does, and the policy posture Peios takes by default. The mechanics of each operation (load, unload, sign, parameterise) live on the dedicated pages linked at the bottom.

## Why modules exist

Modules let the kernel ship small. Rather than baking every supported driver, filesystem, and networking protocol into a single immutable image, the kernel boots with a minimal set and loads additional code on demand:

- **Drivers** — most device drivers (Ethernet, GPU, USB controllers, SATA controllers) are modules. The kernel image stays small; modules for the hardware actually present get loaded at boot.
- **Filesystems** — ext4, XFS, NFS, FUSE — all loadable.
- **Network protocols** — WireGuard, exotic socket families, custom firewalls.
- **Specialised features** — virtualization extensions, RAID, security frameworks.

The same code can be compiled either as a module or built into the kernel image directly. Built-in code is part of the immutable boot kernel; module code is loaded after boot. The choice between built-in and modular is made at kernel build time.

## The security premise

The security shape of the entire module subsystem flows from one fact:

> Loading a kernel module is functionally equivalent to giving someone write access to the running kernel.

A loaded module's code runs in the same address space, with the same privileges, and against the same data structures as every other kernel function. A buggy module can crash the kernel; a malicious module can:

- Disable any security check by replacing it with a no-op.
- Exfiltrate kernel memory (including credentials, keys, and sensitive userspace memory mapped into kernel views).
- Modify any process's memory or token state.
- Tamper with audit before it leaves the kernel.

There is no in-kernel sandbox for module code. Any defense must therefore happen at the **load gate** — before the module's code starts running.

The Peios load gate has two independent components:

| Component | What it gates | Defense it provides |
|---|---|---|
| **Authority** (`SeLoadDriverPrivilege`) | Who can ask the kernel to load a module | A compromised low-privilege process cannot directly invoke `init_module` |
| **Signature verification** | Whether a given module is permitted to load | Even with `SeLoadDriverPrivilege`, the module must be signed by a trusted key |

Both gates apply to every load. The authority gate stops the call from reaching the loader; the signature gate stops untrusted code from being installed even when the call is permitted. See [Loading and unloading](loading-and-unloading) for the authority story and [Signing and trust](signing-and-trust) for the signature story.

## Policy posture

The standard Peios server build is configured for **operations-driven module management** — drivers and protocol modules ship as signed packages from the Peios distribution (or from a customer's internal package pipeline), are installed via the package manager like anything else, and are loaded at boot or by the relevant service. Runtime ad-hoc module loading is permitted but not the typical operational pattern.

Specifically:

- **Authority is held narrowly.** `SeLoadDriverPrivilege` is granted to `Administrators` and `LocalSystem` by default. Service principals that load drivers (e.g. the device-management service) hold the privilege; ordinary application services do not.
- **Signing is enforced via build-time floor.** The kernel build hardcodes a minimum signing-policy floor (`warn` on standard server builds, matching Linux's effective default; can be raised to `enforce` via the registry knob `\System\Modules\SigningPolicy`). The runtime knob can tighten beyond the floor but never loosen.
- **Auto-loading defaults to enabled** for compatibility with Linux's behaviour. Customers that want to tighten can set `\System\Modules\AutoLoadPolicy` to `allow-list` or `disabled`.
- **Forced unload is compiled out** on standard server builds. The mechanism does not exist in the kernel; `rmmod -f` returns the same result as `rmmod`.
- **Live patching is deferred** to post-v1. The `CONFIG_PEIOS_LIVEPATCH` build flag is `n` on standard builds. Kernel security updates are applied via reboot.
- **Out-of-tree modules are pre-built and signed by Peios distribution infrastructure** (or by customer build pipelines) and shipped as regular packages. There is no DKMS, no compiler, and no kernel headers on the standard server image.

Each of these is configurable for environments with different needs (development variants, multi-tenant hosting, forensic) but the standard server defaults are calibrated for "production server with a known operational team."

## What lives on which page

| Topic | Page |
|---|---|
| Load/unload mechanics, authority gate, lifecycle | [Loading and unloading](loading-and-unloading) |
| Signature verification, trusted keyrings, MOK | [Signing and trust](signing-and-trust) |
| Module parameters and runtime tuning | [Parameters](parameters) |
| Dependency resolution, symbol exports, ABI compatibility | [Dependencies and metadata](dependencies-and-metadata) |
| Auto-loading policy, blacklist, post-boot lockdown | [Auto-loading and lockdown](auto-loading-and-lockdown) |
| Taint bits, observability, audit | [Tainting and observability](tainting-and-observability) |

## See also

- [SeLoadDriverPrivilege](../privileges/load-driver) — the privilege that gates module loading and unloading.
- [SeTcbPrivilege](../privileges/tcb) — required to flip the post-boot lockdown ratchet.
- [Linux compatibility](../linux-compatibility) — how Linux module ABI is preserved.
