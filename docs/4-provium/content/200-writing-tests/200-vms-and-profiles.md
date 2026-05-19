---
title: VMs and profiles
type: how-to
description: How to create, boot, snapshot, restore, pause, reset, and inject files into VMs. How profiles map to kernel/initrd choices, and how multiple profiles let one test run against different kernels.
---

Every Provium test ultimately drives one or more guest VMs. This page covers the lifecycle: creating a VM, picking its profile, controlling boot, taking snapshots, and tearing down.

The exhaustive reference is on [VM](~provium/reference/vm).

## Creating a VM

```lua
local vm = provium:vm("name", "profile")
```

The first arg is the VM's name (per-scope unique). The second arg is a profile name from `provium.toml`. The VM is in `Created` state until you call `:boot()`.

**Two forms.** `provium:vm(name, profile)` *creates* a VM in the current scope. `provium:vm(name)` *looks one up* by name, walking from the current scope to the file root. Inside a `test()` body, the current scope is the per-test scope; at file top-level, it's the file root. See [labs and scope](~provium/writing-tests/labs-and-scope) for the full rules.

Optional third arg is a boot-opts table (memory, cpus, kernel cmdline, files, etc.):

```lua
local vm = provium:vm("v", "peios", {
    memory = "2G",
    cpus = 4,
    kernel_cmdline = "console=hvc0 quiet earlyprintk=hvc0",
    rng_seed = 0xdeadbeef,
    initial_time = 1700000000,
    files = {
        {path = "/etc/hostname", content = "v"},
        {path = "/root/.ssh/authorized_keys", content = pubkey},
    },
})
```

These can also be passed to `vm:boot(opts)` for per-boot overrides. Per-boot opts merge with creation-time opts.

## Booting

```lua
local vm = provium:vm("v", "peios"):boot()
```

`:boot()` returns `self` so you can chain. The VM is in `Booted` state on return. A `vm_spawned` event fires as soon as the agent has handshaken; consumers see it before `:boot()` returns.

For multi-VM tests, you can boot each individually:

```lua
local a = provium:vm("a", "peios"):boot()
local b = provium:vm("b", "peios"):boot()
```

Or batch-boot via the lab:

```lua
provium:vm("a", "peios")
provium:vm("b", "peios")
provium:boot()                -- boots both
```

The batch form is mainly useful when you've declared a topology in a fixture builder and want to bring it up atomically.

## Profiles

A profile is a `[profiles.<name>]` block in `provium.toml`:

```toml
[profiles.peios]
kernel   = "/build/peios/bzImage"
initrd   = "/build/peios/initrd.cpio.gz"
cmdline  = "console=hvc0 quiet"
guest_os = "peios"
```

Each profile names a (kernel, initrd, cmdline) tuple. A test picks which profile to use by name:

```lua
provium:vm("a", "peios")           -- uses [profiles.peios]
provium:vm("a", "peios-debug")     -- uses [profiles.peios-debug]
```

You can have any number of profiles. Common patterns:

| Pattern | Profiles |
|---|---|
| Test against multiple kernel versions | `peios-stable`, `peios-mainline` |
| Compare optimised and debug builds | `peios`, `peios-debug` |
| Test pre/post a feature flag | `peios-prefeatx`, `peios-postfeatx` |

Multi-profile fixtures invalidate every cached fixture when any profile's kernel or initrd identifier changes — see [fixtures and dependencies](~provium/running-tests/fixtures-and-dependencies).

## Lifecycle methods

```
Created ──:boot()──> Booted ──:pause()──> Paused
                       │                    │
                       ├─:reset()→Booted    ├─:resume()→Booted
                       ├─:power_button()──> Shutdown
                       └─:shutdown()─────> Shutdown
```

| Method | What it does |
|---|---|
| `vm:boot(opts?)` | `Created → Booted`. |
| `vm:pause()` | `Booted → Paused`. |
| `vm:resume()` | `Paused → Booted`. |
| `vm:shutdown()` | Anything → `Shutdown`. |
| `vm:reset()` | `Booted → Booted` (warm reboot). |
| `vm:power_button()` | `Booted → Shutdown` (graceful ACPI). |

Operations against a VM in the wrong state error cleanly with the offending state in the message — `vm:reset() on Created VM must error`. The harness's auto-close walker uses `vm:close()`, which is a no-op idempotent shutdown.

You typically don't call `:shutdown()` explicitly. The harness's resource-graph walker tears every VM down at the appropriate scope boundary: test-scope VMs at the end of their `test()` body, file-scope VMs at file end. (`reset_between_tests = true` snapshots and restores instead — see [labs and scope](~provium/writing-tests/labs-and-scope).)

## Boot opts in detail

