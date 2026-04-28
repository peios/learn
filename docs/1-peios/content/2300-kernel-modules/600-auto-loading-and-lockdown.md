---
title: Auto-loading and Lockdown
type: concept
description: The request_module demand-load path, AutoLoadPolicy registry knob, blacklist mechanism, and the post-boot LockAfterBoot ratchet.
related:
  - peios/kernel-modules/loading-and-unloading
  - peios/kernel-modules/dependencies-and-metadata
  - peios/privileges/tcb
---

Beyond explicit `modprobe foo` invocations, the kernel can demand-load modules in response to events: hardware appearing, code paths needing functionality the kernel doesn't currently have. This page covers the demand-load mechanism, the policy that gates it, and the runtime ratchet that disables module operations entirely after boot.

## request_module: kernel-side demand load

When code inside the kernel needs a module that isn't currently loaded — a network protocol family the kernel doesn't have, a filesystem driver for a mount that's about to happen, a crypto algorithm that's been requested — the kernel calls `request_module(format, ...)`. This is not a syscall but a kernel-internal helper.

The implementation:

1. The format string + arguments produces a module name or alias (`"net-pf-17"`, `"fs-ext4"`, `"crypto-aes-x86_64"`).
2. The kernel writes a request to a userspace helper. By default this is `/sbin/modprobe` (typically a `kmod` symlink), configurable through the `kernel.modprobe` registry knob.
3. The userspace helper consults `modules.alias` and `modules.dep`, finds the matching module, and calls `finit_module`.
4. The module loads (subject to all the standard checks: `SeLoadDriverPrivilege` on the helper's token, signature verification, vermagic, etc.).
5. The kernel-internal code that called `request_module` retries the operation that triggered the demand.

### Common demand-load triggers

| Trigger | Module name format |
|---|---|
| `socket(AF_X, ...)` for an unloaded protocol family | `net-pf-N` (where N is the family number) |
| `mount` of a filesystem type whose driver is unloaded | `fs-NAME` |
| Crypto algorithm requested but not registered | `crypto-NAME` |
| Hardware device appearing on a bus | The device's `MODULE_ALIAS` string (e.g. `pci:v00008086d000010C9*`) |
| Specific kernel features (TUN/TAP, dummy net, etc.) | Various subsystem-defined formats |

## Auto-load policy

Linux's default behaviour is to demand-load whenever `request_module` is called, with no policy gate beyond standard module-load checks. This is convenient but creates an attack-surface multiplier: any unprivileged code path that opens a socket of an unusual protocol family demands the kernel load a module — and any vulnerability in that module becomes exploitable by any caller who can trigger the load.

Peios exposes a registry-driven policy controlling when demand loads are honoured:

| Mode | Behaviour |
|---|---|
| `enabled` (default) | Linux behaviour. Any `request_module` call is honoured, subject to standard module-load checks. |
| `allow-list` | Demand loads succeed only for module names matching the allow-list. Other demand loads fail (returning the original operation's "module not available" error). |
| `disabled` | Auto-loading is turned off entirely. `request_module` returns failure regardless of caller. Modules must be loaded explicitly via `init_module`/`finit_module` by a token holding `SeLoadDriverPrivilege`. |

The default is `enabled` to match Linux behaviour and avoid surprising compatibility breakage on workloads that rely on demand-loaded protocol families or filesystems. Customers running locked-down workloads who want to harden may set `allow-list` (with a curated set of modules permitted) or `disabled` (with all needed modules pre-loaded at boot).

### Registry knobs

| Path | Purpose |
|---|---|
| `\System\Modules\AutoLoadPolicy` | One of `enabled` / `allow-list` / `disabled`. |
| `\System\Modules\AutoLoadAllowed` | Subkey containing one entry per allow-listed module name; consulted when `AutoLoadPolicy` is `allow-list`. |

Both keys have restrictive DACLs granting `KEY_SET_VALUE` to `LocalSystem` and `Administrators`. They are Superlock candidates when that mechanism ships.

### Operational considerations

Switching to `allow-list` or `disabled` interacts with several common Linux behaviours:

- **Sockets for unloaded protocol families** return `EAFNOSUPPORT` rather than triggering a load. Applications that rely on demand-loaded protocols need to explicitly load modules at boot or via service start.
- **Filesystem mounts** for unloaded filesystem drivers fail. Mount-time loading needs to be replaced by explicit pre-loading.
- **Hardware hot-add** cannot auto-attach a driver that isn't on the allow-list. Servers with stable hardware sets are mostly unaffected; environments with hot-add hardware need to enumerate expected drivers.

For a server with a known, stable workload, `disabled` is operationally clean: every needed module is loaded at boot, runtime loading is unnecessary. For more dynamic environments, `allow-list` lets ops describe an explicit whitelist.

## Module blacklist

Independent of the auto-load policy, the **blacklist** lets ops mark specific modules as "never load." A module on the blacklist will not load even via explicit `modprobe`, even by a holder of `SeLoadDriverPrivilege`, until the blacklist entry is removed.

Blacklist sources, applied in order:

| Source | Format |
|---|---|
| Kernel command line: `modprobe.blacklist=foo,bar` | Comma-separated module names blocked for this boot. |
| `/etc/modprobe.d/*.conf` files containing `blacklist <name>` directives | Persisted across boots; written by ops. |
| Registry: `\System\Modules\Blacklist` subkey | Peios-native equivalent of the modprobe.d mechanism, registry-driven via ksyncd. |

The Linux idiom `install <name> /bin/false` (a modprobe.d directive that maps a module-load attempt to running `/bin/false`, which fails) is supported for compatibility but is functionally equivalent to a blacklist entry.

Blacklist entries are advisory in the sense that nothing prevents `init_module` / `finit_module` from being called with the module's bytes — the blacklist is consulted by `modprobe`, not by the kernel itself. Code that goes around `modprobe` and calls the syscalls directly with the right module bytes will not be blocked. The blacklist is therefore a configuration mechanism for the standard load path, not a security boundary.

## Post-boot lockdown: LockAfterBoot

For environments that want the strongest possible "no-runtime-kernel-mutation" posture, Peios exposes a one-way ratchet that **disables all module operations entirely** after early boot completes.

### The mechanism

The kernel has a runtime flag `module_loading_locked`. When set:

- All `init_module` / `finit_module` calls return `EPERM`.
- All `delete_module` calls return `EPERM`.
- All `request_module` calls return failure regardless of caller or `AutoLoadPolicy`.

Once set, this flag **cannot be cleared at runtime**. It can only be reset by rebooting. The ratchet is one-way.

### How it gets set

Two paths:

1. **Registry knob `\System\Modules\LockAfterBoot`** — when set to `true`, peinit (or the equivalent boot orchestrator) sets `module_loading_locked = true` after the boot-time module set has finished loading. From that point, no further module operations succeed for the rest of the boot.

2. **Runtime API** — a privileged process holding `SeTcbPrivilege` may flip the flag mid-boot via a dedicated kernel syscall. This lets a service explicitly say "I'm done loading my modules; lock down now" without waiting for an external orchestrator.

The default is `LockAfterBoot=false` — matching Linux's default behaviour where module operations remain available throughout the kernel's lifetime.

### Why this is `SeTcbPrivilege`, not `SeLoadDriverPrivilege`

Flipping the gate that controls who can load modules is a higher-tier operation than module loading itself. An actor that can flip the lock can affect the security posture of every subsequent module operation in the boot. `SeTcbPrivilege` is the authority appropriate for that scope of change.

### Audit

Setting `module_loading_locked` is a security-relevant event, audited unconditionally. The audit record captures:

- The actor token (after truth-projection).
- The path that triggered the set: registry-driven, runtime-syscall, or boot-orchestrator-step.

## See also

- [Loading and unloading](loading-and-unloading) — the underlying load mechanism that `request_module` invokes.
- [Dependencies and metadata](dependencies-and-metadata) — `modules.alias` is the data structure consulted by demand-loading.
- [SeTcbPrivilege](../privileges/tcb) — the privilege required for the runtime lockdown ratchet.
