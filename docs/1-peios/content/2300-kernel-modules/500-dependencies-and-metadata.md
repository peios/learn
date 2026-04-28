---
title: Module Dependencies and Metadata
type: concept
description: How modules declare dependencies and exports, the depmod-built dependency database, vermagic and modversions ABI checks, and EXPORT_SYMBOL_GPL semantics.
related:
  - peios/kernel-modules/loading-and-unloading
  - peios/kernel-modules/auto-loading-and-lockdown
---

A module is rarely standalone. It typically imports symbols from the kernel core or from other modules, and it advertises symbols other modules can use. The module subsystem maintains the metadata describing these relationships and validates them at load time.

## Symbol exports

A kernel function or variable becomes loadable-into by other code through one of two macros:

| Macro | Resolvable by |
|---|---|
| `EXPORT_SYMBOL(name)` | Any loaded module, regardless of declared license. |
| `EXPORT_SYMBOL_GPL(name)` | Only modules whose `MODULE_LICENSE` declaration is on the GPL-compatible list (`"GPL"`, `"GPL v2"`, `"Dual BSD/GPL"`, `"Dual MIT/GPL"`, etc.). |

The kernel maintains the exported-symbol table at runtime. When a module loads, the kernel walks the module's import list and looks up each symbol — if it's exported via `EXPORT_SYMBOL_GPL` and the loading module's license is not GPL-compatible, the resolution fails and the load is rejected with an unresolved-symbol error.

This split is preserved on Peios for **Linux ABI compatibility**. Linux modules that import GPL-only symbols expect the Linux semantics. Peios honours the same gate so that modules' behaviour matches what their authors targeted.

For Peios's own future kernel ABI (separate from the Linux compatibility surface), the export distinction will be **stable / experimental** rather than license-based — that is, "this symbol's signature is committed-to" versus "this symbol may change between kernel versions." The license-based gate is a Linux-historical artifact that doesn't apply to Peios's own design.

## Module metadata in the .ko

Every module embeds metadata in a `.modinfo` ELF section, structured as null-terminated `key=value` strings:

| Key | Purpose |
|---|---|
| `license` | License declaration. Affects GPL-symbol resolvability. |
| `vermagic` | Kernel version + compiler + critical config flags string. |
| `srcversion` | Hash of the source the module was built from. |
| `depends` | Comma-separated list of module names this module depends on. |
| `alias` | One or more device-identification strings the module handles (e.g. `pci:v00008086d000010C9*`). Used by `modprobe` for auto-loading. |
| `parmtype` | Per-parameter type info, one entry per parameter. |
| `parm` | Per-parameter description, one entry per parameter. |
| `intree` | Set to `Y` for modules built from the in-tree source, absent otherwise. Affects taint flags. |
| `signature` | Set when the module is signed. |

The `modinfo <module-name>.ko` userspace tool reads and pretty-prints this metadata.

## vermagic

The `vermagic` string is compiled into every module from a kernel header generated at kernel-build time. It includes:

- Kernel version (e.g. `6.5.0-peios`)
- SMP/preemption configuration (`SMP preempt mod_unload`)
- GCC/Clang version used to build the kernel
- A few critical config flags (e.g. `MODULE_UNLOAD`)

When a module loads, the kernel compares the module's vermagic with its own. **Mismatch fails the load** with a `vermagic` error. This catches the most basic form of "wrong-kernel module" — if you built the module against a different kernel version, vermagic will differ in the version-string portion alone.

vermagic is always-on in standard Peios builds. There is no opt-out, no flag to ignore vermagic mismatch. (The Linux flag `MODULE_INIT_IGNORE_VERMAGIC` is rejected — see [Loading and unloading](loading-and-unloading) on forced loading.)

## Modversions

Modversions (`CONFIG_MODVERSIONS`) is the finer-grained ABI compatibility check. For each symbol the kernel exports, the build process computes a CRC from the symbol's **type signature** — the function pointer prototype, struct layout, and any types referenced. The CRC is stored alongside the symbol name in the kernel's exported-symbol table.

A module that imports a symbol records, at build time, the CRC of the symbol as it was at the kernel's build moment. At load, the kernel compares the module's recorded CRC for each imported symbol against the kernel's current CRC for that symbol. **Mismatch fails the load.**

This catches a class of compatibility break that vermagic misses: if a kernel update changes a struct's layout but doesn't bump the version string, vermagic will pass but modversions will catch the layout change because the CRC will differ.

Modversions is enabled in standard Peios builds. As with vermagic, there is no runtime opt-out.

## The dependency database

Modules exist as `.ko` files under `/lib/modules/<kernel-version>/`. To efficiently answer queries like "which module provides this symbol?" or "what does this module depend on?", a dependency database is generated at install time by the `depmod` tool.

Files generated by `depmod`:

| File | Purpose |
|---|---|
| `modules.dep` / `modules.dep.bin` | Dependency graph: each module → list of modules it depends on. Used by `modprobe` to determine load order. |
| `modules.alias` / `modules.alias.bin` | Device-id alias → module mapping. Used for auto-loading drivers when matching hardware appears. |
| `modules.symbols` / `modules.symbols.bin` | Exported-symbol → module mapping. Used by `request_module` / `modprobe` to resolve symbol-name requests. |
| `modules.builtin` | List of modules compiled into the kernel image rather than as separate `.ko` files. The kernel reports these as "loaded" but they cannot be unloaded. |
| `modules.softdep` | Soft-dependency hints: "before loading X, also load Y." |

These files are regenerated by `depmod` whenever modules are installed or removed. The standard package-manager flow runs `depmod` automatically as part of post-install hooks.

## modules.builtin

Modules that are compiled directly into the kernel image (rather than as separate `.ko` files) are listed in `modules.builtin`. The kernel reports them through `/sys/module/<name>/` as "loaded" but they:

- Cannot be unloaded (their code is part of the immutable kernel image).
- Have no refcount (or, equivalently, a refcount of "permanent").
- Have no signature (they're part of the kernel itself, signed as part of the kernel image).

`modprobe` consults `modules.builtin` before attempting a load — if the requested module is built-in, no load is needed, the request returns success immediately.

## modprobe and dependency resolution

The `modprobe` userspace tool is the standard interface for loading modules with their dependencies:

```
modprobe foo
```

Operations performed:

1. Look up `foo` in `modules.dep`. Discover that loading `foo` requires `bar` and `baz` already loaded.
2. Recursively resolve dependencies (load `bar`, then `baz`, then `foo`).
3. Apply parameters from `/etc/modprobe.d/*.conf` matching `foo`.
4. Open the module file, call `finit_module`.

The kernel's `request_module` path internally invokes `modprobe` for demand loading — see [Auto-loading and lockdown](auto-loading-and-lockdown).

## See also

- [Loading and unloading](loading-and-unloading) — where vermagic, modversions, and symbol resolution fit in the load lifecycle.
- [Auto-loading and lockdown](auto-loading-and-lockdown) — `modules.alias` and the demand-load path.
- [Tainting and observability](tainting-and-observability) — taint bits set when out-of-tree (`intree=Y` absent) modules load.