| Key | Type | Effect |
|---|---|---|
| `memory` | int (bytes) or `"512M"`/`"2G"` | VM memory cap. Hands to QEMU as `-m <size>`. |
| `cpus` | int | vCPU count. Hands to QEMU as `-smp <n>`. |
| `kernel_cmdline` | string | Replaces the profile's `cmdline`. Useful for per-VM `loglevel`, `nokaslr`, etc. |
| `rng_seed` | int (u64) | Seeds `virtio-rng`. Use for determinism in randomized tests. |
| `initial_time` | int or float (sec since epoch) | Sets the guest's wall clock at boot. Float for sub-second precision. |
| `files` | array of `{path, content}` | Files to inject into the guest's filesystem before init runs. The agent injects them by appending to the initramfs cpio. |

```lua
local vm = provium:vm("v", "peios", {
    memory = "1G",
    cpus = 2,
    rng_seed = 42,
    initial_time = 1700000000.5,
    files = {
        {path = "/etc/test.conf", content = "key=value\n"},
    },
}):boot()
```

## Querying VM state

```lua
vm:name()              -- "v"
vm:profile()           -- "peios"
vm:state()             -- "created" | "booted" | "paused" | "shutdown" | "dead"
vm:cid()               -- assigned vsock CID, or nil before boot
vm:is_quiescent()      -- true if no in-flight ops, no open files, no open streams
vm:open_file_count()   -- count of open files via the agent
vm:open_stream_count() -- count of active streams (tails, captures, console-reads)
```

`is_quiescent` and the count accessors are useful for snapshot precondition asserts:

```lua
test("snapshot is taken at quiescence", function(t)
    local vm = provium:vm("v", "peios"):boot()
    vm:run("…")
    t:assert(vm:is_quiescent(), "VM must be quiescent before snapshot")
    local s = vm:snapshot()
    t:assert(s:size() > 0)
end)
```

## Snapshots

```lua
local s = vm:snapshot()              -- writes to a tempfile
local s = vm:snapshot("/tmp/x.snap") -- writes to that path
```

Returns a [Snapshot](~provium/reference/snapshot) userdata wrapping the path. Use it to:

- Restore later in the same test: `vm:shutdown(); vm:restore(s)`.
- Inspect size: `s:size()`.
- Delete: `s:delete()` (idempotent).

The snapshot file is what fixture builders return. If the snapshot fails because of an open stream, the error names the stream's creation site — close streams before snapshotting:

```lua
test("snapshot needs no open streams", function(t)
    local vm = provium:vm("v", "peios"):boot()
    local stream = vm:tail_file("/var/log/messages")
    -- vm:snapshot() would error here; close first.
    stream:close()
    local s = vm:snapshot()
end)
```

## Restoring

Restore from a Snapshot userdata or a bare path string:

```lua
vm:shutdown()
vm:restore(s)            -- from snapshot userdata
vm:restore("/tmp/x.snap") -- from path
```

The VM moves through `Shutdown → Created → Booted` (the restored state is already `Booted`). Restoring requires the VM to be in `Created` or `Shutdown` first.

## Determinism patterns

For tests that depend on randomness or wall-clock time, fix both at boot:

```lua
local vm = provium:vm("v", "peios", {
    rng_seed = 0xdeadbeef,
    initial_time = 1700000000,
}):boot()
```

After boot, you can move time forward (or backward) with `vm:clock():advance(N)` — see [Clock reference](~provium/reference/clock).

## Pausing for inspection

`vm:pause()` freezes the guest's vCPUs. Useful for:

- Time-sensitive tests where you need to read multiple bits of state without races.
- Snapshotting (the snapshot path will pause anyway, but explicit pause makes the test's intent clear).

```lua
vm:pause()
local before = vm:read_file("/proc/loadavg")
vm:resume()
```

## Reset and power-button

`vm:reset()` warm-reboots the guest — same VM, same RAM image initially, then init re-runs. Stays in `Booted`.

`vm:power_button()` sends ACPI power-button. The guest's init handles it as a graceful shutdown signal (typically: stop services, sync filesystems, kernel halts). Ends in `Shutdown`.

```lua
test("guest survives reset", function(t)
    local vm = provium:vm("v", "peios"):boot()
    vm:write_file("/tmp/before", "1")
    vm:reset()
    -- /tmp is tmpfs in the test profile; vm:reset() is a warm
    -- reboot, so /tmp is fresh. Check that the test's expectation
    -- matches what the profile actually does.
    local r = vm:run("test ! -f /tmp/before")
    r:assert_ok()
end)
```

## Multi-VM topologies

The two-VM pattern is the workhorse of networking tests:

```lua
local lan = provium:bridge("lan")
local a   = provium:vm("a", "peios"):boot()
local b   = provium:vm("b", "peios"):boot()
lan:attach({a, b})

test("a can reach b", function(t)
    a:run("ping -c 1 -W 1 b.lan"):assert_ok()
end)
```

For larger topologies, use sub-labs to keep names organised — see [labs and scope](~provium/writing-tests/labs-and-scope).

## See also

- [VM reference](~provium/reference/vm) — every method, every option.
- [Snapshot reference](~provium/reference/snapshot) — snapshot/lab-snapshot userdata.
- [provium.toml reference](~provium/configuration/provium-toml) — profile configuration.
- [Bridges and impairments](~provium/writing-tests/bridges-and-impairments) — wiring VMs together.
