---
title: Project Structure
type: concept
description: A Provium project is a directory with provium.toml, one or more test roots holding *.test.lua and *.fixture.lua files, and a per-user fixture cache. Nothing else is needed.
---

Provium has no scaffolding command. A project is whatever directory `provium.toml` lives in. This page documents what each piece does.

## Directory layout

```
my-project/
  provium.toml                  # Required. Profiles + scan roots.
  tests/                        # One of the directories listed in `roots`.
    smoke.test.lua              # Run by `provium`.
    networking/
      partition.test.lua
      uplink.test.lua
    helpers/
      assert_pingable.lua       # `require("helpers.assert_pingable")`
    fixtures/
      booted-pair.fixture.lua   # Built once, restored per test.
  ~/.cache/provium/
    fixtures/                   # Per-user fixture cache.
      <hash>.snap               # Single-VM fixture snapshots.
      <hash>.lab/               # Multi-VM lab-fixture directories.
    rerun.json                  # `--rerun-failed` state.
```

The only required file is `provium.toml`. Tests, helpers, and fixtures all live under whatever directory you list in `[provium].roots`.

## `provium.toml`

The configuration file at the project root. Two sections:

```toml
[provium]
roots = ["tests", "vendor/upstream-tests"]
cache_dir       = "/var/cache/provium/fixtures"   # optional
cache_max_size  = "20G"                            # optional

[profiles.peios]
kernel   = "/build/peios/bzImage"
initrd   = "/build/peios/initrd.cpio.gz"
cmdline  = "console=hvc0 quiet"
guest_os = "peios"

[profiles.peios-debug]
kernel   = "/build/peios-debug/bzImage"
initrd   = "/build/peios-debug/initrd.cpio.gz"
cmdline  = "console=hvc0 debug loglevel=7"
```

`[profiles.<name>]` blocks declare named (kernel, initrd, cmdline) tuples. Test code looks them up by name: `provium:vm("a", "peios")` boots the VM using `[profiles.peios]`. You can have any number of profiles; tests pick whichever they need.

`[provium].roots` is the list of directories scanned for `*.test.lua` files. It also controls where `require("helper.module")` resolves; `helpers/foo.lua` under any root is reachable as `require("helpers.foo")`.

`cache_dir` and `cache_max_size` configure where fixture snapshots are stored and how big the cache is allowed to grow. Defaults: `~/.cache/provium/fixtures/`, `20 GiB`. See [provium.toml reference](~provium/configuration/provium-toml) for full detail.

## Test files

Files matching `*.test.lua` under any `roots` directory are picked up by `provium`. Each file is run in a fresh Lua state with a fresh root `Lab`.

A test file consists of `test(name, [meta,] fn)` calls. Tests run in declaration order, and each test runs sequentially (one at a time within a file). The harness builds a fresh `t` context for each test and passes it as the function's first argument.

```lua
test("simple", function(t)
    t:assert_eq(1 + 1, 2)
end)

test("with metadata", {tags = {"smoke"}, timeout = "30s"}, function(t)
    t:assert(true)
end)

test("declaratively skipped", {skip = "still figuring out the spec"}, function(t)
    -- never runs
end)
```

See [the test-framework reference](~provium/reference/test-framework) for `test()`, the `t` context, `todo()`, and `wait_until()`.

## Fixture files

Files matching `*.fixture.lua` are not picked up by the test runner directly. Instead, test files reference them by name:

```lua
test("uses a pre-booted VM", function(t)
    local vm = provium:vm_fixture("booted-base")
    -- vm is restored from a cached snapshot
end)
```

When the test runs, Provium:

1. Locates `<root>/booted-base.fixture.lua` (under any `roots` directory).
2. Hashes the file's source bytes plus every transitive dependency (other fixtures it references via `vm_fixture`/`lab_fixture`, plus every helper it `require`s) plus every profile's kernel and initrd identifier into a cache key.
3. Looks up `<cache_dir>/<key>.snap`. If present, restores it and hands the test a fresh VM.
4. If absent, builds the fixture by running its chunk under a build-time Lua state, takes the resulting snapshot, sparse-zstd-compresses it, and installs it into the cache.

