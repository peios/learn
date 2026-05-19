---
title: provium.toml
type: reference
description: Every field in provium.toml — the [provium] section (roots, cache_dir, cache_max_size) and the [profiles.<name>] blocks (kernel, initrd, cmdline, guest_os).
---

`provium.toml` is the only config file Provium reads. The default location is `./provium.toml`; override with `--config <path>`.

The schema has two top-level keys: `[provium]` for runner settings, and `[profiles.<name>]` for per-VM-type tuples. Both are optional individually — an empty `provium.toml` parses cleanly but won't be useful for anything (no profiles means `provium:vm(name, profile)` won't find any profile to look up).

## Minimum useful config

```toml
[provium]
roots = ["tests"]

[profiles.peios]
kernel  = "/path/to/bzImage"
initrd  = "/path/to/initrd.cpio.gz"
cmdline = "console=hvc0 quiet"
```

This declares one test root and one profile. `provium tests/` will scan `tests/` for `*.test.lua`, and tests can call `provium:vm("name", "peios")`.

## `[provium]` section

### `roots`

```toml
[provium]
roots = ["tests", "vendor/upstream-tests"]
```

| Type | Default | Description |
|---|---|---|
| array of strings | `[]` (empty) | Directories scanned for `*.test.lua` and `*.fixture.lua` files. Also prepended to `package.path` so `require("helper.module")` resolves under any root. |

When `roots` is empty (or unset), `provium <paths>` scans whichever paths you pass on the CLI; if you also omit those, it scans the current directory.

For most projects, set `roots = ["tests"]` (or whichever directory contains your tests) so that:

- `provium` (no arg) walks the test tree.
- `provium fixture build foo` finds `tests/foo.fixture.lua`.
- Tests can `require("helpers.assert_pingable")` and Provium resolves it as `tests/helpers/assert_pingable.lua`.

### `cache_dir`

```toml
[provium]
cache_dir = "/var/cache/provium/fixtures"
```

| Type | Default | Description |
|---|---|---|
| path string | `~/.cache/provium/fixtures` | Where fixture snapshots are stored. |

Useful for:

- Per-machine caches on shared hosts (default is per-user, set to a system-wide path for shared CI runners).
- Fast scratch storage (point at an SSD or tmpfs for build performance).
- Large dedicated cache (point at a partition with more headroom than `~/.cache`).

The directory is created on first build. If the path is unreadable / unwritable at startup, eviction silently skips and the next build attempt errors with the underlying I/O error.

### `cache_max_size`

```toml
[provium]
cache_max_size = "100G"
```

| Type | Default | Description |
|---|---|---|
| string with `K`/`M`/`G`/`T` suffix, or bare bytes | `"20G"` | LRU eviction target. The cache is allowed to grow beyond this between runs; eviction trims at the next `provium` startup. |

When the cache exceeds the cap, Provium sorts entries by access time and deletes oldest until total size is under the cap. Each successful restore bumps the entry's atime so popular fixtures stay hot.

## `[profiles.<name>]` blocks

Each `[profiles.<name>]` block declares one (kernel, initrd, cmdline, guest_os) tuple. Test code looks them up by name: `provium:vm("v", "<name>")`.

You can have any number of profiles; tests pick whichever they need.

### `kernel`

```toml
[profiles.peios]
kernel = "/build/peios/bzImage"
```

| Type | Required | Description |
|---|---|---|
| path string | yes | Path to a bzImage-format kernel image. Booted via QEMU's `-kernel` option. |

Path validation (does the file actually exist?) happens at VM-boot time, not config-load time. This lets a single `provium.toml` be portable across machines that have different kernel layouts.

### `initrd`

```toml
[profiles.peios]
initrd = "/build/peios/initrd.cpio.gz"
```

| Type | Required | Description |
|---|---|---|
| path string | yes | Path to an initramfs. Booted via QEMU's `-initrd`. |

By default, Provium injects the `provium-agent` binary at `/sbin/provium-agent` by concatenating a small overlay cpio onto your initrd at launch (the kernel unpacks concatenated gzip cpios into a single rootfs). The agent runs as PID 1, performs the standard pseudo-FS mounts, then forks: the child becomes the vsock listener, the parent execs your initrd's `/init`. Userspace runs as it would have on its own; the agent runs alongside as PID 2.

Three consequences:

- **Your initrd doesn't need to know about Provium.** A vanilla distro initramfs, a buildroot image, or a from-scratch cpio with just `/init` will all work.
- **Your `/init` runs as PID 1.** If your tests need PID-1 init duties (signals, child reaping), they happen in your init as before.
- **The merged initrd is content-hash cached** under `<scratch_root>/agent-overlay-cache/<sha256>.cpio.gz`. Subsequent boots of the same `(initrd, overlay)` pair pay nothing.

To opt out (e.g. when your initrd already bundles an agent at the path Provium would set), set `inject_agent = false` on the profile.

### `inject_agent`

```toml
[profiles.peios]
inject_agent = false
```

| Type | Default | Description |
|---|---|---|
| bool | `true` | When `true`, Provium concatenates the agent overlay onto `initrd` at launch and appends `rdinit=/sbin/provium-agent` to the kernel cmdline. Set `false` to use the initrd as-is. |

If your cmdline already pins a different `rdinit=PATH`, the launch errors with a clear conflict message rather than silently overriding. Either remove the conflicting `rdinit=`, or set `inject_agent = false`.

