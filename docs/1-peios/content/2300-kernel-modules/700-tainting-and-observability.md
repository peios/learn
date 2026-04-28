---
title: Tainting and Observability
type: concept
description: The kernel-tainted flag bitfield — what each bit means, when it's set, how it's surfaced, and how taint events flow into audit.
related:
  - peios/kernel-modules/signing-and-trust
  - peios/kernel-modules/loading-and-unloading
  - peios/auditing
---

The kernel maintains a bitfield of **taint flags** recording "irregular things have happened to this kernel since boot." Tainting is purely diagnostic — it does not change the kernel's behaviour, it just records what's been done. Once a bit is set, it stays set until reboot.

## Why taint flags exist

When something goes wrong with the kernel — a crash, an oops, weird behaviour — the support process is "send us your logs." Knowing whether the kernel had been tainted (and how) tells the maintainer "your kernel had a proprietary driver loaded, we can't reason about its state" or "you forced a module unload at some point, this is consistent with the corruption pattern we're seeing." Taint flags are a cheap, persistent observability channel for support and forensic purposes.

## The taint bits

Peios replicates the Linux taint bitfield verbatim. Each bit means the same thing on Peios as on Linux, so existing Linux-aware tooling reads the bitfield without modification.

| Symbol | Meaning |
|---|---|
| `TAINT_PROPRIETARY_MODULE` | A module declaring a non-GPL-compatible license has been loaded. |
| `TAINT_FORCED_MODULE` | A module was loaded with vermagic or modversions checks bypassed. (Not reachable on standard Peios server builds — the bypass flags are ignored.) |
| `TAINT_UNSAFE_SMP` | The kernel detected an unsafe SMP configuration. |
| `TAINT_FORCED_RMMOD` | Forced module unload was used. (Not reachable on standard Peios server builds — forced unload is compiled out.) |
| `TAINT_MACHINE_CHECK` | A machine check exception occurred. |
| `TAINT_BAD_PAGE` | The kernel encountered a bad page. |
| `TAINT_USER` | A user-mode program requested kernel taint via `/proc/sys/kernel/tainted` write. |
| `TAINT_DIE` | A kernel oops or panic occurred. |
| `TAINT_OVERRIDDEN_ACPI_TABLE` | An ACPI table was overridden by user-supplied data. |
| `TAINT_WARN` | A `WARN_ON()` triggered. |
| `TAINT_CRAP` | A staging-tree module was loaded. |
| `TAINT_FIRMWARE_WORKAROUND` | A firmware-bug workaround was used. |
| `TAINT_OOT_MODULE` | An out-of-tree module was loaded (a module without `intree=Y` in its `.modinfo`). |
| `TAINT_UNSIGNED_MODULE` | An unsigned module was loaded under `warn` signing policy. |
| `TAINT_SOFTLOCKUP` | A soft-lockup was detected. |
| `TAINT_LIVEPATCH` | A live patch has been applied. (Not reachable on standard Peios server builds — livepatching is compiled out.) |
| `TAINT_AUX` | Auxiliary taint, kernel-defined uses. |
| `TAINT_RANDSTRUCT` | Built with `randstruct` plugin and the layout matched. |

Some bits are only reachable when specific kernel features are compiled in or specific events happen. On standard Peios server builds, `TAINT_FORCED_MODULE`, `TAINT_FORCED_RMMOD`, and `TAINT_LIVEPATCH` are not reachable because the underlying mechanisms (forced load, forced unload, livepatching) are compiled out — but the bits remain in the bitfield for compatibility with monitoring tools that interpret it.

## Surfacing the taint state

Two interfaces expose the current taint state:

- **`/proc/sys/kernel/tainted`** — text-mode file, read returns the integer bitmask. The standard Linux interface; Linux monitoring tools read this directly.
- **`/proc/sys/kernel/tainted_chars`** (where supported) — character-mode representation, one character per non-zero bit (e.g. `P` for proprietary, `O` for OOT).

Reading either of these is unprivileged. The taint state is broadly considered observability data, not sensitive — knowing that a kernel has been tainted by `TAINT_OOT_MODULE` doesn't reveal anything beyond what `lsmod` would.

## Auditing taint events

While the taint bitfield is observability rather than enforcement, *transitions* into a tainted state are security-relevant: they mark "irregular state has been entered" and ops needs to know.

Peios audits taint-set transitions through the kernel module event audit subsystem. When a previously-clear taint bit gets set, an audit record is generated containing:

- The taint bit being set (symbolic name).
- The triggering event (module name and properties for module-related taints; subsystem identifier for others).
- The actor token, where there is one (module loads have a calling token; non-actor-driven events like `TAINT_BAD_PAGE` do not).
- A timestamp and sequence number.

Repeated triggers of the same already-set bit are not re-audited (the first transition was the security event; subsequent triggers are noise). A reboot resets all bits and re-arms the audit.

### Registry-driven audit configuration

The audit knob is at `\System\Audit\Modules\TaintEvents` with the standard quartet:

| Value | Behaviour |
|---|---|
| `enabled` (default) | All taint-set transitions audited. |
| `success-only` | Same as `enabled` (taint events have no success/failure axis). |
| `failure-only` | Same as `enabled`. |
| `disabled` | No taint-set events audited. |

The default is `enabled` because the volume is genuinely low (taints are sticky, set rarely) and the value is high (each event marks a meaningful posture change). Forensic environments may set higher-tier capture; lab environments running with proprietary drivers as a matter of course may set `disabled` to reduce noise.

## See also

- [Signing and trust](signing-and-trust) — `TAINT_UNSIGNED_MODULE` is set when an unsigned module loads under `warn` signing policy.
- [Loading and unloading](loading-and-unloading) — `TAINT_PROPRIETARY_MODULE` and `TAINT_OOT_MODULE` are set when relevant modules complete a successful load.
- [Auditing](../auditing) — the audit subsystem that consumes taint-set events.
