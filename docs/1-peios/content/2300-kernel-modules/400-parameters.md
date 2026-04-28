---
title: Module Parameters
type: concept
description: Module-declared tunables — load-time and runtime — and the file-SD model that governs their mutation.
related:
  - peios/kernel-modules/loading-and-unloading
  - peios/kernel-modules/overview-and-design
---

Modules can declare **parameters** — typed tunables that affect the module's behaviour. Parameters are useful for debug levels, feature toggles, and timing knobs that ops may need to adjust without rebuilding the module.

## Declaration

Parameters are declared in module source code with the `module_param()` macro:

```c
static int debug_level = 0;
module_param(debug_level, int, 0644);
MODULE_PARM_DESC(debug_level, "Diagnostic verbosity level (0-3)");

static char *driver_mode = "auto";
module_param(driver_mode, charp, 0644);
MODULE_PARM_DESC(driver_mode, "Driver mode: auto, manual, disabled");
```

Three pieces of metadata travel with the parameter:

| Component | Purpose |
|---|---|
| Type | One of `bool`, `int`, `uint`, `long`, `ulong`, `charp` (string), `array`, `byte`, `short`, etc. The kernel parses incoming text representations into the typed storage. |
| Permissions | Octal mode bits applied to the parameter's sysfs file. `0` means "no sysfs entry; load-time-only." Non-zero means "sysfs file with these permissions." |
| Description | Free-form documentation, surfaced via `modinfo`. |

The permissions value is the module author's declaration of "is this parameter runtime-mutable?" A parameter declared with `0` or `0444` (read-only) cannot be changed at runtime regardless of how the system is configured — the module author has decided the value is fixed once the module loads.

## Setting parameters at load time

Parameters can be set at module load via:

- **`modprobe foo bar=42 baz=true`** — passed to `init_module` as the parameter string.
- **Kernel command line: `foo.bar=42`** — for modules loaded during early boot from the initramfs.
- **`/etc/modprobe.d/*.conf`** — `options foo bar=42` lines, picked up by `modprobe` and applied at load.

Load-time parameters apply before the module's `init` function runs, so the module sees its configured values from the moment it starts.

## Setting parameters at runtime

Parameters whose declaration permits writing are exposed in sysfs at:

```
/sys/module/<name>/parameters/<param-name>
```

The file represents the parameter's current value. Reading the file returns the current value as text; writing the file sets a new value (the kernel parses the written bytes against the declared type and either accepts or rejects).

Reading is broadly permitted — observability into module state is generally useful and non-sensitive. Writing is **gated by the file's SD**, which by default has a restrictive DACL granting `FILE_WRITE_DATA` only to:

- `LocalSystem`
- `Administrators`

This DACL is the gate for runtime parameter mutation. There is no separate privilege gate — the file SD is the gate.

This composes with the broader Peios sysfs SD model: writes to anything under `/sys/` are restricted at the file-SD layer, and the same pattern applies to module parameter files.

## Module author retains override authority

The module author's declaration is sticky. A parameter declared with permissions `0` (no sysfs entry) cannot be made writable by any DACL change — the file simply doesn't exist. A parameter declared `0444` (read-only) cannot be made writable — the file's mode is read-only at the kernel level, below any DACL machinery.

The DACL only governs writes when the module exposes the parameter as runtime-mutable in the first place. The author's intent (load-time-only / read-only / writable) is preserved across configuration changes.

## Parameter changes are observable

Writes to module parameter sysfs files generate audit events through the standard sysfs-write audit path:

- Caller token (after truth-projection per the audit model).
- Target file path (`/sys/module/<name>/parameters/<param>`).
- New value (the bytes written).

These events are subject to the standard sysfs-audit registry knob (`\System\Audit\Sysfs\WriteEvents`). For modules whose parameters are security-relevant (e.g. an LSM-style module with an enforce/permissive toggle), per-file audit configuration on the SD enables higher-tier capture for that specific file.

## Default DACL inheritance

The default DACL for a module's parameter directory is set by the kernel when the module is registered. New parameters created when the module loads inherit from this default. Sysadmins who want to relax write access to specific parameters (e.g. permitting a service principal to write a particular tunable) may grant additional ACEs on a per-file basis after the module is loaded.

DACLs do not survive module unload — when the module is unloaded and the sysfs entries are torn down, then loaded again, the entries reappear with the default DACL. Persistent DACL changes for a parameter need to be re-applied after each module load. (Configuration management tooling typically does this automatically.)

## See also

- [Loading and unloading](loading-and-unloading) — where parameter values feed in during the load lifecycle.
- [Sysfs](../filesystems/sysfs) — the broader sysfs file-SD model that parameter files inherit from.
