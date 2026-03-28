---
title: Raw Syscalls
type: concept
order: 10
description: Call any Linux syscall from Lua — pass integer arguments, send buffers, and receive output data.
related:
  - kernel-testing/binary-packing
  - kernel-testing/pointer-patching
  - kernel-testing/ioctl
---

Provium's most powerful feature is raw syscall access. From Lua, you can call any syscall — standard Linux syscalls, custom kernel module syscalls, anything — passing integer arguments, buffer pointers, and receiving results.

## Simple syscalls

`vm:syscall(nr, arg1, arg2, ...)` executes a syscall with up to 6 integer arguments and returns the raw return value:

```lua
-- getpid (syscall 39)
local pid = vm:syscall(39)
assert(pid > 0)

-- Custom syscall: kacs_open_self_token(flags=0, access=TOKEN_QUERY)
local TOKEN_QUERY = 0x0008
local fd = vm:syscall(1000, 0, TOKEN_QUERY)
assert(fd >= 0, "open_self_token failed: " .. fd)
```

Arguments are passed as integers (Lua numbers). The return value is the raw `int64` result — for syscalls that return error codes, this will be a negative errno value on failure.

## Syscalls with one buffer

Many syscalls take a pointer to a buffer — a struct, a path, a data block. `vm:syscall_buf(nr, buf_arg_index, buf_data, arg1, ...)` replaces one argument with a pointer to buffer data:

```lua
-- syscall(nr, arg0, arg1, arg2, ...)
-- buf_arg_index=0 means arg0 gets the buffer pointer

local spec = provium.pack("u32 u32", 1, 42)
local fd = vm:syscall_buf(1003, 0, spec, 0, #spec)
assert(fd >= 0)
```

The `buf_arg_index` is the position (0-indexed) of the argument that should be replaced with a pointer. The agent allocates memory in the guest, copies the buffer data there, patches the pointer into the argument, and executes the syscall.

## Syscalls with multiple buffers

`vm:syscall_bufs(nr, bufs_table, arg1, ...)` handles syscalls that need multiple buffer arguments:

```lua
-- bufs_table maps argument indices to buffer data
local path_bytes = "/tmp/test\0"
local sd_data = build_sd()

local ret = vm:syscall_bufs(1022,
    {[1] = path_bytes, [3] = sd_data},   -- buffers
    -100, 0, 0x07, 0, #sd_data, 0)       -- remaining args
```

Each key in the `bufs_table` is an argument index (0-based). The corresponding argument is replaced with a pointer to the buffer data. Non-buffer arguments are passed as-is.

### Output buffers

`syscall_bufs` also returns output buffer contents — the buffer data after the syscall completes. This is essential for syscalls that write into caller-provided buffers:

```lua
-- Allocate an output buffer (filled with zeros)
local out_buf = string.rep("\0", 256)

local ret, path_out, data_out = vm:syscall_bufs(1021,
    {[1] = path_bytes, [3] = out_buf},
    -100, 0, 0x04, 0, 256, 0)

-- data_out contains what the kernel wrote into the buffer
if ret > 0 then
    local sd = data_out:sub(1, ret)
end
```

Output buffers are returned as additional return values in argument-index order. If you have buffers at indices 1 and 3, you get two extra return values: the buffer at index 1 first, then the buffer at index 3.

## Error handling

Syscall return values follow Linux conventions:

- **Success:** Non-negative value (often a file descriptor or 0)
- **Failure:** Negative errno value (`-1` = EPERM, `-13` = EACCES, `-22` = EINVAL, etc.)

```lua
local fd = vm:syscall(1000, 0, 0x0008)
if fd < 0 then
    error("syscall failed with errno: " .. (-fd))
end
```

For tests that verify error cases, assert the expected negative value:

```lua
test("rejects invalid flags", function()
    local ret = vm:syscall(1000, 0xFF, 0)
    assert_eq(ret, -22, "expected EINVAL")  -- -22 = EINVAL
end)
```

## Worked example

Testing a custom `kacs_open_self_token` syscall:

```lua
local vm = provium.create("minimal")
vm:boot()

-- Syscall 1000 = kacs_open_self_token(flags, access_mask)
local TOKEN_QUERY = 0x0008
local fd = vm:syscall(1000, 0, TOKEN_QUERY)
assert(fd >= 0, "kacs_open_self_token failed: " .. fd)

-- The fd should be a valid file descriptor (3+)
assert(fd >= 3, "unexpected fd: " .. fd)

vm:shutdown()
```

For more complex examples involving binary struct construction, see [Binary Packing](~provium/kernel-testing/binary-packing). For syscalls with nested pointer structures, see [Pointer Patching](~provium/kernel-testing/pointer-patching).
