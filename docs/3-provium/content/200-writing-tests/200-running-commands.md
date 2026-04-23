---
title: Running Commands
type: concept
description: Execute shell commands in the guest, parse JSON output, read and write files, inspect kernel logs, and mount virtual filesystems.
related:
  - provium/writing-tests/assertions-and-subtests
  - provium/writing-tests/background-jobs
---

Once a VM is booted, you interact with it through the guest agent. The agent runs shell commands, transfers files, and provides access to the kernel — all over a vsock connection with no IP networking required.

## Executing commands

`vm:exec(cmd)` runs a shell command in the guest and returns the result:

```lua
local r = vm:exec("ls -la /tmp")
```

The result is a table with these fields:

| Field | Type | Description |
|---|---|---|
| `ok` | boolean | `true` if the command exited with code 0 |
| `exit_code` | number | The command's exit code |
| `stdout` | string wrapper | Standard output |
| `stderr` | string wrapper | Standard error |

### String wrappers

The `stdout` and `stderr` fields are string wrapper tables with helper methods and a `.value` field for the raw string:

```lua
-- Raw string access
local output = r.stdout.value

-- Helper methods
r.stdout.contains("pattern")      -- returns true/false
r.stdout.starts_with("prefix")    -- returns true/false
r.stdout.trim()                   -- returns trimmed string
```

Use `.value` when you need the raw string for comparisons or passing to other functions. Use the helper methods for quick inline checks.

### Common patterns

```lua
-- Check a command succeeded
local r = vm:exec("whoami")
assert(r.ok, "whoami failed: " .. r.stderr.value)

-- Check output contains a substring
local r = vm:exec("cat /proc/version")
assert_contains(r.stdout.value, "Linux", "not Linux")

-- Use exit code for control flow
local r = vm:exec("test -f /tmp/marker")
if r.ok then
    -- file exists
end
```

## Parsing JSON output

`vm:json(cmd)` runs a command, parses its stdout as JSON, and returns a Lua table:

```lua
local info = vm:json("cat /proc/meminfo.json")
assert(info.total > 0, "no memory reported")
```

If the command exits with a non-zero code or the output is not valid JSON, the call raises an error.

## Reading and writing files

`vm:write_file(path, data)` writes a string to a file in the guest:

```lua
vm:write_file("/tmp/config.toml", '[server]\nport = 8080')
```

`vm:read_file(path)` reads a file from the guest and returns its contents as a string:

```lua
local data = vm:read_file("/etc/hostname")
assert_eq(data, "testvm\n")
```

These operations transfer data over the vsock connection. They work with any file the agent process can access — there is no size limit beyond the 16 MiB protocol maximum.

## Inspecting kernel logs

`vm:dmesg()` returns the full kernel log:

```lua
local log = vm:dmesg()
assert_contains(log, "Linux version")
```

With a pattern argument, it filters lines through `grep`:

```lua
local kacs_log = vm:dmesg("kacs:")
assert_contains(kacs_log, "initialized")
```

This is useful for verifying that kernel modules loaded correctly, checking for warnings or errors, and confirming kernel-level events during tests.

## Mounting virtual filesystems

`vm:mount_vfs()` mounts the standard virtual filesystems that most tests need:

```lua
vm:mount_vfs()
```

This mounts:

| Filesystem | Mount point |
|---|---|
| `proc` | `/proc` |
| `sysfs` | `/sys` |
| `securityfs` | `/sys/kernel/security` |
| `devtmpfs` | `/dev` |

The call is idempotent — if a filesystem is already mounted, the mount failure is silently ignored. Most tests call `vm:mount_vfs()` immediately after boot. If you are using a [fixture](~provium/writing-tests/fixtures), the fixture script typically handles this.
