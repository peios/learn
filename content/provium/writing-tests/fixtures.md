---
title: Fixtures
type: concept
order: 40
description: Fixtures snapshot a booted VM's state so that tests can resume from it instantly instead of cold-booting every time.
related:
  - writing-tests/vm-lifecycle
  - architecture/snapshots
---

Cold-booting a VM takes seconds. When you have dozens or hundreds of tests that all need the same base state — a booted kernel with virtual filesystems mounted — those seconds add up.

Fixtures solve this. A fixture is a cached snapshot of a booted VM. The first test that requests a fixture triggers a cold boot, runs a setup script, and saves the VM's memory state to disk. Every subsequent test resumes from that snapshot in a fraction of the time.

## Using a fixture

`provium.fixture(name)` returns a VM resumed from a cached snapshot:

```lua
local vm = provium.fixture("minimal_vfs")

-- securityfs is already mounted — the fixture set it up
local r = vm:exec("ls /sys/kernel/security/")
assert(r.ok)

vm:shutdown()
```

The returned VM has the same API as one created with `provium.create()` — you call `vm:exec()`, `vm:syscall()`, `vm:shutdown()`, and everything else as normal.

## Writing a fixture

Fixture scripts live in the `tests/fixtures/` directory. The filename (minus `.lua`) becomes the fixture name. A file named `minimal_vfs.lua` creates a fixture called `"minimal_vfs"`.

A fixture script creates a VM, boots it, configures it, and then exits. Provium snapshots the last created VM after the script completes.

```lua
-- fixtures/minimal_vfs.lua
local vm = provium.create("minimal")
vm:boot()
vm:mount_vfs()
```

That is the entire fixture. The `vm:shutdown()` call is deliberately absent — Provium needs the VM running to save its state.

### A more complex fixture

Fixtures can do any setup that tests need:

```lua
-- fixtures/kacs_sd.lua
local h = dofile("tests/helpers.lua")

local vm = provium.create("minimal")
vm:boot()
vm:mount_vfs()

-- Stamp permissive SDs on all rootfs files so non-SYSTEM
-- tokens can access them
local sd = h.build_sd(h.SID_SYSTEM, h.SID_SYSTEM,
    h.build_acl({h.build_allow_ace(h.FILE_ALL_ACCESS, h.SID_EVERYONE)}))

local paths = {"/", "/bin", "/sbin", "/dev", "/etc", "/tmp"}
for _, path in ipairs(paths) do
    h.set_sd(vm, path, sd,
        h.OWNER_SECURITY_INFORMATION +
        h.GROUP_SECURITY_INFORMATION +
        h.DACL_SECURITY_INFORMATION)
end
```

## How fixtures work

### Lazy building

Fixtures are built on demand. The first call to `provium.fixture("name")` triggers the build:

1. Provium looks for `tests/fixtures/name.lua`
2. It runs the script, which creates and configures a VM
3. After the script completes, Provium disconnects from the guest agent
4. It saves the VM's full memory state to a snapshot file via QEMU's migration mechanism
5. The snapshot is cached for the duration of the test run

### Thread safety

Fixture building is thread-safe. If multiple tests request the same fixture concurrently (during parallel execution), only one build runs. The others block until the build completes and then resume from the same snapshot.

### Resume from snapshot

When a test calls `provium.fixture("name")` after the fixture is built:

1. Provium starts a new QEMU process, loading the saved state
2. QEMU resumes the VM from the snapshot — the guest kernel and agent are already running
3. Provium connects to the agent over vsock
4. The VM is ready for the test

### Fixture nesting

Fixtures can use other fixtures. If your `kacs_sd` fixture needs the same base state as `kacs`, the `kacs_sd` fixture script can call `provium.fixture("kacs")` instead of booting from scratch:

```lua
-- fixtures/kacs_sd.lua
local h = dofile("tests/helpers.lua")
local vm = provium.fixture("kacs")

-- Additional setup on top of the kacs fixture...
```

### Cleanup

Snapshot files are stored in a temporary directory under `/tmp/provium-runs/` and cleaned up when the test run finishes. They are not persisted between runs — each `provium test` invocation rebuilds fixtures from scratch.

## When to use fixtures

Use fixtures when:

- Multiple tests need the same base VM state
- The setup takes more than a trivial amount of time (mounting filesystems, stamping security descriptors, loading kernel state)
- You want consistent starting conditions across tests

Do not use fixtures when:

- The test needs a completely fresh VM (testing boot behavior itself)
- Setup is trivial (a single `vm:exec()` call)
- Each test needs different boot options (different memory, different disks)
