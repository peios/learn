---
title: Kernel invariants
type: concept
description: The boot chain relies on a handful of kernel-level invariants — the LSM stack must include PKM and exclude MAC LSMs, certain build-config flags must be set, the kernel must verify these at initialisation. This page covers the invariants the boot chain depends on and the failure modes if any are missing.
related:
  - peios/boot-and-trust-establishment/overview
  - peios/boot-and-trust-establishment/bootstrap-tokens
  - peios/boot-and-trust-establishment/initramfs-stage
  - peios/boot-and-trust-establishment/peinit-pid-1
  - peios/binary-signing/overview
  - peios/process-integrity-protection/overview
  - peios/linux-compatibility/overview
---

The boot chain — kernel-direct tokens, peinit at PID 1, the authd handoff — relies on a handful of **kernel-level invariants** to be safe. Things like "PKM is in the LSM stack and no incompatible LSM is", "the kernel rejects unsigned kernel modules", "physical memory is restricted to what is appropriate". If these invariants are violated, the security model the rest of these docs describes is no longer guaranteed.

This page covers the invariants, where each is enforced, and the consequences of failure. They are not user-facing settings in the sense of "things you might change" — they are kernel build-time and init-time configurations that the deployment requires. But knowing what they are helps with reasoning about the trust chain and diagnosing the rare case where something doesn't fit the expected model.

## The LSM stack invariant

The Linux Security Module framework lets the kernel host multiple security modules in a defined order. Peios's KACS is implemented as an LSM called **PKM** (Peios Kernel Module). For PKM to function correctly:

- PKM must be in the LSM stack.
- MAC (Mandatory Access Control) LSMs must NOT be in the stack — specifically SELinux, AppArmor, SMACK, and TOMOYO.
- The BPF LSM must not be active.

The reasoning: MAC LSMs and PKM both want to make authoritative access decisions, and the LSM framework's composition rules don't merge their decisions cleanly. A system with SELinux *and* PKM would have both modules trying to decide each access; the result would be that either both must agree (over-restrictive) or one supersedes the other (whichever the LSM order puts first), neither of which is the right semantic. Peios's model is that PKM is the sole authoritative module for the operations it covers.

### What the kernel verifies

The kernel verifies at PKM initialisation that no MAC LSM is active and that BPF LSM is not in use. If any are present, PKM refuses to activate. The kernel boots, but the access control is now broken — PKM is supposed to be enforcing, and it isn't. This is detected and reported as an init-time error.

Specifically, PKM refuses to activate if any of `selinux`, `apparmor`, `smack`, `tomoyo`, or `bpf` LSMs are present in the active stack.

### The required stack

The LSM stack Peios expects is, in order:

```
landlock, lockdown, yama, integrity, pkm
```

- **`commoncap`** is implicit (Linux always includes it; not listed in `CONFIG_LSM` explicitly).
- **`landlock`** is permitted — it's a process-local sandboxing LSM that processes opt into; it doesn't conflict with PKM.
- **`lockdown`** is permitted — it gates specific kernel-debugging interfaces; orthogonal to PKM.
- **`yama`** is permitted — it adds ptrace restrictions; complements PKM's ptrace gating.
- **`integrity`** is permitted — Linux's IMA/EVM mechanisms can run alongside PKM for the use cases they cover.
- **`pkm`** is the Peios module.

Distributors building a Peios kernel must include this stack. Building a kernel with SELinux enabled and active would produce a system where PKM cannot activate — boot would fail with a clear error.

## Module signing

`CONFIG_MODULE_SIG_FORCE=y` is required. This flag tells the kernel to refuse to load any kernel module that is not signed by a key the kernel recognises.

The reasoning: a kernel module runs with full kernel privileges. An attacker who can load arbitrary kernel modules bypasses every layer of PIP and KACS — they can read memory directly, modify any data structure, disable any check. The defence against this is to refuse to load unsigned modules.

`CONFIG_MODULE_SIG_FORCE=y` is the kernel-level switch that enforces it. With the flag set, unsigned modules are rejected at load time; a malicious or buggy administrator with `SeLoadDriverPrivilege` cannot load a malicious module unless they have the signing key (and they don't — the signing key is the same TCB private key that signs the binaries, and it's not on a running system).

The flag is verified at kernel build time. A kernel built without it doesn't enforce the rule and is not a valid Peios kernel for security purposes; the PIP threat model relies on this enforcement.

User-visible effect: kernel modules from the Peios distribution work (they are signed); modules built ad-hoc on a running system do not load. Third-party kernel modules (a vendor driver, say) must be signed by a key the kernel trusts, which in practice means going through the Peios signing infrastructure to add them.

## Memory access restrictions

`CONFIG_STRICT_DEVMEM=y` is required. This flag restricts `/dev/mem` and `/dev/kmem` access — physical-memory mapping pseudo-devices — to specific I/O regions, denying read or write access to actual system RAM.

