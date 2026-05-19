---
title: Worker
type: reference
description: A Worker userdata gives a test concurrent agent connections to the same guest VM, so you can drive multiple ops in parallel without spinning up another VM.
---

A Worker is what `vm:spawn_worker()` returns: a sub-agent connection to the same VM. It exposes the same VM-style API for running commands, opening files, and issuing syscalls — handles allocated under it live in the worker's own namespace on the agent side.

Workers are not a hard isolation boundary in v1. They're bookkeeping namespaces — handles are routable from outside the worker, but the agent tracks per-worker membership for cleanup. Per-worker dispatch wire ops are deferred to a future slice; for now, treat workers as parallelism, not security.

## Constructing

| Source | Returns |
|---|---|
| `vm:spawn_worker()` | New worker on the VM's main agent. |
| `vm:spawn_worker({thread = false})` | Same. (`{thread = true}` is rejected with a future-work pointer.) |

## Methods

The worker mirrors the VM's run / file / syscall surface. Where semantics differ from the VM equivalent, it's noted explicitly.

### `worker:run(cmd, opts?)`

Synchronous exec. Same call shape as [`vm:run`](~provium/reference/vm#vmruncmd_or_args-opts). Returns a [RunResult](~provium/reference/vm#runresult).

### `worker:run_async(cmd, opts?)`

Async spawn. Returns a [Process](~provium/reference/process). Like `vm:run_async`, the `timeout` opt is rejected — pass it to `proc:wait` instead.

The returned Process is auto-registered with the test's resource registry, so the scope walker SIGTERMs and reaps it at scope end. Without this, a worker-spawned child would leak past the test boundary.

### `worker:open_file(path, mode_table)`

Open a guest-side file under the worker's namespace. Returns a [File](~provium/reference/file-handle). Same mode-table shape as `vm:open_file`.

The returned File is auto-registered with the test scope so `file:close()` fires automatically at scope end.

### `worker:syscall(nr, …)`

Direct syscall. Same call shape as [`vm:syscall`](~provium/reference/vm#vmsyscallnr-) — both the integer-only and table forms work. Returns the same `{ret, result, errno, out_bufs}` shape.

### `worker:kill(sig?)`

Broadcast a signal to every async process spawned under this worker. Argument shape mirrors `proc:kill`: nil → SIGTERM, int → that signal, string → friendly name.

A bad argument type (e.g. a Lua table) errors with the type-name in the message rather than silently defaulting to SIGTERM. This catches test-code typos.

### `worker:join()`

Wait for every in-flight worker child to exit. Returns whatever the agent reports as the joined exit summary.

### `worker:handle()`

Returns the worker's opaque handle id.

### `worker:close()`

Auto-close hook. SIGTERMs every in-flight worker child, then joins. The scope walker fires this at scope end.

## Concurrency pattern

Workers shine for tests that need two threads of control inside the same guest:

```lua
test("two concurrent writers don't tear", function(t)
    local vm = provium:vm("v", "peios"):boot()
    local w1 = vm:spawn_worker()
    local w2 = vm:spawn_worker()

    -- Each worker writes its own block of data, in parallel.
    local p1 = w1:run_async("dd", {args = {"if=/dev/urandom", "of=/tmp/a", "bs=1M", "count=8"}})
    local p2 = w2:run_async("dd", {args = {"if=/dev/urandom", "of=/tmp/b", "bs=1M", "count=8"}})

    p1:wait("10s"):assert_ok()
    p2:wait("10s"):assert_ok()

    t:assert_eq(vm:stat("/tmp/a").size, 8 * 1024 * 1024)
    t:assert_eq(vm:stat("/tmp/b").size, 8 * 1024 * 1024)
end)
```

For coordination between workers, use [`lab:barrier(name, count, timeout?)`](~provium/reference/lab#barriername-count-timeout) or a guest-side primitive (file, fifo, etc.).

## See also

- [VM](~provium/reference/vm) — `vm:spawn_worker()` and the parent surface.
- [Process](~provium/reference/process), [File](~provium/reference/file-handle) — what worker ops return.
