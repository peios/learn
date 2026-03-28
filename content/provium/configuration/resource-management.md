---
title: Resource Management
type: concept
order: 30
description: Provium gates VM launches against available memory and CPU to prevent overcommit. Two modes — auto-detection and fixed budgets.
related:
  - configuration/cli-reference
  - writing-tests/vm-lifecycle
---

Each VM consumes real system memory and CPU. If Provium launches too many VMs simultaneously, the host can run out of memory or become CPU-saturated. The resource pool prevents this by gating VM boot on available resources.

## Auto mode (default)

Without explicit `--mem` or `--cpus` flags, Provium uses auto-detection:

- **Memory:** Before each VM boot, Provium reads `/proc/meminfo` MemAvailable. If there is not enough free memory (accounting for the VM's configured size plus a 1.5 GB host reserve), the boot waits until other VMs shut down and release their memory.
- **CPU:** Provium limits parallelism to half the host CPU count (minimum 2) to avoid saturating KVM and vhost-vsock resources.

Auto mode adapts to the host's actual load. If other processes are consuming memory, fewer VMs run concurrently.

## Fixed mode

With `--mem` and/or `--cpus`, Provium uses a fixed resource budget:

```bash
provium test --mem 4G --cpus 8 tests/
```

VMs acquire resources from the declared pool:

- A VM configured with `memory = "512M"` and `cpus = 1` takes 512 MB and 1 CPU from the pool
- If the pool does not have enough resources, the VM boot blocks until another VM shuts down
- When a VM shuts down, its resources are returned to the pool

Fixed mode is predictable — the same resource budget always produces the same scheduling behavior. It is useful on CI systems or shared machines where you want to cap Provium's resource usage.

```
provium test --mem 4G --cpus 8 tests/

resource pool: 4096M memory, 8 CPUs

  kacs_boot.lua ... ok (2.1s)
  kacs_token.lua ... ok (86 tests, 4.3s)
  ...
```

## How resources are calculated

Each VM's resource usage comes from the boot options in the Lua script:

```lua
vm:boot({memory = "1G", cpus = 2})
-- Uses 1 GB from the memory pool, 2 from the CPU pool
```

```lua
vm:boot()
-- Uses 512 MB (default) from memory, 1 (default) from CPUs
```

Resources are acquired at boot time and released when the VM is shut down or killed.

## Parallelism interaction

The `-p` flag controls how many test files run concurrently. The resource pool controls how many VMs run concurrently within those tests.

- **Auto mode:** The `-p` flag and memory pool both gate concurrency. A test file may be running but its VM boot may be waiting for memory.
- **Fixed mode:** When `--mem` or `--cpus` is set, `-p` defaults to the total number of test files (unlimited concurrency) since the pool handles all gating.
- **Explicit `-p`:** Always respected. Combines with the pool — the semaphore limits test concurrency, and the pool limits VM concurrency within those tests.
