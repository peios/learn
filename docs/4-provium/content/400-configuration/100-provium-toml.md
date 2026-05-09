---
title: provium.toml Reference
type: reference
description: The provium.toml configuration file defines VM profiles — named combinations of kernel, filesystem, and init binary.
related:
  - provium/getting-started/project-structure
  - provium/writing-tests/vm-lifecycle
---

The `provium.toml` file defines **profiles** — named VM configurations that specify what kernel and filesystem to boot. Hardware settings (memory, CPUs) are not part of profiles; they are set per-test in the Lua script.

## Location

Provium searches for `provium.toml` starting in the current working directory and walking up through parent directories. This means tests in subdirectories inherit the nearest config file:

```
project/
  provium.toml         ← found when running from project/ or any subdirectory
  tests/
    boot.lua
    kernel/
      syscalls.lua     ← also uses project/provium.toml
```

## Format

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

Each `[profile.name]` section defines a profile. The `name` is used in Lua with `provium.create("name")`.

## Profile fields

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `kernel` | string | Yes | -- | Path to the Linux kernel image (`bzImage`). |
| `initrd` | string | No | -- | Path to an initramfs/cpio archive. At least one of `initrd` or `rootfs` should be set. |
| `rootfs` | string | No | -- | Path to a root filesystem disk image. Attached as a read-only virtio drive. |
| `init` | string | No | `"/sbin/init"` | Path to the init binary inside the guest. |
| `append` | string | No | `""` | Extra kernel command-line arguments. |

### Path resolution

Relative paths are resolved against the directory containing `provium.toml`:

```toml
# If provium.toml is at /home/user/project/provium.toml:
[profile.minimal]
kernel = "../kernel/out/bzImage"     # resolves to /home/user/kernel/out/bzImage
initrd = "testdata/rootfs.cpio.gz"   # resolves to /home/user/project/testdata/rootfs.cpio.gz
```

### Initrd vs rootfs

A profile can specify an initramfs (`initrd`), a disk image (`rootfs`), or both:

| Configuration | Boot behavior |
|---|---|
| `initrd` only | Kernel boots from the initramfs. The agent's shim is concatenated with it. |
| `rootfs` only | Kernel boots from the disk image (attached as a virtio drive). The agent's shim is provided as a separate initramfs. |
| Both | The initramfs is used for early boot, and the disk image is available as a block device. |

### The init path

The `init` field specifies what the guest should run as PID 1 — but Provium's agent wrapper intercepts this. The wrapper starts the agent first, then chains to the specified init binary. The kernel command line is set to:

```
rdinit=/provium-wrapper provium.init=/sbin/init
```

(or `init=` instead of `rdinit=` for disk-based boot)

### Kernel append

The `append` field adds extra arguments to the kernel command line. Common uses:

```toml
append = "loglevel=7"              # verbose kernel logging
append = "kacs.debug=1"            # module-specific option
append = "quiet"                   # suppress kernel messages
```
