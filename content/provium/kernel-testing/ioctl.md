---
title: Ioctl
type: concept
order: 20
description: Issue ioctls on guest file descriptors — pass structs, receive output, and handle ioctls with embedded buffer pointers.
related:
  - kernel-testing/raw-syscalls
  - kernel-testing/pointer-patching
---

Many kernel interfaces expose their functionality through ioctls on file descriptors rather than custom syscalls. Provium provides two ioctl functions: one for simple ioctls and one for ioctls whose struct contains embedded pointers to sub-buffers.

## Simple ioctl

`vm:ioctl(fd, cmd, data)` executes an ioctl on a guest file descriptor:

```lua
local args = provium.pack("u32 u32 u64", class, 0, 0)
local ret, out = vm:ioctl(fd, 0xC0104B00, args)
assert(ret == 0, "ioctl failed: " .. ret)
```

| Parameter | Type | Description |
|---|---|---|
| `fd` | number | File descriptor in the guest |
| `cmd` | number | Ioctl command number |
| `data` | string | Binary data to pass as the ioctl argument (optional) |

Returns two values:

| Return | Type | Description |
|---|---|---|
| `result` | number | Ioctl return value (0 on success, negative errno on failure) |
| `out` | string or nil | Output data (for `_IOR` and `_IOWR` ioctls) |

### Direction-aware behavior

The ioctl command number encodes the data direction in its upper bits:

| Direction | Meaning | Behavior |
|---|---|---|
| `_IOW` | Write (host → kernel) | Input data is passed to the kernel |
| `_IOR` | Read (kernel → host) | Output data is returned |
| `_IOWR` | Read/write | Input is passed, modified struct is returned |

For `_IOWR` ioctls, the returned `out` string contains the struct after the kernel modified it.

## Ioctl with embedded buffers

Some ioctls take a struct that contains pointers to sub-buffers. For example, a token query ioctl might take a struct with a `class` field and a pointer to an output buffer:

```c
struct token_query {
    uint32_t class;
    uint32_t buf_len;
    void    *buf;      // ← embedded pointer
};
```

You cannot pass a host pointer in a Lua string — the guest has its own address space. `vm:ioctl_buf()` solves this by allocating guest-side memory and patching the pointer into the struct.

`vm:ioctl_buf(fd, cmd, struct_data, specs)` executes an ioctl with embedded buffer pointer patching:

```lua
local args = provium.pack("u32 u32 u64", class, buf_size, 0)
local ret, struct_out, data = vm:ioctl_buf(fd, 0xC0104B00, args, {
    {ptr_offset = 8, buf_len = buf_size, output = true},
})
```

### Buffer specs

The `specs` parameter is a list of tables, each describing one embedded pointer in the struct:

| Field | Type | Description |
|---|---|---|
| `ptr_offset` | number | Byte offset of the pointer field within the struct |
| `buf_len` | number | Size of the buffer to allocate in the guest |
| `output` | boolean | If `true`, the buffer contents are returned after the ioctl |
| `data` | string | Input data to populate the buffer (for input buffers) |

### Return values

`ioctl_buf` returns multiple values:

| Return | Type | Description |
|---|---|---|
| `result` | number | Ioctl return value |
| `struct_out` | string or nil | The struct after the ioctl (for `_IOWR` commands) |
| `buf1, buf2, ...` | strings | Output buffer contents (only for specs with `output = true`) |

### Worked example: token query

A two-step query pattern — first query for size, then query for data:

```lua
-- Step 1: Size query (buf_len=0, no buffer needed)
local args = provium.pack("u32 u32 u64", class, 0, 0)
local ret, out = vm:ioctl(fd, KACS_IOC_QUERY, args)
assert(ret == 0)

-- Parse the returned buf_len to learn the needed buffer size
local _, needed = provium.unpack("u32 u32", out)

-- Step 2: Data query with allocated buffer
local args2 = provium.pack("u32 u32 u64", class, needed, 0)
local ret2, struct_out, data = vm:ioctl_buf(fd, KACS_IOC_QUERY, args2, {
    {ptr_offset = 8, buf_len = needed, output = true},
})
assert(ret2 == 0)
-- data contains the query result
```

### Multiple embedded buffers

A struct can have multiple pointer fields. List them all in the specs:

```lua
local ret, struct_out, sids_out, groups_out = vm:ioctl_buf(fd, cmd, struct_data, {
    {ptr_offset = 8, buf_len = 256, output = true},   -- first pointer
    {ptr_offset = 24, buf_len = 128, output = true},  -- second pointer
})
```

Output buffers are returned in the order they appear in the specs list.
