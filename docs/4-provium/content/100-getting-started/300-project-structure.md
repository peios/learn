---
title: Project Structure
type: concept
description: A Provium project is organized into a configuration file, test scripts, fixtures, and optional helper libraries.
---

A Provium project follows a simple directory layout. There is no scaffolding command — you create the directories yourself.

## Directory layout

```
my-tests/
  provium.toml             # Profile definitions (required)
  tests/                   # Test scripts (required)
    boot.lua               # Test file
    syscalls.lua           # Test file
    helpers.lua            # Shared helper library (not a test)
    fixtures/              # Fixture scripts (not run as tests)
      ready.lua            # Fixture definition
  testdata/                # Test assets (optional)
    rootfs.cpio.gz         # Initramfs image
    disk.img               # Disk image
```

## provium.toml

The configuration file defines **profiles** — named combinations of kernel, initramfs, and init binary. Profiles describe what to boot, not how much hardware to allocate.

```toml
[profile.minimal]
kernel = "../kernel/out/bzImage"
initrd = "testdata/rootfs.cpio.gz"
init = "/sbin/init"

[profile.peinit]
kernel = "../kernel/out/bzImage"
initrd = "testdata/rootfs.cpio.gz"
init = "/provium/peinit"
append = "loglevel=7"
```

Relative paths are resolved against the directory containing `provium.toml`. Provium also searches parent directories for the config file, so tests in subdirectories inherit the nearest `provium.toml`.

See the [provium.toml reference](~provium/configuration/provium-toml) for all profile fields.

## tests/

All `.lua` files in this directory (and subdirectories) are discovered as tests. Provium walks the directory recursively, collecting every file ending in `.lua` — except files inside `fixtures/` subdirectories.

Files are sorted alphabetically for deterministic ordering in sequential mode. In parallel mode, the order depends on completion time.

### Helper libraries

Not every `.lua` file needs to be a test. Shared utilities can be loaded with Lua's `dofile()`:

```lua
local h = dofile("tests/helpers.lua")
local sid = h.build_sid(5, {18})
```

Helper files are still discovered by the test runner, but if they don't call any `provium.*` functions or `test()` blocks, they pass silently. By convention, helper files are named `helpers.lua` and return a table of functions.

## fixtures/

Fixture scripts live in `tests/fixtures/`. They are **not** run as tests — the runner skips the `fixtures/` directory during discovery.

A fixture script creates and configures a VM. Provium snapshots the VM's state after the script completes. Tests that call `provium.fixture("name")` resume from that snapshot instead of cold-booting.

```
tests/fixtures/
  minimal_vfs.lua          # Boots minimal profile, mounts VFS
  kacs.lua                 # Boots with KACS kernel module loaded
```

See [Fixtures](~provium/writing-tests/fixtures) for how to write and use fixture scripts.

## Test output

Provium writes console logs to `/tmp/provium-runs/run-*/`. Each test gets its own log file. Logs are deleted on success and retained on failure, so you can inspect QEMU console output when a test fails.

```
/tmp/provium-runs/
  run-abc123/
    boot.lua.log           # Retained (test failed)
```

The `--rerun-failed` flag uses these retained logs to identify which tests to re-run.
