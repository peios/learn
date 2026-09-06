---
title: Disks and fault injection
type: how-to
description: How to attach disks, read and write sectors directly, and inject EIO and slow I/O faults to exercise guest-side error recovery.
related:
  - provium/reference/disk
  - provium/reference/vm
  - provium/writing-tests/vms-and-profiles
---

Provium's disk support has three goals: put a block device in front of the guest, give the test direct sector-level access to the backing image, and inject faults that exercise the guest's error-handling paths.

The exhaustive method reference is on [Disk](~provium/reference/disk).

## Attaching a disk

A disk the guest can see is declared **before the boot**, because the guest's firmware and initramfs look for block devices long before there is an agent to call anything.

For one test — a blank disk to install onto, a filesystem you have damaged on purpose:

```lua
local img = "/tmp/test.img"
-- Pre-create a backing file; Provium does not auto-create.
io.open(img, "w"):write(string.rep("\0", 1024 * 1024)):close()

local vm = provium:vm("v", "peios"):boot({
    disks = {{path = img, id = "target"}},
})
local disk = vm:disk("target")
```

For every test in a suite — a boot medium, an image that *is* the system under test — put it in the profile instead, beside `kernel` and `initrd`:

```toml
[profiles.peios]
disks = [{ path = "{out}/peios.iso", id = "medium", readonly = true }]
```

Either way the guest gets a `virtio-blk-pci` device, named `/dev/vda`, `/dev/vdb`, … in attachment order, with the profile's disks first. Both forms are documented in full under [`disks`](~provium/configuration/provium-toml#disks) and [Boot disks](~provium/reference/vm#boot-disks).

> [!IMPORTANT]
> `vm:attach_disk` is **not** this. It records a host-side attachment — a name, a size, and a backing file — so that sector access and fault injection have something to address. It emits no QEMU device, so the guest sees nothing new. Reach for it when the guest already gets at the image some other way; reach for the boot forms above when the guest is meant to find a device.

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

Modes are activated with `disk:fault_inject(mode)` and cleared with `disk:clear_faults()`. Multiple modes can be active simultaneously — with `slow` + `eio_read` both set, the EIO check wins: the read errors immediately, without the 50 ms delay.

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

`slow` delays each sector op but doesn't change its outcome. Assert both halves: the op took the hit, and it still worked. The guest [Clock](~provium/reference/clock) gives you a sub-millisecond time source (`os.time()` only has 1-second resolution):

```lua
test("write completes despite slowness", function(t)
    disk:fault_inject("slow")

    local clock = vm:clock()
    local before = clock:get_ns()
    disk:write_sectors(0, "data")            -- sleeps ~50 ms, then writes
    local elapsed_ms = (clock:get_ns() - before) / 1e6

    t:assert(elapsed_ms >= 50, "slow fault should add at least 50 ms")
    t:assert_eq(disk:read_sectors(0, 1):sub(1, 4), "data")  -- the write still landed
end)
```

The 50 ms delay is fixed per call; it is not currently configurable from test code.

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

The harness re-checks the fault set after the slow-fault sleep AND after the actual I/O completes, so an EIO fault that lands mid-call still takes effect. There is currently no way to exercise this from a test, though: test code runs on a single thread, and workers run guest processes — they can't call `disk:fault_inject`. Inject faults up-front, act, then clear; the mid-call recheck is defensive insurance in the harness, not a pattern you can drive.

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

`disk:detach()` issues a best-effort QMP `device_del` against the parent VM and marks the local handle detached; after that, sector ops error. The exact behaviour for disks that were never QMP-added is in the [Disk reference](~provium/reference/disk#diskdetach).

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
local vm = provium:vm("v", "peios"):boot({
    disks = {
        {path = "/tmp/data.img", id = "data"},
        {path = "/tmp/logs.img", id = "logs"},
    },
})

-- Inject EIO on data only; logs is unaffected.
vm:disk("data"):fault_inject("eio_read")
```

Attachment order is device order in the guest, so `data` is `/dev/vda` and `logs` is `/dev/vdb` — or `/dev/vdb` and `/dev/vdc` if the profile already attached one of its own.

Use `vm:disk(id)` to look a disk up again anywhere later in the test:

```lua
vm:disk("data"):fault_inject("slow")
```

## Caveats

- **Sector size is fixed at 512 bytes.** Tests that need 4 KiB sectors should expect their guest to layer that on top.
- **`read_sectors` and `write_sectors` go directly to the host file**, not through QEMU's block backend. This means a test that exercises QEMU's block translation (sparse holes, compression, etc.) will not see those layers — the disk userdata is a direct view of the underlying image bytes.
- **`disk:size()` reports the live image file size when an image is attached.** Test code that resizes the underlying file (`truncate`, `fallocate`) sees the new size, not the modelled `size` from `attach_disk`.

## See also

- [Disk reference](~provium/reference/disk) — every method, every error message.
- [VM reference](~provium/reference/vm) — `vm:attach_disk`, `vm:disk`.
