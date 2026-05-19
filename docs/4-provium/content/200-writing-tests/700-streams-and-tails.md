---
title: Streams and tails
type: how-to
description: Patterns for the three stream userdata types — when to use next vs read_until vs expect vs drain, how to handle EOF, what creation_site is for, and how snapshots interact with live streams.
---

Provium has three stream userdata types — Tail, Capture, and ConsoleStream — that share a common surface: `next` / `read_until` / `expect` / `drain` / `close` / `eof` / `creation_site`. This page is the practical guide.

The exhaustive method reference is on [Streams](~provium/reference/streams).

## What returns what

| Source | Type | Use for |
|---|---|---|
| `vm:tail_file(path, opts?)` | Tail | Following a file as it grows. |
| `vm:fd_stream(fd_or_file)` | Tail | Following an open file handle. |
| `file:tail_stream()` | Tail | Following a file from its current cursor. |
| `proc:stdout_stream()` / `proc:stderr_stream()` | Tail | Following an async process's output. |
| `bridge:capture()` | Capture | Sniffing every packet on a bridge. |
| `nic:capture()` | Capture | Sniffing one VM's TAP. |
| `console:read()` | ConsoleStream | Reading the guest's serial console. |

All three types support the same operations. The differences are in the underlying transport and the per-frame shape.

## Operations

### `:next(timeout?)` — pull the next chunk

Returns the next chunk of bytes as a Lua string, or `nil` at EOF / timeout.

```lua
local stream = vm:tail_file("/var/log/messages")
vm:run("logger 'event'"):assert_ok()
local frame = stream:next("5s")
print(frame)  -- "Jan  1 00:00:00 v: event\n"
```

Frame shape per type:

- **Tail**: one frame per agent-side write — usually one log line, possibly a multi-line write.
- **Capture**: chunks of pcap bytes from tcpdump's pipe (variable size, up to 64 KiB).
- **ConsoleStream**: chunks of console bytes from the chardev socket (variable size, up to 64 KiB).

Default timeout: 10 seconds.

### `:read_until(pattern, timeout?)` — read until a substring

```lua
local line = stream:read_until("\n", "5s")
```

Pulls frames until `pattern` (a Lua string of bytes) appears in the accumulated buffer. Returns the prefix up to AND including the matched bytes. Errors with the pattern in the message on timeout.

Bytes past the matched suffix are kept as `pending` and replayed on the next call. Important: this means a sequence of `read_until` calls never silently loses data.

### `:expect(pattern, timeout?)` — assert and discard

```lua
stream:expect("ready", "30s")
-- next() / read_until() will see anything past "ready"
```

Like `read_until`, but discards the matched prefix. Returns nothing. Use this when you want the assertion semantics — "this stream produced X" — without caring about the bytes themselves.

### `:drain(timeout?)` — collect everything available

```lua
local chunks = stream:drain("2s")
-- chunks is a Lua array of strings
local body = table.concat(chunks)
```

Read frames until the stream is quiet for the timeout, EOF, or the timeout lapses. Useful for "what did the stream produce in this window?"

