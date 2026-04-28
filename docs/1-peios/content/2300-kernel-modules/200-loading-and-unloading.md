---
title: Loading and Unloading Modules
type: concept
description: The load/unload syscalls, authority gate via SeLoadDriverPrivilege, the userspace helper path, reference counting, and forced unload policy.
related:
  - peios/kernel-modules/overview-and-design
  - peios/kernel-modules/signing-and-trust
  - peios/kernel-modules/dependencies-and-metadata
  - peios/privileges/load-driver
---

This page covers the mechanics of getting a module into and out of the running kernel.

## The interface

| Call | Purpose |
|---|---|
| `init_module(image, len, params)` | Load a module from an in-memory buffer. The caller has read the `.ko` into memory and passes the buffer plus a parameter string. |
| `finit_module(fd, params, flags)` | Load a module from an open file descriptor. The kernel reads the `.ko` directly from the fd. Modern preferred form — avoids userspace having to copy the bytes. |
| `delete_module(name, flags)` | Unload a module by name. |
| `request_module(format, ...)` | Kernel-internal call (not a syscall). Asks userspace to load a module on the kernel's behalf. See [Auto-loading and lockdown](auto-loading-and-lockdown) for the demand-load path. |

`finit_module` is the form used by every modern userspace loader. `init_module` exists for compatibility with very old code that read the module bytes itself.

## Authority: SeLoadDriverPrivilege

Every call into `init_module`, `finit_module`, or `delete_module` requires the calling token to hold `SeLoadDriverPrivilege`. The kernel checks the privilege before any of the loader's other work happens — privilege failure returns `EPERM` immediately.

The privilege is the **complete authority gate** — there is no SD on a "module loader" object, no per-module ACL, no separate check. Either the caller has the privilege and may attempt to load, or the call fails. The other gates (signature verification, vermagic check, dependency resolution) apply *after* the privilege check, gating *what* may be loaded rather than *who* may load.

`SeLoadDriverPrivilege` is held by default by:

- `Administrators`
- `LocalSystem`

Service principals that load drivers as part of their function (a hardware-management service that loads device drivers when devices appear, an init process that loads boot-time modules) are configured with this privilege explicitly. Ordinary application services do not hold it.

Unload is gated by the same privilege. The reasoning: an actor that can replace any kernel module (load + delete + load) already has the same effective authority as a module-load-only actor. Splitting the privileges would not reduce the attack surface meaningfully.

## The load lifecycle

A successful `finit_module` call goes through these stages:

1. **Privilege check.** Caller's token must hold `SeLoadDriverPrivilege`.
2. **Image read.** Kernel reads the module bytes from the supplied fd.
3. **Signature verification.** Per the active signing policy. See [Signing and trust](signing-and-trust).
4. **vermagic check.** Module's compiled-in kernel-version-and-config string is compared with the running kernel's. Mismatch fails the load. See [Dependencies and metadata](dependencies-and-metadata).
5. **Symbol resolution.** All symbols the module imports are matched against the kernel's exported symbol table. Unresolved symbol fails the load. `EXPORT_SYMBOL_GPL` symbols are only resolvable for modules whose declared license is GPL-compatible — preserved for Linux-ABI compatibility.
6. **Modversions check** (if enabled). Each imported symbol's CRC must match the kernel's exported CRC. Mismatch fails the load.
7. **Memory allocation.** Kernel allocates the module's text/data sections in kernel address space.
8. **`init` invocation.** The module's `module_init`-registered function runs. If it returns non-zero, the load is rolled back: the module is removed from the loaded list, its memory is freed, and the load fails with the init function's error code.
9. **Loaded.** The module appears in `/proc/modules` and `/sys/module/<name>/`.

Any of stages 3–8 failing rolls back the entire load. Partial loads are not possible — either the module loads completely or not at all.

## Reference counting

Once loaded, a module accumulates an in-kernel **reference count** representing the number of in-kernel objects that depend on the module being present. References are taken when:

- A device whose driver is provided by the module is opened.
- A filesystem mounted from the module is mounted.
- A kernel object (socket, key, etc.) registered by the module is created.
- Any other module that imports symbols from this module is loaded.

References are dropped when these objects close. A module's refcount reaches zero only when nothing in the kernel is currently using it.

`delete_module` checks the refcount: non-zero refcount returns `EBUSY` and the module stays loaded. This prevents the most obvious form of "module unloaded out from under code that was using it" panic.

## Forced unload

The Linux kernel optionally supports `rmmod -f`, which calls `delete_module` with the `O_TRUNC` flag and **bypasses the refcount check**. A module loaded into use is yanked out from under whatever was using it. The result is, almost always, a kernel panic — or much worse, silent memory corruption that crashes things minutes later.

This exists in Linux for a single use case: kernel-driver developers iterating on broken modules during development. It is not a production feature.

**Standard Peios server builds compile this out.** `CONFIG_PEIOS_MODULE_FORCE_UNLOAD=n` is baked in. The flags-bit that would request forced unload is ignored: `delete_module` always honours the refcount check regardless of flags. The capability does not exist in the running kernel.

This is stronger than gating it behind a privilege:

- A privilege gate adds runtime branches that would slow down every unload.
- A privilege that exists is a privilege that can be granted, leak, or be exploited.
- "The feature is compiled out" is the strongest possible "no."

Development variant builds (used for kernel module authors working on driver code) may opt the feature back in. The standard server tier does not.

## /proc/modules and /sys/module/

Two observability surfaces are populated by the load mechanism:

- `/proc/modules` — text format, one module per line: name, size, refcount, dependency-list, state, base-address. Equivalent to `lsmod` output.
- `/sys/module/<name>/` — directory per loaded module, containing files for refcount, parameters, sections, and module-specific attributes.

Reading these is unprivileged (modulo the broad sysfs DACL on the directory). They reveal which modules are loaded — useful information for both ops and (potentially) attackers fingerprinting the kernel. Peios does not coarsen or hide this beyond standard sysfs DACL gating.

## Userspace helpers

Module loading is rarely invoked directly by `init_module` syscall. The standard loader is `kmod`'s `modprobe`, which handles dependency resolution, alias lookup, and parameter parsing. The kernel's auto-load path also dispatches to `modprobe` for demand loading — see [Auto-loading and lockdown](auto-loading-and-lockdown).

`kmod` runs as a normal user-space process, holds whatever token the invoking caller has, and inherits `SeLoadDriverPrivilege` from that caller. There is no setuid path, no helper binary that elevates — the privilege travels with the calling token.

## See also

- [Signing and trust](signing-and-trust) — what verification the kernel performs in stage 3.
- [Dependencies and metadata](dependencies-and-metadata) — vermagic, modversions, EXPORT_SYMBOL semantics.
- [Auto-loading and lockdown](auto-loading-and-lockdown) — `request_module`, `kernel.modules_disabled`, runtime ratchet.
- [SeLoadDriverPrivilege](../privileges/load-driver) — the privilege specification.
