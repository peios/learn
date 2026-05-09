---
title: Workers
type: concept
description: Fork the guest agent into independent worker processes to test multi-process scenarios — credential isolation, inter-process communication, and concurrent access.
related:
  - provium/writing-tests/vm-lifecycle
  - provium/kernel-testing/raw-syscalls
---

Some tests need multiple independent processes inside the same VM — testing credential isolation, inter-process communication, or concurrent access to shared resources. Workers provide this by forking the guest agent.

## Spawning a worker

`vm:spawn()` forks the guest agent process and returns a worker handle:

```lua
local worker = vm:spawn()
```

The worker has the same API as a VM — you call `worker:exec()`, `worker:syscall()`, `worker:read_file()`, and everything else. Each worker gets its own vsock connection to the host, its own process ID, and its own copy of the parent's state at fork time.

```lua
local vm = provium.fixture("kacs")

local worker = vm:spawn()

-- Both can execute commands independently
local r1 = vm:exec("echo parent")
local r2 = worker:exec("echo child")
assert_contains(r1.stdout.value, "parent")
assert_contains(r2.stdout.value, "child")

worker:kill()
vm:shutdown()
```

## Fork vs thread mode

By default, `vm:spawn()` forks the agent using `fork()`. The worker gets:

- A separate PID
- A separate address space (copy-on-write)
- A separate file descriptor table
- Independent credentials

For tests that need shared file descriptors but independent credentials, pass `{thread = true}`:

```lua
local worker = vm:spawn({thread = true})
```

In thread mode, the worker uses `clone(CLONE_THREAD)` instead of fork. The worker shares the file descriptor table and address space with the parent but has independent credentials. This is useful for testing per-thread impersonation and credential isolation.

## Independent credentials

The key use case for workers is testing credential isolation. Each worker can install a different security token and verify that access decisions are independent:

```lua
local h = dofile("tests/helpers.lua")
local vm = provium.fixture("kacs")

local worker = vm:spawn()

-- Install a non-SYSTEM token on the worker
local user_sid = h.domain_user(1001)
local spec = h.build_token_spec({
    user_sid = user_sid,
    privs_present = h.SE_CHANGE_NOTIFY,
})
local token_fd = h.create_token(worker, spec)
h.install_token(worker, token_fd)

-- Worker now has domain user credentials
local wfd = worker:syscall(h.SYS_KACS_OPEN_SELF_TOKEN, 0, h.TOKEN_QUERY)
local wdata = h.query_token(worker, wfd, h.TOKEN_CLASS_USER)
assert_eq(wdata, user_sid, "worker should have domain user token")

-- Parent still has SYSTEM
local pfd = h.open_self_token(vm)
local pdata = h.query_token(vm, pfd, h.TOKEN_CLASS_USER)
assert_eq(pdata, h.SID_SYSTEM, "parent should still have SYSTEM")

worker:kill()
vm:shutdown()
```

## Killing workers

`worker:kill()` closes the connection. The worker process detects EOF and exits. Always kill workers when you are done with them:

```lua
local worker = vm:spawn()
-- ... use worker ...
worker:kill()
```

If a test exits without killing its workers, Provium cleans them up automatically — but explicit cleanup makes intent clear.

## Multiple workers

A test can spawn multiple workers from the same VM:

```lua
local w1 = vm:spawn()
local w2 = vm:spawn()
local w3 = vm:spawn()

-- Each has a different PID
local pid1 = w1:syscall(39) -- getpid
local pid2 = w2:syscall(39)
local pid3 = w3:syscall(39)
assert(pid1 ~= pid2 and pid2 ~= pid3)

w1:kill()
w2:kill()
w3:kill()
```

## Workers vs multiple VMs

Workers and multiple VMs serve different purposes:

| | Workers | Multiple VMs |
|---|---|---|
| **Isolation** | Shared kernel, separate processes | Separate kernels, fully isolated |
| **Speed** | Near-instant fork | Full boot (or fixture resume) |
| **Use case** | Multi-process testing within one kernel | Testing interactions between independent systems |
| **Shared state** | Shared kernel memory, filesystem | None |
| **Credentials** | Independent per worker | Independent per VM |

Use workers when you need multiple identities or processes inside the same kernel. Use multiple VMs when you need fully isolated environments.