Default timeout: 0.5 seconds (much shorter than `next` because drain's intent is "snapshot what's available").

Pending bytes from a prior `expect`/`read_until` come out as the first entry, so drain doesn't silently lose them.

### `:close()` — drop the underlying transport

```lua
stream:close()
stream:next()    -- returns nil (closed stream is semantically EOF)
stream:expect("…")  -- raises "stream closed"
```

Idempotent. Pending bytes are dropped on close so a `:next` after close can't drain stale data.

### `:eof()` — has the stream reported EOF?

```lua
while not stream:eof() do
    local chunk = stream:next("100ms")
    if chunk then process(chunk) end
end
```

Returns `true` once the underlying transport reported EOF AND no `pending` bytes remain. Pending bytes mean `eof` returns `false` until they've been consumed.

### `:creation_site()` — where was this stream opened?

```lua
local site = stream:creation_site()
-- {file = "tests/x.test.lua", line = 42}
```

Returns `{file=string, line=int}` for the test-author frame at creation time, or `nil` if the stream was opened from a frame that doesn't look like `*.test.lua` / `*.fixture.lua`. Mostly useful for snapshot diagnostics — when a snapshot fails because of a live stream, the error names the offending stream's creation site.

## Choosing between next, read_until, expect, drain

| Scenario | Use |
|---|---|
| "Tell me when X happens." | `:expect("X", timeout)` |
| "What's the next line?" | `:read_until("\n", timeout)` |
| "Pull bytes until I have enough." | Loop on `:next(timeout)` |
| "Snapshot everything in this window." | `:drain(timeout)` |
| "Has the stream finished?" | `:eof()` after `:next()` returns nil. |

`:expect` is the workhorse for log-watching tests — it has tight, unambiguous error messages on timeout, and it doesn't dump bytes you don't want into your handler.

`:read_until` is the workhorse when you need the matched bytes (parsing structured log lines, checking that the prefix matches an expected shape).

`:next` is most useful in loops where you want to inspect each frame before deciding what to do.

`:drain` is most useful at the end of a test to confirm "nothing weird snuck through" or to capture a quiet window for offline analysis.

## EOF semantics

A closed stream is semantically EOF — `:next` returns `nil`, `:read_until` and `:expect` error. Idiomatic loops:

```lua
while true do
    local frame = stream:next("100ms")
    if not frame then break end       -- EOF or timeout
    process(frame)
end
```

For Tail specifically, the closed-stream-returns-nil behaviour mirrors Capture and ConsoleStream so the `while s:next() do … end` idiom works across all three types.

## Tail-specific: starting position

```lua
vm:tail_file("/var/log/messages")                    -- start at end (default)
vm:tail_file("/var/log/messages", {start = "end"})   -- explicit
vm:tail_file("/var/log/messages", {start = "beginning"})  -- replay from byte 0
vm:tail_file("/var/log/messages", {start = 1024})    -- start at byte 1024
vm:tail_file("/var/log/messages", {start = -512})    -- last 512 bytes then follow
```

`"end"` is the most common — only bytes appended after the call are streamed. `"beginning"` is useful for tests that need to assert on the whole file. Non-negative integer offsets are useful when you've previously seek'd to a known position. **Negative integers** mean "N bytes before EOF" — provium stats the file and resolves to an absolute offset. If N is larger than the current size, the stream starts at byte 0. Floats are accepted and truncated toward zero.

## Capture: pcap bytes

`bridge:capture()` and `nic:capture()` produce raw pcap bytes (the standard pcap-savefile format, not pcap-ng). Concatenate the chunks and pipe into `tshark`, `tcpdump -r -`, or a parser library:

```lua
local cap = lan:capture()
vm:run("ping -c 5 b.lan")
local pcap = table.concat(cap:drain("3s"))
cap:close()

-- Save to disk and analyse out-of-process.
local f = io.open("/tmp/test.pcap", "wb"); f:write(pcap); f:close()
local r = vm:run("tcpdump -r /tmp/test.pcap -n")
print(r.stdout)
```

Capture pins the bridge's `active_captures` counter — the snapshot precondition checks this counter before allowing `vm:snapshot()`. So a live capture blocks snapshots; this is on purpose, not a bug. Close the capture before snapshotting.

## ConsoleStream: bytes from the chardev

```lua
local console = vm:console()
local stream  = console:read()

stream:expect("login:", "30s")
console:write("root\n")
stream:expect("Password:", "5s")
console:write("toor\n")
stream:expect("# ", "5s")
```

ConsoleStream wraps a `UnixStream` to QEMU's chardev socket. Reads come back as raw bytes from the chardev — typically the boot log, login prompt, and anything the guest has written to `/dev/hvc0` since the last read.

Mid-stream `ConnectionReset` and `BrokenPipe` are mapped to "console EOF" — they happen on VM reset / shutdown, where they're semantically EOF rather than I/O errors.

The connect-time read timeout is 50 ms. The `:next(timeout)` arg overrides it for the duration of the call and the previous timeout is restored afterwards, so a `next("5s")` followed by a bare `next()` doesn't inherit the 5s deadline.

## Process streams

`proc:stdout_stream()` and `proc:stderr_stream()` open Tail streams subscribed to captured output:

```lua
local proc = vm:run_async("server")
local out  = proc:stdout_stream()
out:expect("listening on :8080", "10s")
-- now hit the server
```

The stream's `creation_site` and `kind`/`detail` carry the process handle id, so snapshot diagnostics can name "proc_stdout_stream(handle=42)" when something refuses a snapshot.

## File streams

`file:tail_stream()` opens a Tail rooted at the file's current cursor:

```lua
local h = vm:open_file("/var/log/messages", {read=true})
h:seek(0, "end")  -- start at current EOF
local stream = h:tail_stream()
-- stream subscribes from EOF onwards, just like vm:tail_file with start="end"
```

`vm:fd_stream(fd_or_file)` is the lower-level form — accepts either an integer fd (from `file:fd()`) or the File userdata directly:

```lua
local h = vm:open_file("/dev/console", {read=true})
local stream = vm:fd_stream(h)
```

## Snapshots and live streams

Snapshots refuse to run while a stream is live. The error names the stream:

```
provium: vm:snapshot() refused — file `tests/x.test.lua` has live streams:
  - tail_file("/var/log/messages") at tests/x.test.lua:42
  - proc_stdout_stream(handle=7) at tests/x.test.lua:55
Close the streams before snapshotting (or remove the snapshot).
```

Two ways out:

1. Close the streams explicitly before `vm:snapshot()`.
2. Move the snapshot earlier in the test, before the streams are opened.

The pre-condition is enforced for both single-VM (`vm:snapshot()`) and lab (`provium:snapshot()`) snapshots. It also blocks `provium.reset_between_tests = true` files at chunk-load time when file-scope streams are open.

## Common patterns

### "Wait for a log line"

```lua
local stream = vm:tail_file("/var/log/messages")
vm:run("trigger-something"):assert_ok()
stream:expect("trigger landed", "5s")
```

### "Race a process boot against its readiness signal"

```lua
local proc = vm:run_async("server")
local out  = proc:stdout_stream()
out:expect("ready", "10s")
-- safe to hit the server now
```

### "Capture pcap during a specific operation"

```lua
local cap = lan:capture()
vm:run("ping -c 3 b.lan"):assert_ok()
local pcap = table.concat(cap:drain("2s"))
cap:close()
```

### "Drive an interactive prompt over the console"

```lua
local console = vm:console()
local stream  = console:read()
stream:expect("login:", "30s")
console:write("root\n")
stream:expect("# ", "10s")
```

### "Confirm nothing weird snuck through"

```lua
local cap = lan:capture()
vm:run("…benign workload…"):assert_ok()
local frames = cap:drain("1s")
cap:close()
local pcap = table.concat(frames)
local r = vm:run("tcpdump -r /dev/stdin -n", {stdin = pcap})
t:assert(not r.stdout:find("malformed"))
```

## See also

- [Streams reference](~provium/reference/streams) — every method, EOF semantics, type-specific notes.
- [Console reference](~provium/reference/console) — `console:read` and `console:expect`.
- [VM reference](~provium/reference/vm) — `vm:tail_file`, `vm:fd_stream`.
- [File handle reference](~provium/reference/file-handle) — `file:tail_stream`.
