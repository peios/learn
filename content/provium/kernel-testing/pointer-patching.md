---
title: Pointer Patching
type: concept
order: 40
description: Handle syscalls with nested structs that contain pointers to sub-buffers — Provium allocates guest memory and patches the addresses automatically.
related:
  - kernel-testing/raw-syscalls
  - kernel-testing/ioctl
  - kernel-testing/binary-packing
---

Some kernel interfaces pass structs that contain pointers to other buffers. For example, an access check syscall might take a struct with a pointer to a security descriptor, which itself contains pointers to SID buffers. You cannot embed a host-side pointer in a Lua string — the guest has its own address space.

Provium's pointer patching solves this. You provide the struct data with placeholder zeros where the pointers go, describe where the pointers are and what they should point to, and the guest agent allocates memory, patches the addresses, and executes the syscall.

## syscall_ptr

`vm:syscall_ptr(nr, bufs_table, ptrs_table, arg1, ...)` executes a syscall with buffer arguments and embedded pointer patching:

```lua
local ret, buf_out, ptr_out = vm:syscall_ptr(nr,
    bufs_table,    -- buffer arguments (same as syscall_bufs)
    ptrs_table,    -- pointer specs (new)
    arg1, arg2, ...
)
```

### Buffer arguments

The `bufs_table` works exactly like `vm:syscall_bufs()` — it maps argument indices to buffer data:

```lua
{[0] = struct_data, [2] = extra_data}
```

### Pointer specs

The `ptrs_table` is a list of tables, each describing one embedded pointer within a buffer argument:

```lua
{
    {buf_idx = 0, ptr_offset = 8, data_len = 128, output = true},
    {buf_idx = 0, ptr_offset = 16, data_len = 64, data = input_bytes},
}
```

| Field | Type | Description |
|---|---|---|
| `buf_idx` | number | Which buffer argument contains this pointer (matches a key in `bufs_table`) |
| `ptr_offset` | number | Byte offset of the pointer field within the buffer |
| `data_len` | number | Size of the sub-buffer to allocate in the guest |
| `output` | boolean | If `true`, the sub-buffer contents are returned after the syscall |
| `data` | string | Input data to populate the sub-buffer (for input pointers) |

The agent:

1. Allocates `data_len` bytes of guest memory for each spec
2. Copies `data` into the allocation (if provided)
3. Writes the allocation's guest address into the buffer at `ptr_offset`
4. Executes the syscall
5. Returns output sub-buffer contents (for specs with `output = true`)

### Return values

`syscall_ptr` returns:

| Return | Type | Description |
|---|---|---|
| `result` | number | Syscall return value |
| `buf1, buf2, ...` | strings | Output buffer contents (from `bufs_table`, in index order) |
| `ptr1, ptr2, ...` | strings | Output sub-buffer contents (from `ptrs_table`, in spec order, only for `output = true`) |

## When to use pointer patching

Use `syscall_ptr` when:

- A buffer argument contains a pointer field that the kernel dereferences
- You need to pass nested data structures (struct within struct)
- The kernel writes into a sub-buffer and you need to read the result

For most simple cases, `syscall_buf` or `syscall_bufs` is sufficient. Pointer patching is only needed when the kernel follows pointers embedded within your struct.

## Worked example

Consider a syscall that takes a struct containing a pointer to a security descriptor:

```c
struct access_check_args {
    uint32_t size;         // offset 0
    int32_t  token_fd;     // offset 4
    void    *sd_ptr;       // offset 8  ← embedded pointer
    uint32_t sd_len;       // offset 16
    uint32_t desired;      // offset 20
    // ... more fields
};
```

In Lua:

```lua
-- Build the struct with a placeholder zero at the pointer offset
local args = provium.pack("u32 i32 u64 u32 u32",
    96,       -- size
    token_fd, -- token_fd
    0,        -- sd_ptr (placeholder — will be patched)
    #sd,      -- sd_len
    desired)  -- desired access

-- Call with pointer patching
local ret, args_out, sd_out = vm:syscall_ptr(1023,
    {[0] = args},                                         -- buffer args
    {{buf_idx = 0, ptr_offset = 8, data_len = #sd, data = sd}},  -- pointer specs
    0)                                                    -- remaining int args

assert(ret >= 0, "access check failed: " .. ret)
```

The agent allocates guest memory for the security descriptor, copies `sd` into it, writes the guest address into `args` at byte offset 8, then calls `syscall(1023, args_ptr, 0)`.

## ioctl_buf as an alternative

For ioctls (rather than syscalls), `vm:ioctl_buf()` provides the same pointer-patching capability with a simpler interface. See [Ioctl](~provium/kernel-testing/ioctl) for details.

The key difference: `ioctl_buf` patches pointers within the ioctl struct itself, while `syscall_ptr` patches pointers within syscall buffer arguments.
