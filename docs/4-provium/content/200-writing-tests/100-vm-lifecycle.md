---
title: VM Lifecycle
type: concept
description: VMs are created from profiles, booted with hardware options, and shut down when the test is done. Provium cleans up any VMs left running.
related:
  - provium/writing-tests/fixtures
  - provium/configuration/provium-toml
  - provium/configuration/resource-management
---

Every Provium test creates one or more VMs, drives them through test scenarios, and shuts them down. The lifecycle is explicit — you control when each step happens.

## Creating a VM

`provium.create(profile)` creates a VM from a named profile in `provium.toml`. The VM is not started yet — it is just a handle waiting to be booted.

```lua
local vm = provium.create("minimal")
```

The profile name must match a `[profile.name]` section in `provium.toml`. If the profile does not exist, the script raises an error.

## Booting

`vm:boot()` starts QEMU and waits for the guest agent to be ready. An optional table controls hardware settings:

```lua
vm:boot({
    memory = "1G",
    cpus = 2,
})
```

| Option | Type | Default | Description |
|---|---|---|---|
| `memory` | string | `"512M"` | VM memory. Accepts QEMU suffixes: `"512M"`, `"1G"`, `"2G"`. |
| `cpus` | number | `1` | Number of virtual CPUs. |
| `files` | table | `nil` | Files to inject into the VM. Maps guest paths to host paths. |
| `disks` | table | `nil` | Additional block devices to attach. |

### Injecting files

The `files` option injects host files into the guest's initramfs before boot:

```lua
vm:boot({
    files = {
        ["/etc/config.toml"] = "/host/path/to/config.toml",
        ["/usr/bin/mytool"] = "/host/path/to/mytool",
    },
})
```

Injected files are available immediately at boot — no need to copy them after the VM starts.

### Attaching disks

The `disks` option attaches additional block devices. They appear as `/dev/vdX` in the guest:

```lua
vm:boot({
    disks = {
        {path = "/host/path/to/disk.img", format = "raw"},
        {path = "/host/path/to/data.qcow2", format = "qcow2", readonly = true},
    },
})
```

| Field | Type | Default | Description |
|---|---|---|---|
| `path` | string | required | Host path to the disk image. |
| `format` | string | `"raw"` | Image format: `"raw"` or `"qcow2"`. |
| `readonly` | boolean | `false` | Attach as read-only. |

## What happens during boot

When `vm:boot()` is called, Provium:

1. **Acquires resources** from the pool (if resource management is active)
2. **Builds a shim initramfs** containing the guest agent and any injected files
3. **Launches QEMU** with the configured kernel, initramfs, memory, CPUs, and vsock device
4. **Connects to the agent** over vsock, retrying until the agent sends a READY message

If KVM is available (`/dev/kvm` exists), hardware acceleration is enabled automatically. Without KVM, QEMU falls back to software emulation.

The boot call blocks until the agent is ready. If the agent does not respond within 30 seconds, the call raises an error.

## Shutting down

`vm:shutdown()` gracefully shuts down the VM:

```lua
vm:shutdown()
```

This sends a shutdown command to the agent, waits up to 10 seconds for QEMU to exit, then force-kills the process if it has not stopped. Resources are released back to the pool.

## Forceful kill

`vm:kill()` immediately terminates the QEMU process without a graceful shutdown:

```lua
vm:kill()
```

Use this when the VM is in a bad state and a graceful shutdown would hang.

## Shutdown all

`provium.shutdown_all()` shuts down every VM created in the current test:

```lua
provium.shutdown_all()
```

## Automatic cleanup

If a test script exits without shutting down its VMs — whether it completes normally or raises an error — Provium automatically kills all remaining VMs. You do not need to add cleanup code in error paths, but explicitly shutting down VMs is good practice for readability.

## Multiple VMs

A single test can create and run multiple VMs concurrently:

```lua
local vm1 = provium.fixture("minimal_vfs")
local vm2 = provium.fixture("minimal_vfs")

vm1:write_file("/tmp/id", "vm1")
vm2:write_file("/tmp/id", "vm2")

assert_eq(vm1:read_file("/tmp/id"), "vm1")
assert_eq(vm2:read_file("/tmp/id"), "vm2")

vm1:shutdown()
vm2:shutdown()
```

Each VM gets its own QEMU process, vsock connection, and guest agent. They are fully isolated from each other.
