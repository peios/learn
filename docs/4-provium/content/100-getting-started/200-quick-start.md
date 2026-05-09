---
title: Quick Start
type: how-to
description: Write and run your first Provium test — boot a VM, run a command, and check the output.
---

This guide walks through creating a minimal Provium test, configuring a profile, and running it.

## Prerequisites

Provium requires:

- **QEMU** with KVM support (`qemu-system-x86_64`)
- **A Linux kernel image** (`bzImage`) to boot in the VM
- **An initramfs or root filesystem** for the VM's userspace
- **The `provium` binary** (built from the Provium repository)

Verify KVM is available:

```bash
ls /dev/kvm
```

If `/dev/kvm` exists, Provium will use hardware acceleration automatically. Without KVM, tests still work but boot significantly slower.

## Create a project

A Provium project needs a `provium.toml` configuration file and at least one `.lua` test file.

```bash
mkdir my-tests && cd my-tests
```

## Configure a profile

Create `provium.toml` with a profile that points to your kernel and initramfs:

```toml
[profile.minimal]
kernel = "/path/to/bzImage"
initrd = "/path/to/rootfs.cpio.gz"
init = "/sbin/init"
```

A profile defines **what** to boot — the kernel, root filesystem, and init binary. Hardware settings (memory, CPUs) are specified per-test in the Lua script.

## Write a test

Create `tests/hello.lua`:

```lua
local vm = provium.create("minimal")
vm:boot()

local r = vm:exec("uname -r")
assert(r.ok, "uname failed")

vm:shutdown()
```

This test:

1. Creates a VM from the `minimal` profile
2. Boots it with default settings (512 MB memory, 1 CPU)
3. Runs `uname -r` inside the guest
4. Asserts the command succeeded
5. Shuts down the VM

## Run the test

```bash
provium test tests/
```

Provium discovers all `.lua` files under the given path, runs them, and prints results:

```
provium test

  hello.lua ... ok (2.1s)

ok: 1 passed
```

## Run a single test

Use the `-f` flag to filter by filename:

```bash
provium test -f hello tests/
```

## Add assertions

Expand the test to check the output:

```lua
local vm = provium.create("minimal")
vm:boot()

local r = vm:exec("uname -r")
assert(r.ok, "uname failed")
assert_contains(r.stdout.value, "6.", "expected kernel 6.x")

local r2 = vm:exec("cat /proc/cpuinfo")
assert(r2.ok, "cpuinfo failed")

vm:shutdown()
```

## Use sub-tests

Organize related assertions into named `test()` blocks:

```lua
local vm = provium.create("minimal")
vm:boot()
vm:mount_vfs()

test("kernel version", function()
    local r = vm:exec("uname -r")
    assert(r.ok)
    assert_contains(r.stdout.value, "6.")
end)

test("proc mounted", function()
    local r = vm:exec("cat /proc/version")
    assert(r.ok, "proc not mounted")
end)

vm:shutdown()
```

Sub-tests run sequentially within the file. Each failure is reported independently:

```
  hello.lua ... ok (2 tests, 2.1s)
    · kernel version ... ok
    · proc mounted ... ok
```

## Next steps

- Learn about the [VM lifecycle](~provium/writing-tests/vm-lifecycle) — boot options, memory, CPUs, disks
- Read about [fixtures](~provium/writing-tests/fixtures) to avoid cold-booting in every test
- See the [project structure](~provium/getting-started/project-structure) for how to organize a test suite
