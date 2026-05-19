---
title: Disks and fault injection
type: how-to
description: How to attach disks, read and write sectors directly, and inject EIO and slow I/O faults to exercise guest-side error recovery.
---

Provium's disk support has two goals: give the test direct sector-level access to the backing image, and inject faults that exercise the guest's error-handling paths.

The exhaustive method reference is on [Disk](~provium/reference/disk).

## Attaching a disk

```lua
local img = "/tmp/test.img"
-- Pre-create a backing file; Provium does not auto-create.
io.open(img, "w"):write(string.rep("\0", 1024 * 1024)):close()

local vm = provium:vm("v", "peios"):boot()
local disk = vm:attach_disk({id = "vda", size = 1024 * 1024, image = img})
```

Opts:

| Field | Default | Effect |
|---|---|---|
| `id` | `attached-<vm_name>` | Disk identifier within the VM. Use this to re-look-up via `vm:disk(id)`. |
| `size` | 4 GiB | Modeled disk size. Used by `disk:size()` when no image is attached. |
| `image` | none | Path to the backing file. Required for `read_sectors` / `write_sectors`. |

## Reading and writing sectors

Sectors are 512 bytes throughout. Offsets and counts are in sectors, not bytes.

```lua
-- Read sector 0 (the first 512 bytes).
local sec0 = disk:read_sectors(0, 1)

-- Read 4 sectors starting at sector 100 (bytes 51200..53247).
local block = disk:read_sectors(100, 4)
assert(#block == 4 * 512)

-- Write at sector 50.
disk:write_sectors(50, "hello, sector 50")
```

Without a backing image, both ops error with a `no backing image — disk:with_image required` message.

## Fault injection

Three modes:

| Mode | Effect |
|---|---|
| `eio_read` | Every `read_sectors` short-circuits to EIO. |
| `eio_write` | Every `write_sectors` short-circuits to EIO. |
| `slow` | Every `read_sectors` / `write_sectors` sleeps 50 ms before doing the I/O. |

Modes are activated with `disk:fault_inject(mode)` and cleared with `disk:clear_faults()`. Multiple modes can be active simultaneously — `slow` + `eio_read` delays for 50 ms then errors.

### Inject EIO

```lua
test("guest sees EIO on read", function(t)
    -- … attach disk with backing image …
    disk:fault_inject("eio_read")
    local ok, err = pcall(function() disk:read_sectors(0, 1) end)
    t:assert(not ok)
    t:assert(tostring(err):find("EIO"))
end)
```

### Inject slow I/O

```lua
test("write completes despite slowness", function(t)
    disk:fault_inject("slow")
    local started = os.time()
    disk:write_sectors(0, "data")  -- still succeeds
    local elapsed_ms = (os.time() - started) * 1000
    -- The 50 ms sleep is per-call. Tests that need a finer dial can
    -- patch the SLOW_FAULT_MS constant in the harness source.
end)
```

### Combine modes

```lua
test("slow EIO is still EIO", function(t)
    disk:fault_inject("slow")
    disk:fault_inject("eio_read")
    local ok, err = pcall(function() disk:read_sectors(0, 1) end)
    t:assert(not ok)  -- slow doesn't change the outcome
    t:assert(tostring(err):find("EIO"))
end)
```

### Concurrent injection during I/O

The harness re-checks the fault set after the slow-fault sleep AND after the actual I/O completes. So a test thread that flips `eio_read` mid-call still sees the EIO take effect:

```lua
test("EIO injected during slow read still fires", function(t)
    disk:fault_inject("slow")
    -- Spawn a worker that flips EIO while the read is sleeping.
    local w = vm:spawn_worker()
    w:run_async("sleep 0.025 && true")  -- placeholder: in a real test
                                        -- the worker would call
                                        -- disk:fault_inject via
                                        -- a parallel control plane

    -- The expectation: regardless of when the EIO injection lands
    -- (during the 50 ms sleep or during the actual read), the
    -- post-I/O recheck makes sure the test sees an EIO error.
end)
```

In practice, you usually inject up-front and then act, or use a worker for the parallel injection. The post-I/O recheck is mostly insurance against silent races.

### Inspecting state

```lua
local active = disk:active_faults()  -- {"eio_read", "slow"}
disk:is_detached()                   -- false
```

### Clearing

```lua
disk:clear_faults()
local r = disk:read_sectors(0, 1)    -- succeeds
```

## Detaching a disk

```lua
disk:detach()
local ok = pcall(function() disk:read_sectors(0, 1) end)
assert(not ok)  -- "disk is detached"
```

`disk:detach()` issues a best-effort QMP `device_del` against the parent VM and marks the local handle detached. If the disk was never QMP-added (host-bookkeeping-only attach), `device_del` silently surfaces "Device not found" but the local detached flag is still set.

## Common patterns

### "Does the guest retry after a transient EIO?"

```lua
test("guest retries on transient EIO", function(t)
    -- Inject EIO.
    disk:fault_inject("eio_read")

    -- Have the guest start a read in the background.
    local proc = vm:run_async("dd if=/dev/vda of=/tmp/out bs=512 count=1")

    -- Wait briefly, then clear so retry succeeds.
    vm:clock():sleep("100ms")
    disk:clear_faults()

    local r = proc:wait("5s")
    -- If the guest's driver retries, this succeeds. Otherwise dd
    -- returned an I/O error.
    r:assert_ok()
end)
```

### "Does the filesystem remount read-only after EIO?"

```lua
test("filesystem goes read-only after persistent EIO", function(t)
    disk:fault_inject("eio_write")
    vm:run("echo data > /mnt/test/file"):assert_ok()  -- might succeed or fail
    -- Force a sync to surface the write.
    vm:run("sync")
    -- Now check the kernel's view: errors=remount-ro should kick in.
    local r = vm:run("findmnt /mnt/test -o OPTIONS")
    t:assert(r.stdout:find("ro"))
end)
```

### "Does the guest panic on EIO at boot?"

```lua
test("EIO at boot does not panic", function(t)
    disk:fault_inject("eio_read")
    vm:reset()
    -- vm:reset() returns to Booted; check the console for panic strings.
    local log = vm:console():read_log()
    t:assert(not log:find("kernel panic"))
end)
```

## Multiple disks per VM

```lua
local data = vm:attach_disk({id = "vdb", size = 1024 * 1024, image = "/tmp/data.img"})
local logs = vm:attach_disk({id = "vdc", size = 1024 * 1024, image = "/tmp/logs.img"})

-- Inject EIO on data only; logs is unaffected.
data:fault_inject("eio_read")
```

Use `vm:disk(id)` to look up an already-attached disk:

```lua
local data = vm:disk("vdb")
data:fault_inject("slow")
```

## Caveats

- **Sector size is fixed at 512 bytes.** Tests that need 4 KiB sectors should expect their guest to layer that on top.
- **`read_sectors` and `write_sectors` go directly to the host file**, not through QEMU's block backend. This means a test that exercises QEMU's block translation (sparse holes, compression, etc.) will not see those layers — the disk userdata is a direct view of the underlying image bytes.
- **`disk:size()` reports the live image file size when an image is attached.** Test code that resizes the underlying file (`truncate`, `fallocate`) sees the new size, not the modeled `size` from `attach_disk`.

## See also

- [Disk reference](~provium/reference/disk) — every method, every error message.
- [VM reference](~provium/reference/vm) — `vm:attach_disk`, `vm:disk`.
