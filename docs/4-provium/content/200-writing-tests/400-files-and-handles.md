---
title: Files and handles
type: how-to
description: Patterns for guest-side file I/O — read_file/write_file vs open_file, mode tables, seek/tell, tail streams, stat, listdir, mkdir, unlink, rename, and ioctl over open handles.
---

Provium gives you two layers for guest-side file I/O. Most tests use the high-level `vm:read_file` / `vm:write_file` / `vm:stat` calls; tests that need cursor control, partial reads, or POSIX semantics drop to `vm:open_file` and the [File](~provium/reference/file-handle) userdata.

## High-level: `read_file` / `write_file` / `stat`

These are one-shot operations. Each is a single round-trip to the agent.

```lua
vm:write_file("/etc/test.conf", "key=value\n")
local body = vm:read_file("/etc/test.conf")
local meta = vm:stat("/etc/test.conf")
```

### `vm:read_file(path)`

Returns the entire file as a Lua string. Errors on agent-side `read` failure (ENOENT, EACCES, etc.).

```lua
local content = vm:read_file("/etc/hostname")
```

### `vm:write_file(path, data)`

Replaces the file's contents. Creates if absent. The mode bits follow agent defaults — use `vm:open_file` if you need explicit `perm`.

```lua
vm:write_file("/tmp/data", "binary\0bytes")
```

### `vm:push_file(host_path, guest_path, opts?)`

Read a file on the host and write its bytes to `guest_path` in the guest. Equivalent to reading the host file in Lua and passing the bytes to `vm:write_file`, but with one important extra: inside a fixture, the host file is folded into the fixture's cache key automatically, so rebuilding the host artifact (e.g. a binary you're testing) invalidates the snapshot.

```lua
vm:push_file("../peios-uapi/target/release/peios-uapi", "/usr/bin/peios-uapi")
```

Relative `host_path` is resolved against the fixture (or helper) file's directory, not the cwd at invocation time. Pass `{auto_dep = false}` to skip the auto-fold for a single call (e.g. a large test corpus you don't want included in the key):

```lua
vm:push_file("../big-corpus.tar", "/data.tar", {auto_dep = false})
```