### `agent_overlay_path`

```toml
[profiles.peios]
agent_overlay_path = "/usr/local/share/provium/agent-overlay.cpio.gz"
```

| Type | Default | Description |
|---|---|---|
| path string | unset | Override the path to the agent overlay cpio. Useful for distribution-installed Provium where the overlay isn't co-located with the binary. |

When unset, Provium tries (in order): the `PROVIUM_OVERLAY` env var, then `<provium-binary-dir>/../share/provium/agent-overlay.cpio.gz`, then walks up the binary's directory tree looking for `dist/agent-overlay.cpio.gz` (covers in-development runs from `target/`). Set this field — or the env var — when none of those apply.

### `cmdline`

```toml
[profiles.peios]
cmdline = "console=hvc0 quiet"
```

| Type | Required | Description |
|---|---|---|
| string | yes (must be non-empty) | Default kernel command line. Empty cmdlines (or whitespace-only) are rejected with `profile \`<name>\` has empty cmdline`. |

`vm:boot({kernel_cmdline = "..."})` overrides this for one boot.

Provium **always appends `console=ttyS0`** if absent. The kernel happily uses multiple `console=` directives, so any user-set values are preserved alongside. The reason: the QEMU command wires the serial port into Provium's console capture, so the kernel's printk needs to land there for failure diagnostics to be visible. Without `console=ttyS0`, PID 1's `/dev/console` may resolve to a device QEMU doesn't capture, and writes to stderr can fail and crash userspace.

Common additions:

- `loglevel=7` — verbose kernel logging for debugging.
- `nokaslr` — for reproducible kernel addresses in panic dumps.
- `panic=1` — panic immediately rather than hanging on unrecoverable errors.

### `guest_os`

```toml
[profiles.peios]
guest_os = "peios"
```

| Type | Default | Description |
|---|---|---|
| string | `"peios"` | Guest OS identifier. v1 only supports `"peios"`. |

Validated at config load time. A profile with `guest_os = "linux"` (or any other value) errors with `profile \`<name>\` has guest_os = \`linux\`, only \`peios\` is supported in v1`.

The field exists to future-proof the schema for other ports — when there's a Windows agent, this would be how a profile selects it.

## Multiple profiles

```toml
[profiles.peios]
kernel  = "/build/peios/bzImage"
initrd  = "/build/peios/initrd.cpio.gz"
cmdline = "console=hvc0 quiet"

[profiles.peios-debug]
kernel  = "/build/peios-debug/bzImage"
initrd  = "/build/peios-debug/initrd.cpio.gz"
cmdline = "console=hvc0 debug loglevel=7 nokaslr"

[profiles.peios-stable]
kernel  = "/build/peios-stable/bzImage"
initrd  = "/build/peios-stable/initrd.cpio.gz"
cmdline = "console=hvc0 quiet"
```

Tests pick:

```lua
provium:vm("v",        "peios")          -- production-like
provium:vm("debug-v",  "peios-debug")    -- verbose, debuggable
provium:vm("stable-v", "peios-stable")   -- pinned older kernel
```

**Important:** the fixture cache key folds in EVERY profile's kernel + initrd identifier. Adding a new profile invalidates the entire fixture cache. This is intentional: a new kernel could behave differently, so existing fixtures are no longer trustworthy.

## Configuration loading

| Step | What happens |
|---|---|
| 1. Read | `provium.toml` is read from `--config <path>` (default `./provium.toml`). |
| 2. Parse | TOML is parsed. Parse errors include the file path. |
| 3. Validate | Each profile is validated (`cmdline` non-empty, `guest_os = "peios"`). |
| 4. Use | The `Config` struct is wrapped in an `Arc` and passed to every file runner. |

Errors:

| Error | Cause |
|---|---|
| `read \`<path>\`: <io error>` | File missing or unreadable. |
| `parse \`<path>\`: <toml error>` | Malformed TOML. |
| `invalid config in \`<path>\`: <message>` | Validation failed (empty `cmdline`, unsupported `guest_os`, etc.). |

All three abort the run with exit code `2`.

## Worked example

```toml
[provium]
roots          = ["tests", "internal-tests"]
cache_dir      = "/srv/provium-cache"
cache_max_size = "200G"

[profiles.peios]
kernel   = "/srv/peios-builds/latest/bzImage"
initrd   = "/srv/peios-builds/latest/initrd.cpio.gz"
cmdline  = "console=hvc0 quiet panic=1"
guest_os = "peios"

[profiles.peios-mainline]
kernel   = "/srv/peios-builds/mainline/bzImage"
initrd   = "/srv/peios-builds/mainline/initrd.cpio.gz"
cmdline  = "console=hvc0 quiet panic=1"
guest_os = "peios"

[profiles.peios-debug]
kernel   = "/srv/peios-builds/debug/bzImage"
initrd   = "/srv/peios-builds/debug/initrd.cpio.gz"
cmdline  = "console=hvc0 debug loglevel=7 nokaslr panic=1"
guest_os = "peios"
```

This declares three profiles (production, mainline, debug), centralises the cache on a 200 GiB dedicated mount, and scans both `tests/` and `internal-tests/`.

## See also

- [Project structure](~provium/getting-started/project-structure) — the broader project layout.
- [VM reference](~provium/reference/vm) — `boot_opts.kernel_cmdline` overrides.
- [Profiles](~provium/configuration/profiles) — patterns for using multiple profiles.