A fixture file's chunk must end in a `return` statement that hands back either a `vm:snapshot()` (single VM) or a `provium:snapshot()` (whole lab). Example:

```lua
-- booted-base.fixture.lua
local vm = provium:vm("base", "peios"):boot()
vm:run("apk add curl"):assert_ok()
return vm:snapshot()
```

See [fixtures and dependencies](~provium/running-tests/fixtures-and-dependencies) for the cache lifecycle, eviction policy, and what triggers a rebuild.

## Helper files

Plain Lua files anywhere under a `roots` directory are reachable through `require`. The `roots` directories are prepended to `package.path` at file-runner setup, so `tests/helpers/assert_pingable.lua` can be loaded as:

```lua
local pingable = require("helpers.assert_pingable")
```

Helpers are not detected as tests (they don't end in `.test.lua`) and not detected as fixtures. Editing a helper invalidates the cache key of every fixture that transitively requires it.

## The fixture cache

```
~/.cache/provium/fixtures/
  c5e6f8….snap           # Single-VM fixture snapshot (sparse, zstd).
  c5e6f8….snap.lock      # Per-key build lock.
  abc123….lab/           # Lab-fixture directory.
    lab.json             # Per-VM snapshot index.
    base.snap            # Per-VM snapshot.
    extra.snap
  abc123….lab.lock
```

The cache is per-user by default (`~/.cache/provium/fixtures/`). Override it system-wide with `[provium].cache_dir` in `provium.toml`. The cache is shared across runs and across files within a run — concurrent file runners building the same fixture coordinate via the per-key lock file.

LRU eviction runs at `provium` startup before tests dispatch: the harness sums file sizes under `cache_dir`, sorts entries by access time, and deletes the oldest until the total is under `cache_max_size`.

Inspect or manage the cache from the CLI:

```
provium fixture list      # Show every cached entry, with sizes.
provium fixture build P   # Force-build the named fixture.
provium fixture rebuild P # Evict and rebuild.
provium fixture clean     # Wipe the cache.
provium fixture stale     # List fixtures whose source hashes don't match any cache entry.
```

## The rerun state file

After every run that produced at least one failure, Provium writes the canonical paths of the failing files to `~/.cache/provium/rerun.json` (override with `$PROVIUM_RERUN_STATE`). The `--rerun-failed` flag intersects discovered files against this list, so:

```
provium tests/ --rerun-failed
```

re-runs only files that failed last time. A clean run leaves the file alone, so the failed set persists until you fix the failures.

## Required external binaries

| Binary | Used for | Provided by |
|---|---|---|
| `qemu-system-x86_64` | VMM backend | `qemu-system-x86` package |
| `ip` | Bridge / TAP / link operations | `iproute2` |
| `tc` | Latency / drop-rate / bandwidth qdiscs | `iproute2` |
| `nft` | Per-bridge partition rules, NAT for uplink | `nftables` |
| `tcpdump` | `bridge:capture()` and `nic:capture()` | `tcpdump` |

Provium's startup pre-flight checks for `/dev/kvm`, `/dev/vhost-vsock`, `ip`, `tc`, `nft`, `qemu-system-x86_64`, and effective `CAP_NET_ADMIN`. Missing pieces fail with an actionable message; nothing is checked lazily at first-use.

## What lives outside the project tree

- The fixture cache (default: `~/.cache/provium/fixtures/`).
- The rerun-state file (default: `~/.cache/provium/rerun.json`).
- Optional `--save-events` / `--events-socket` paths (your choice).
- The kernel and initrd files referenced by `[profiles.<name>]`.

Everything else — tests, fixtures, helpers, configuration — lives inside the project directory and is the project author's responsibility to keep version-controlled.