The auto-fold relies on static scanning of the call site, so non-literal host paths (variables, concatenation) are NOT tracked. Use [`lab:depends_on_file`](~provium/reference/lab#labdepends_on_file) with a literal string to declare them explicitly. See [Fixtures and dependencies — External host-file deps](~provium/running-tests/fixtures-and-dependencies#external-host-file-deps) for the full model.

Mode bits follow `write_file`'s agent defaults — `vm:run("chmod +x …")` after the push if you need executable bits.

### `vm:stat(path)`

Returns a table:

```lua
local m = vm:stat("/etc/test.conf")
print(m.size)        -- 10
print(m.mtime)       -- float: seconds since epoch
print(m.mtime_ns)    -- int: nanoseconds since epoch
print(m.perm)        -- POSIX mode bits (≤ 4095, i.e. 0o7777)
print(m.entry_type)  -- "file" / "directory" / "symlink" / "fifo" / "socket" /
                     -- "block_device" / "char_device" / "other"
```

`mtime` carries seconds; `mtime_ns` carries the same time at full precision. Use `mtime_ns` for exact comparisons; use `mtime` when "around what o'clock" is enough.

`perm` is in the POSIX range. Lua 5.4 doesn't accept `0o…` literals — use decimal or hex (`0x180` for 0o600). `4095` is `0o7777`, the upper bound.

### `vm:listdir(path)`

Returns an array of `{name, entry_type}` tables:

```lua
for _, e in ipairs(vm:listdir("/etc")) do
    print(e.name, e.entry_type)
end
```

### `vm:mkdir(path, opts?)`

Create a directory:

```lua
vm:mkdir("/tmp/d")
vm:mkdir("/tmp/d/e/f", {parents = true})
vm:mkdir("/tmp/private", {perm = 0x1c0})  -- 0o700
```

### `vm:unlink(path)`

Remove a file or empty directory. Errors on non-empty directory (use `vm:run("rm -rf …")` for that).

### `vm:rename(from, to)`

Atomic rename within the guest filesystem.

## Low-level: `vm:open_file`

Returns a [File](~provium/reference/file-handle) userdata that you can read, write, seek, and close.

```lua
local h = vm:open_file("/tmp/data", {read=true, write=true, create=true, truncate=true})
h:write("hello")
h:seek(0)
local s = h:read(5)
h:close()
```

### Mode table

At least one of `read`, `write`, `append` must be true; an empty mode table errors at open time.

| Key | Effect |
|---|---|
| `read` | Open for reading. |
| `write` | Open for writing. |
| `create` | Create if absent. |
| `truncate` | Truncate to zero bytes on open. |
| `append` | Append-only writes. |
| `exclusive` | Combine with `create=true` for `O_EXCL`. |
| `perm` | POSIX mode for newly-created files. |

```lua
-- Write-only, create, truncate, mode 0o600.
local h = vm:open_file("/etc/secret", {write=true, create=true, truncate=true, perm=0x180})
```

### Reading

```lua
local h = vm:open_file("/etc/hostname", {read=true})

local first = h:read(64)         -- up to 64 bytes
local rest  = h:read_all()       -- drain to EOF
h:close()
```

`h:read(n)` returns up to `n` bytes. At EOF, returns the empty string `""` — POSIX semantics. Loops:

```lua
while true do
    local chunk = h:read(4096)
    if chunk == "" then break end
    -- process chunk
end
```

`h:read_all()` chunks at 64 KiB internally and returns the concatenated bytes.

### Writing

```lua
local h = vm:open_file("/tmp/data", {write=true, create=true, truncate=true})
local n = h:write("hello world")
-- n is 11 (bytes actually written, may be less than #data on partial write)
h:close()
```

### Seek and tell

```lua
local h = vm:open_file("/tmp/x", {read=true})
h:seek(10, "set")             -- absolute offset 10
h:seek(5, "cur")              -- relative +5 from current
h:seek(-1, "end")             -- 1 byte before EOF
h:tell()                      -- current offset
```

`tell()` re-reads the position from the agent (a no-op `Seek(Cur, 0)`) rather than trusting the host-side cache. This stays honest when a previous read or write returned mid-flight.

### Closing

```lua
h:close()
h:close()  -- second close is fine; idempotent
h:read(1)  -- raises "file is closed"
```

The harness's resource walker auto-closes files at scope end via the `_provium_close_test_scope` hook, so you can usually omit explicit closes. Closing manually is good practice when the file's lifetime is bounded by a clear point in the test.

### Raw fd

```lua
local fd = h:fd()              -- u64 handle id
vm:ioctl(fd, MY_IOCTL_NUM)
```

`fd()` returns `0` on a closed file, otherwise the handle's u64 value. Useful for `vm:ioctl(fd, …)` and `vm:syscall(…)` invocations that take a file descriptor.

## Tailing files

Two ways to tail:

### `vm:tail_file(path, opts?)`

Subscribe to bytes appended to a file. Returns a [Tail](~provium/reference/streams).

```lua
local stream = vm:tail_file("/var/log/messages")
vm:run("logger 'hello'"):assert_ok()
local line = stream:read_until("\n", "5s")
t:assert(line:find("hello"))
```

`opts.start` controls the starting position:

| Value | Effect |
|---|---|
| `"end"` (default) | Only bytes appended after the call. |
| `"beginning"` / `"start"` | Replay from byte 0, then continue tailing. |
| Integer | Start from that exact byte offset. |

### `file:tail_stream()`

Open a tail rooted at the file handle's current cursor:

```lua
local h = vm:open_file("/var/log/messages", {read=true})
h:seek(0, "end")
local stream = h:tail_stream()
-- stream now subscribes from current EOF onwards
```

Useful when you've already seek-d to a known position.

### `vm:fd_stream(fd_or_file)`

Open a tail against an existing file handle (by fd integer or by the File userdata directly):

```lua
local h = vm:open_file("/dev/console", {read=true})
local stream = vm:fd_stream(h)
```

## Common patterns

### Writing then reading back

```lua
test("config round-trips", function(t)
    local body = "key1=value1\nkey2=value2\n"
    vm:write_file("/etc/test.conf", body)
    t:assert_eq(vm:read_file("/etc/test.conf"), body)
    t:assert_eq(vm:stat("/etc/test.conf").size, #body)
end)
```

### Asserting permission bits

Lua 5.4 has no `0o…` literal. Use decimal or hex:

```lua
test("private file is 0600", function(t)
    local h = vm:open_file("/etc/secret", {write=true, create=true, perm=0x180})  -- 0o600
    h:close()
    t:assert_eq(vm:stat("/etc/secret").perm, 0x180)
end)
```

### Tailing a log while the test acts

```lua
test("logger writes are persisted", function(t)
    local stream = vm:tail_file("/var/log/messages")
    vm:run("logger 'event 1'"):assert_ok()
    vm:run("logger 'event 2'"):assert_ok()
    stream:expect("event 1", "5s")
    stream:expect("event 2", "5s")
end)
```

### Listing then filtering

```lua
test("/tmp has the expected files", function(t)
    vm:write_file("/tmp/a", "")
    vm:write_file("/tmp/b", "")
    local names = {}
    for _, e in ipairs(vm:listdir("/tmp")) do
        if e.entry_type == "file" then table.insert(names, e.name) end
    end
    table.sort(names)
    t:assert(names[1] == "a" and names[2] == "b")
end)
```

## Files inside a worker

`worker:open_file(path, mode)` allocates the file under the worker's namespace. The returned File auto-registers with the test scope:

```lua
local w = vm:spawn_worker()
local h = w:open_file("/tmp/from-worker", {write=true, create=true})
h:write("hi")
h:close()
```

Otherwise the API is identical.

## Batch I/O for low latency

For many small ops back-to-back, batch them in one round trip:

```lua
local results = vm:batch(function(b)
    b:write_file("/tmp/a", "1")
    b:write_file("/tmp/b", "2")
    b:write_file("/tmp/c", "3")
    b:read_file("/tmp/a")
    b:stat("/tmp/b")
end)
```

Each entry in `results` is `{ok=value}` or `{err=msg}`. A failure on one op doesn't short-circuit the rest. See [VM batch](~provium/reference/vm#vmbatchfn) for the per-op return shape.

## See also

- [VM reference](~provium/reference/vm) — `read_file`, `write_file`, `stat`, `mkdir`, `listdir`, `unlink`, `rename`, `open_file`, `tail_file`, `fd_stream`.
- [File handle reference](~provium/reference/file-handle) — every method on the File userdata.
- [Streams and tails](~provium/writing-tests/streams-and-tails) — patterns for tail streams.