The reasoning: a process that can read physical memory bypasses PIP. The DACL might say "this process cannot read the memory of authd"; the kernel's PIP check might agree; but if the process can `mmap` `/dev/mem` and read the corresponding physical pages, neither check matters. The defence is to restrict the device.

With `CONFIG_STRICT_DEVMEM=y`:

- `/dev/mem` is readable only for the kernel's defined I/O regions (memory-mapped I/O, the VGA framebuffer, etc.).
- General RAM is not readable through `/dev/mem`.
- `/dev/kmem` is unavailable.

This closes the physical-memory bypass for PIP. Combined with `CONFIG_MODULE_SIG_FORCE`, the two flags eliminate the kernel-level escapes from PIP that don't require an actual kernel compromise.

The flag is build-time; the kernel image either has it or doesn't. A kernel without it is not a valid Peios kernel for security purposes.

## What the kernel will not have

The Peios kernel is built with specific things **excluded**:

- **`CONFIG_BPF_LSM=n`** — the BPF LSM is not built. BPF programs running as security modules would conflict with PKM and bypass its checks.
- **MAC LSMs disabled** — SELinux, AppArmor, SMACK, TOMOYO are all disabled. Their config flags are off.

These exclusions are part of the kernel image. A distribution that includes these LSMs in its kernel image is not running Peios's intended security model.

## What about user-space hardening

A few things are explicit in the Peios environment that aren't strictly kernel invariants but are operational expectations:

- **`peinit` is signed at TCB level.** If the binary peinit is exec'd from is not signed at TCB, the kernel's verification at exec sets `pip_type = None`. peinit then runs unprotected, and any other process can interfere with it. This is operationally untenable; a properly-built Peios image has peinit signed.
- **`authd`, `loregd`, `eventd`, `lpsd` are signed at TCB level.** Same reasoning. These are the TCB daemons; they need PIP protection to function in their role.
- **No kernel modules are loaded other than signed ones.** Per `CONFIG_MODULE_SIG_FORCE`.

These are not enforced at boot in the sense of "the boot will fail" if violated — they are operational expectations. A Peios system where peinit is unsigned will boot, run, and "work" in a superficial sense; it just won't have the security properties Peios documents.

## The invariant verification

The kernel's init code does several checks at start:

1. **Verify PKM is in the LSM stack** and no incompatible LSM is present. PKM refuses to activate if violated.
2. **Verify `CONFIG_MODULE_SIG_FORCE` is set.** (This is a build-time flag; at runtime the kernel just behaves consistently with the build.)
3. **Verify `CONFIG_STRICT_DEVMEM` is set.** (Same; build-time.)
4. **Construct the SYSTEM and Anonymous tokens.** As covered in [Bootstrap tokens](~peios/boot-and-trust-establishment/bootstrap-tokens).
5. **Attach the SYSTEM token to init.** Init becomes the first process holding it.
6. **Start userspace.** init execs the configured first program — **prelude**, the initramfs PID 1, which runs the initramfs and then execs the real init (peinit, in a normal Peios image). See [The initramfs stage](~peios/boot-and-trust-establishment/initramfs-stage).

By the time userspace starts, the invariants are either satisfied (boot proceeds normally) or violated (boot fails or the security model is broken). The verification is internal; from the operator's perspective, the system either comes up cleanly or doesn't.

## Failure modes

If an invariant fails:

- **MAC LSM detected at PKM init.** PKM refuses to activate. The kernel boots but the access control is effectively absent. peinit's exec verification (looking for a TCB signature) returns "valid" but no PIP is set because PKM isn't running. The system is unsafe.
- **`CONFIG_MODULE_SIG_FORCE=n`.** Modules can be loaded without signing. An attacker with `SeLoadDriverPrivilege` can load arbitrary kernel modules and bypass everything. PIP is no longer meaningful.
- **`CONFIG_STRICT_DEVMEM=n`.** `/dev/mem` can read physical memory. Any process with `READ_CONTROL` on `/dev/mem` (or whose DACL grants it) can bypass PIP by reading memory directly.

Each failure mode is a security regression. The boot chain depends on the invariants holding. A deployment that needs to be sure its security model is operating correctly verifies these as part of the boot validation — typically via a post-boot tool that reads `/proc/sys/kernel/lsm`, checks build-time flags via the kernel config, etc.

For most Peios deployments built from the official kernel image, the invariants hold by construction. The verification is mostly relevant for custom kernels built from source — anyone modifying the kernel image needs to know which flags they cannot change.

## Why these invariants

Two themes underlie all of these:

**The trust chain is rooted in kernel integrity.** SYSTEM token, PIP, signed binaries — every layer of the model assumes the kernel is honest. If the kernel can be modified at runtime (unsigned modules), or its memory can be read or written from userspace (`/dev/mem`), the foundation crumbles.

**PKM must be the sole authoritative LSM.** Trying to compose PKM with MAC LSMs would give either over-restrictive or inconsistent semantics; the Peios access model is built on PKM's decisions, and that requires PKM to make the decisions alone.

The invariants are what make these themes operational: the kernel is built and initialised in ways that protect itself from runtime modification and that ensure PKM is in charge.
