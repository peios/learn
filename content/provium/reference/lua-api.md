---
title: Lua API Reference
type: reference
order: 10
description: Complete reference for every function available in Provium test scripts — VM management, commands, syscalls, ioctls, assertions, and utilities.
---

## Module functions

Functions on the global `provium` table.

### provium.create(profile)

Creates a VM from a named profile. Does not boot it.

```lua
local vm = provium.create("minimal")
```

**Parameters:** `profile` (string) — profile name from `provium.toml`.
**Returns:** VM userdata.

### provium.fixture(name)

Resumes a VM from a cached fixture snapshot. Builds the fixture lazily on first call.

```lua
local vm = provium.fixture("kacs")
```

**Parameters:** `name` (string) — fixture name (matches `fixtures/name.lua`).
**Returns:** VM userdata (booted and ready).

### provium.shutdown_all()

Gracefully shuts down all VMs created in the current test.

```lua
provium.shutdown_all()
```

### provium.pack(fmt, ...)

Packs values into a binary string. Little-endian byte order.

```lua
local data = provium.pack("u32 u32 u64", 1, 42, 0)
```

**Format types:** `u8`, `u16`, `i16`, `u32`, `i32`, `u64`, `i64`
**Returns:** Binary string.

### provium.unpack(fmt, data)

Unpacks values from a binary string.

```lua
local a, b = provium.unpack("u32 u32", data)
```

**Returns:** One value per format specifier.

---

## VM methods

Methods on VM userdata returned by `provium.create()` or `provium.fixture()`. Workers returned by `vm:spawn()` support the same methods except `boot`, `shutdown`, and `spawn`.

### vm:boot(opts?)

Starts the VM. Blocks until the agent is ready.

```lua
vm:boot({memory = "1G", cpus = 2})
```

| Option | Type | Default | Description |
|---|---|---|---|
| `memory` | string | `"512M"` | VM memory (`"512M"`, `"1G"`, `"2G"`) |
| `cpus` | number | `1` | Virtual CPUs |
| `files` | table | `nil` | Guest path → host path mapping for file injection |
| `disks` | table | `nil` | Additional block devices: `{path, format, readonly}` |

### vm:exec(cmd)

Runs a shell command. Returns a result table.

```lua
local r = vm:exec("uname -r")
```

**Returns:** `{ok, exit_code, stdout, stderr}` — `stdout` and `stderr` are string wrappers with `.value`, `.contains(s)`, `.starts_with(s)`, `.trim()`.

### vm:json(cmd)

Runs a command and parses stdout as JSON. Raises an error if the command fails or JSON is invalid.

```lua
local data = vm:json("cat /etc/config.json")
```

**Returns:** Lua table (nested tables and arrays).

### vm:write_file(path, data)

Writes a string to a file in the guest.

```lua
vm:write_file("/tmp/test.txt", "hello")
```

### vm:read_file(path)

Reads a file from the guest.

```lua
local data = vm:read_file("/etc/hostname")
```

**Returns:** File contents as a string.

### vm:dmesg(pattern?)

Returns kernel log output. With a pattern, filters through grep.

```lua
local log = vm:dmesg("kacs:")
```

**Returns:** String.

### vm:mount_vfs()

Mounts proc, sysfs, securityfs, and devtmpfs. Idempotent.

```lua
vm:mount_vfs()
```

### vm:wait_until(fn, opts?)

Polls a callback until it returns true or timeout expires.

```lua
vm:wait_until(function()
    return vm:exec("test -f /tmp/ready").ok
end, {timeout = 5, interval = 0.5, desc = "ready"})
```

| Option | Type | Default | Description |
|---|---|---|---|
| `timeout` | number | `10` | Seconds before raising an error |
| `interval` | number | `0.5` | Seconds between polls |
| `desc` | string | `"condition"` | Description for timeout error |

### vm:shutdown()

Gracefully shuts down the VM. Waits up to 10 seconds, then force-kills.

