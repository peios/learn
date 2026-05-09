---
title: Background Jobs
type: concept
description: Start long-running commands in the background and poll or wait for their completion.
related:
  - provium/writing-tests/running-commands
  - provium/writing-tests/workers
---

Some tests need to start a process and interact with the VM while it runs — a daemon, a server, or a long-running computation. Background jobs let you start commands without blocking the test script.

## Starting a background job

`vm:background(cmd)` starts a command in the guest and returns immediately with a job handle:

```lua
local job = vm:background("sleep 10 && echo done > /tmp/marker")
```

The job handle is a table with two fields:

| Field | Type | Description |
|---|---|---|
| `id` | number | Job ID for tracking |
| `pid` | number | PID of the background process in the guest |

The command runs in the guest agent's process context. The test script continues executing while the job runs.

## Waiting for a job

`vm:job_wait(job, timeout)` waits for a background job to finish:

```lua
local result = vm:job_wait(job, 15)
```

The `timeout` argument is in seconds. If the job finishes within the timeout, the result contains the exit code and output:

| Field | Type | Description |
|---|---|---|
| `exit_code` | number | Process exit code (`-1` if still running) |
| `stdout` | string | Standard output |
| `stderr` | string | Standard error |
| `running` | boolean | `true` if the job is still running (timeout expired) |

With `timeout = 0` (or omitted), `job_wait` polls without blocking — it returns immediately with the job's current state.

### Polling pattern

```lua
local job = vm:background("long-running-command")

-- Do other work...
vm:exec("setup-something")

-- Now wait for the job
local result = vm:job_wait(job, 30)
assert(not result.running, "job did not finish in time")
assert_eq(result.exit_code, 0, "job failed")
```

## Killing a job

`vm:job_kill(job)` kills a background job and returns its final result:

```lua
local result = vm:job_kill(job)
```

The result has the same format as `job_wait`. The exit code reflects how the process was terminated.

## Combining with wait_until

Background jobs pair well with `vm:wait_until()` for testing daemons that produce observable side effects:

```lua
-- Start a daemon
local job = vm:background("/usr/bin/mydaemon")

-- Wait for it to be ready
vm:wait_until(function()
    local r = vm:exec("test -f /var/run/mydaemon.pid")
    return r.ok
end, {timeout = 5, desc = "daemon ready"})

-- Test the daemon's behavior
local r = vm:exec("curl http://localhost:8080/health")
assert(r.ok)

-- Clean up
vm:job_kill(job)
```

## wait_until

`vm:wait_until(fn, opts)` polls a callback function until it returns true or a timeout expires:

```lua
vm:wait_until(function()
    local r = vm:exec("test -f /tmp/ready")
    return r.ok
end, {timeout = 10, interval = 0.5, desc = "ready file"})
```

| Option | Type | Default | Description |
|---|---|---|---|
| `timeout` | number | `10` | Maximum wait time in seconds |
| `interval` | number | `0.5` | Seconds between polls |
| `desc` | string | `"condition"` | Description for the timeout error message |

If the timeout expires, `wait_until` raises an error with the description.
