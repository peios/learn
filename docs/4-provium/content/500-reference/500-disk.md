---
title: Disk
type: reference
description: A Disk userdata represents one virtio-blk disk attached to a VM. Use it to read and write sectors directly, inject I/O faults (EIO read, EIO write, slow I/O), or detach the disk from the live guest.
---

A Disk wraps one virtio-blk disk attached to a VM. It exposes block-level operations and a fault-injection surface useful for exercising I/O error paths in the guest.

## Constructing

| Source | Returns |
|---|---|
| `vm:attach_disk({id="vda", size=…, image="…"})` | New disk attached to `vm`. |
| `vm:disk("id")` | Lookup of an already-attached disk. Errors if absent. |

`vm:attach_disk` opts:

| Field | Type | Default | Description |
|---|---|---|---|
| `id` | string | `"attached-<vm_name>"` | Disk identifier within the VM. |
| `size` | int (bytes) | `4 GiB` | Modeled disk size. Used for `:size()` when no image is attached. |
| `image` | string (path) | none | Backing file. Sector ops require an image. |

Disks are 512-byte sectors throughout. The `read_sectors` and `write_sectors` ops express offsets and counts in sectors.

## Methods

### `disk:size()`

Returns the disk's size in bytes. When a backing image is attached, returns the live `stat()` size of the image file (so a test that resized the underlying file with `truncate` / `fallocate` reads honest output). Without an image, returns the modeled size from `attach_disk`.

### `disk:read_sectors(offset, n)`

Read `n` sectors starting at sector `offset`. Returns the bytes as a Lua string. Errors if:

- The disk is detached (`disk:read_sectors: disk is detached`).
- No backing image (`disk:read_sectors: no backing image — disk:with_image required`).
- An `eio_read` fault is active (`disk:read_sectors: EIO (fault_inject)`).
- The host-side `read` fails (passes the underlying error through).

Honours active faults:

- `eio_read` — short-circuits to EIO before any I/O.
- `slow` — sleeps 50 ms per call. After the sleep, re-checks for `eio_read` so a concurrent fault injection during the sleep still takes effect. After the actual I/O, checks one more time for the same reason.

### `disk:write_sectors(offset, data)`

Write `data` (a Lua string) starting at sector `offset`. The data does not have to be a multiple of 512 bytes; it is written verbatim from the offset. Returns nothing.

Errors and fault handling mirror `read_sectors`:

- Detached → error.
- No backing image → error.
- `eio_write` active before the I/O → EIO.
- `slow` → 50 ms sleep, with `eio_write` re-checks after the sleep and after the I/O.

### `disk:fault_inject(mode)`

Activate a fault. Valid modes: `"eio_read"`, `"eio_write"`, `"slow"`. Unknown modes error with the valid list (`disk:fault_inject: unknown mode \`X\` (valid: eio_read, eio_write, slow)`).

Multiple modes can be active simultaneously. `slow` and `eio_*` compose naturally — a `slow` + `eio_read` combination delays the I/O before erroring.

### `disk:clear_faults()`

Clear every active fault. Subsequent reads / writes succeed normally.

### `disk:active_faults()`

Returns a Lua array of the currently-active fault mode names. Useful for tests that need to assert the harness state.

### `disk:detach()`

Mark the disk as detached and issue a best-effort QMP `device_del` against the parent VM. Subsequent `read_sectors` / `write_sectors` error. The QMP call is best-effort: a disk that was never QMP-added (host-bookkeeping-only attach) silently surfaces "Device not found" but the local detached flag is still set.

### `disk:is_detached()` / `disk:id()`

Accessors. `:id()` returns the disk identifier as given to `attach_disk`.

## Example: full fault-injection pattern

```lua
test("guest sees EIO and recovers after clear", function(t)
    local img = "/tmp/test-image"
    -- Pre-create the backing file.
    local f = io.open(img, "w"); f:write(string.rep("\0", 512 * 1024)); f:close()

    local vm = provium:vm("v", "peios"):boot()
    local disk = vm:attach_disk({id = "vda", size = 512 * 1024, image = img})

    -- Confirm baseline read works.
    local body = disk:read_sectors(0, 1)
    t:assert_eq(#body, 512)

    -- Inject EIO.
    disk:fault_inject("eio_read")
    local ok, err = pcall(function() disk:read_sectors(0, 1) end)
    t:assert(not ok)
    t:assert(tostring(err):find("EIO"))

    -- Clear and confirm reads recover.
    disk:clear_faults()
    body = disk:read_sectors(0, 1)
    t:assert_eq(#body, 512)
end)
```

## See also

- [VM](~provium/reference/vm) — disks come from `vm:attach_disk` / `vm:disk`.
- [Disks and fault injection](~provium/writing-tests/disks-and-fault-injection) — patterns for exercising I/O error paths.