### vm:kill()

Forcefully terminates the QEMU process.

---

## Syscalls

### vm:syscall(nr, arg1, ..., arg6)

Executes a raw syscall with up to 6 integer arguments.

```lua
local fd = vm:syscall(1000, 0, 0x0008)
```

**Returns:** Syscall return value (int64).

### vm:syscall_buf(nr, buf_arg_index, buf_data, arg1, ...)

Syscall with one buffer argument. The argument at `buf_arg_index` is replaced with a pointer to `buf_data` in guest memory.

```lua
local ret = vm:syscall_buf(1003, 0, spec_data, 0, #spec_data)
```

**Returns:** Syscall return value.

### vm:syscall_bufs(nr, bufs_table, arg1, ...)

Syscall with multiple buffer arguments. `bufs_table` maps argument indices to buffer data.

```lua
local ret, buf1_out, buf2_out = vm:syscall_bufs(1022,
    {[1] = path, [3] = sd_data},
    -100, 0, 0x07, 0, #sd_data, 0)
```

**Returns:** Syscall return value, then output buffers in argument-index order.

### vm:syscall_ptr(nr, bufs_table, ptrs_table, arg1, ...)

Syscall with buffer arguments and embedded pointer patching.

```lua
local ret, buf_out, ptr_out = vm:syscall_ptr(1023,
    {[0] = args_data},
    {{buf_idx = 0, ptr_offset = 8, data_len = #sd, data = sd}},
    0)
```

**Pointer spec fields:** `buf_idx`, `ptr_offset`, `data_len`, `output` (boolean), `data` (string).
**Returns:** Syscall return value, buffer outputs, pointer outputs.

---

## Ioctls

### vm:ioctl(fd, cmd, data?)

Executes an ioctl on a guest file descriptor.

```lua
local ret, out = vm:ioctl(fd, 0xC0104B00, args)
```

**Returns:** Result value, output data (or nil).

### vm:ioctl_buf(fd, cmd, struct_data, specs)

Ioctl with embedded buffer pointer patching.

```lua
local ret, struct_out, data = vm:ioctl_buf(fd, cmd, args, {
    {ptr_offset = 8, buf_len = 256, output = true},
})
```

**Spec fields:** `ptr_offset`, `buf_len`, `output` (boolean), `data` (string).
**Returns:** Result value, struct output, then output buffers.

---

## Background jobs

### vm:background(cmd)

Starts a command in the background.

```lua
local job = vm:background("sleep 10")
```

**Returns:** `{id, pid}` table.

### vm:job_wait(job, timeout?)

Waits for a background job. Timeout is in seconds (0 = poll).

```lua
local r = vm:job_wait(job, 5)
```

**Returns:** `{exit_code, stdout, stderr, running}`.

### vm:job_kill(job)

Kills a background job and returns its result.

```lua
local r = vm:job_kill(job)
```

---

## Workers

### vm:spawn(opts?)

Forks the guest agent. Returns a worker with the same methods as a VM.

```lua
local worker = vm:spawn()
local thread_worker = vm:spawn({thread = true})
```

| Option | Type | Default | Description |
|---|---|---|---|
| `thread` | boolean | `false` | Use `clone(CLONE_THREAD)` instead of fork |

**Returns:** Worker userdata.

### worker:kill()

Closes the worker connection. The worker process exits.

---

## Assertions

### assert(condition, message?)

Enhanced assert. Raises an error if condition is falsy.

### assert_eq(expected, actual, message?)

Equality check. Shows both values on failure.

### assert_contains(haystack, needle, message?)

Substring check. Shows the haystack and needle on failure.

---

## Sub-tests

### test(name, fn)

Runs a named sub-test with isolated failure handling.

```lua
test("my test", function()
    assert(true)
end)
```

### todo(reason?)

Marks the current test as not yet implemented (skip, not fail).

```lua
test("future work", function()
    todo("waiting on feature X")
end)
```
