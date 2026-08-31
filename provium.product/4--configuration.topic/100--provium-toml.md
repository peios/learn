---
title: provium.toml
type: reference
description: Every field in provium.toml — the [provium] section (roots, cache_dir, cache_max_size), the [profiles.<name>] blocks (kernel, root, initrd, cmdline, guest_os), and discovering profiles from a directory.
related:
  - provium/configuration/profiles
  - provium/configuration/dynamic-profiles
  - provium/getting-started/project-structure
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
cmdline = "console=ttyS0 quiet"
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
| path string | one of `kernel` / `root` | Path to a bzImage-format kernel image. Booted via QEMU's `-kernel` option. |

Path validation (does the file actually exist?) happens at VM-boot time, not config-load time. This lets a single `provium.toml` be portable across machines that have different kernel layouts.

May be omitted when [`root`](#root) names a composed Peios root, in which case the kernel is found inside it.

### `root`

```toml
[profiles.kernel-only]
root = "{out}/root"
```

| Type | Required | Description |
|---|---|---|
| path string | one of `kernel` / `root` | A composed Peios root — what `peiso root` writes. The kernel is taken from `usr/lib/modules/<release>/vmlinuz-<release>` inside it. |

Set this instead of `kernel` when the profile's [`build`](#build) composes a root, so the profile does not also have to know where in that root a kernel lands. A kernel version bump then moves nothing in the config. `kernel`, when set, wins.

Resolution happens at VM-boot time, after the build has run — which is the only order that works, since the build is what produces the root. Two kernels in one root is an error rather than a choice made quietly: set `kernel` to say which.

### `initrd`

```toml
[profiles.peios]
initrd = "/build/peios/initrd.cpio.gz"
```

| Type | Required | Description |
|---|---|---|
| path string | no | Path to an initramfs. Booted via QEMU's `-initrd`. Omit it to boot the agent overlay alone — see [No initrd at all](#no-initrd-at-all). |

By default, Provium injects the `provium-agent` binary at `/sbin/provium-agent` by concatenating a small overlay cpio onto your initrd at launch (the kernel unpacks concatenated gzip cpios into a single rootfs). The agent boots as PID 1 and forks immediately: the child becomes the vsock listener, the parent execs your initrd's `/init`, which therefore takes over PID 1. In this chained layout the agent deliberately mounts nothing first — your init owns the mount and pivot sequence exactly as it would alone. (Only on an agent-only initrd, with no user `/init`, does the agent perform the pseudo-FS mounts itself.) Userspace runs as it would have on its own; the agent runs alongside as PID 2.

Three consequences:

- **Your initrd doesn't need to know about Provium.** A vanilla distro initramfs, a buildroot image, or a from-scratch cpio with just `/init` will all work.
- **Your `/init` runs as PID 1.** If your tests need PID-1 init duties (signals, child reaping), they happen in your init as before.
- **The merged initrd is content-hash cached** under `<scratch_root>/agent-overlay-cache/<sha256>.cpio.gz`. Subsequent boots of the same `(initrd, overlay)` pair pay nothing.

To opt out (e.g. when your initrd already bundles an agent at the path Provium would set), set `inject_agent = false` on the profile.

#### No initrd at all

Omitting `initrd` means the VM has no userspace of its own: the agent overlay *is* the whole initramfs. Nothing is concatenated and nothing is cached — the overlay file is handed to QEMU as it stands. It carries the agent but no `/init`, so the agent comes up as PID 1 in its standalone mode and performs the pseudo-FS mounts itself.

That is the shape a kernel conformance suite wants, where the point is that nothing but the kernel is reachable from a test. It also saves such a project vendoring an initrd cpio it would never otherwise need.

`inject_agent = false` with no `initrd` is rejected: without injection there is no overlay to stand in for the missing file, and so nothing to boot.

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
cmdline = "console=ttyS0 quiet"
```

| Type | Required | Description |
|---|---|---|
| string | one of `cmdline` / `cmdline_file` | Inline kernel command line. May be empty or omitted **when `cmdline_file` is set** — the two compose. A profile with neither a non-empty `cmdline` nor a `cmdline_file` is rejected with `profile \`<name>\` has empty cmdline and no \`cmdline_file\`; set at least one`. |

`vm:boot({kernel_cmdline = "..."})` overrides the whole command line for one boot.

Provium **always appends `console=ttyS0`** if absent. The kernel happily uses multiple `console=` directives, so any user-set values are preserved alongside. The reason: the QEMU command wires the serial port into Provium's console capture, so the kernel's printk needs to land there for failure diagnostics to be visible. Without `console=ttyS0`, PID 1's `/dev/console` may resolve to a device QEMU doesn't capture, and writes to stderr can fail and crash userspace.

Common additions:

- `loglevel=7` — verbose kernel logging for debugging.
- `nokaslr` — for reproducible kernel addresses in panic dumps.
- `panic=1` — panic immediately rather than hanging on unrecoverable errors.

### `cmdline_file`

```toml
[profiles.peios]
cmdline_file = "../dist/peios-experimental-2026.8/root/usr/share/live-boot/cmdline"
cmdline      = "loglevel=7"   # optional; appended after the file
```

| Type | Required | Description |
|---|---|---|
| path string | one of `cmdline` / `cmdline_file` | Path to a file whose contents are the **base** command line — typically an image builder's generated `cmdline`. Read at VM-boot time; resolved relative to the current directory, like `kernel`/`initrd`. |

All whitespace in the file — including newlines — is collapsed to single spaces, then the inline `cmdline` (if any) is appended **after**. Because the kernel applies last-wins semantics to most repeated parameters (`init=`, `loglevel=`, …), an inline token overrides the file's value for those.

The point is to stop the command line from drifting. If a builder bakes `init=/usr/bin/protoinit` into the image's cmdline and you hand-copy that into `cmdline`, the two silently diverge the next time the builder changes. Pointing `cmdline_file` at the builder's output means Provium reads the authoritative value every boot. See [Dynamic profiles](~provium/configuration/dynamic-profiles#cmdline-from-the-builder).

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

### `build`

```toml
[profiles.peios]
build        = "peiso iso specs/peios.toml --out {out}"
kernel       = "{out}/root/usr/lib/modules/<release>/vmlinuz-<release>"
initrd       = "{out}/root/system/boot/initramfs.cpio.gz"
cmdline_file = "{out}/root/usr/share/live-boot/cmdline"
```

| Type | Default | Description |
|---|---|---|
| string | unset | Shell command (run with `sh -c`) that produces this profile's boot artifacts. Runs **once before any VM boots**. A non-zero exit aborts the run. |

The literal token `{out}` — in `build` and in the path fields — expands to this profile's build-output directory (see `build_out`), so the command's `--out` and the `kernel`/`initrd`/`cmdline_file` Provium later reads are the same path and cannot drift.

Provium tracks no staleness: the command runs every invocation. Making rebuilds cheap when nothing changed is the builder's job, not Provium's. Skip the hook with `--no-build`, or run it without booting via `provium prepare`. Full treatment on [Dynamic profiles](~provium/configuration/dynamic-profiles).

### `build_out`

```toml
[profiles.peios]
build_out = "/tmp/provium-builds/peios"
```

| Type | Default | Description |
|---|---|---|
| path string | `$XDG_CACHE_HOME/provium/builds/<profile>/` | The directory `{out}` expands to. |

When unset, the default base is resolved like the fixture cache — `$PROVIUM_BUILD_DIR`, then `$XDG_CACHE_HOME/provium/builds`, then `~/.cache/provium/builds`, then `/tmp/provium-builds` — with the profile name appended. Provium creates the directory before running `build` but **never wipes it**: the `build` command owns its contents (so it can keep its own incremental-build caches there).

## Multiple profiles

You can declare any number of `[profiles.<name>]` blocks; tests pick one by name per VM. Patterns for multi-profile setups (debug builds, cross-version testing, feature-flag gating) are on [Profiles](~provium/configuration/profiles).

### `from_dir`

```toml
[profiles]
from_dir = "profiles"
```

Reads profiles from a directory instead of writing them inline. Each subdirectory holding a `profile.provium.toml` is one profile, named after the directory:

```text
provium.toml
profiles/
  kernel-only/
    profile.provium.toml
  full-system/
    profile.provium.toml
```

gives the profiles `kernel-only` and `full-system`. A subdirectory *without* that file is not a profile and is skipped rather than rejected, so a profile directory may keep whatever else it needs beside its config. A `from_dir` that names a directory holding no profile at all is an error.

The file's contents are the fields above — everything from `[profiles.<name>]` except the name, which the directory supplies.

Adding a testset becomes `mkdir`, with nothing central to keep in sync. That matters most for a repository whose whole purpose is holding many of them.

`from_dir` and inline blocks may both appear. A discovered profile whose name collides with an inline one is an error, not a silent winner.

#### What a discovered profile's paths are relative to

Its own directory — both the paths it names and the directory its `build` runs in. An inline profile keeps resolving against Provium's current directory, as it always has.

This is the rule that makes a profile directory self-contained: it can be moved, copied or renamed and still mean what it says. It also means the same relative path means the same thing whether it is written in the shared config or in a profile beside it, which is not true if everything resolves against one directory.

`{out}` paths are exempt, since a build-output directory is absolute and has nothing to do with where the profile lives.

```toml
# profiles/kernel-only/profile.provium.toml
#
# Both specs are named relative to this directory, and the command runs
# here, so `../../peiso.toml` is the repository's.
# `--out` must not already exist, and Provium never wipes {out} —
# clearing it is the build's own job.
build   = "rm -rf {out}/root && peiso root ../../peiso.toml peiso.toml --out {out}/root"
root    = "{out}/root"
cmdline = "console=hvc0 quiet panic=1"
```

**Important:** the fixture cache key folds in EVERY profile's kernel + initrd identifier. Adding a new profile invalidates the entire fixture cache. This is intentional: a new kernel could behave differently, so existing fixtures are no longer trustworthy. See [Profiles — What happens to the cache when profiles change](~provium/configuration/profiles#what-happens-to-the-cache-when-profiles-change).

## Configuration loading

| Step | What happens |
|---|---|
| 1. Read | `provium.toml` is read from `--config <path>` (default `./provium.toml`). |
| 2. Parse | TOML is parsed. Parse errors include the file path. |
| 3. Validate | Each profile is validated (a non-empty `cmdline` **or** a `cmdline_file`; `guest_os = "peios"`). |
| 4. Expand | The `{out}` token in each profile's `build` command and path fields is replaced with that profile's resolved build-output directory. |
| 5. Use | The `Config` struct is wrapped in an `Arc` and passed to every file runner. |

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
cmdline  = "console=ttyS0 quiet panic=1"
guest_os = "peios"

[profiles.peios-mainline]
kernel   = "/srv/peios-builds/mainline/bzImage"
initrd   = "/srv/peios-builds/mainline/initrd.cpio.gz"
cmdline  = "console=ttyS0 quiet panic=1"
guest_os = "peios"

[profiles.peios-debug]
kernel   = "/srv/peios-builds/debug/bzImage"
initrd   = "/srv/peios-builds/debug/initrd.cpio.gz"
cmdline  = "console=ttyS0 debug loglevel=7 nokaslr panic=1"
guest_os = "peios"
```

This declares three profiles (production, mainline, debug), centralises the cache on a 200 GiB dedicated mount, and scans both `tests/` and `internal-tests/`.

## See also

- [Project structure](~provium/getting-started/project-structure) — the broader project layout.
- [VM reference](~provium/reference/vm) — `boot_opts.kernel_cmdline` overrides.
- [Profiles](~provium/configuration/profiles) — patterns for using multiple profiles.
