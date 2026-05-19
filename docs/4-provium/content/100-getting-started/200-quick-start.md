---
title: Quick Start
type: how-to
description: Install Provium, configure a profile, write a first test, and run it. Five minutes from a clean checkout to a passing test.
---

This guide walks through the minimum setup needed to run one Provium test against a real VM. It assumes you have KVM, QEMU, iproute2, and nftables installed; see [project structure](~provium/getting-started/project-structure) for prerequisites detail.

## Install

Provium is a Cargo workspace. Build the host binary:

```
cd provium
cargo build --release --bin provium
```

The binary lands at `target/release/provium`. Optionally, install it onto your `PATH`:

```
cargo install --path provium-host --bin provium
```

Verify:

```
provium --help
```

## Pre-flight check

Provium runs a startup pre-flight on every invocation. You can run it explicitly to catch environment issues before you start writing tests:

```
provium --no-preflight  # to skip; useful in containers without KVM
```

The pre-flight checks for:

| Check | Recovery |
|---|---|
| `/dev/kvm` exists and is openable | `sudo modprobe kvm-intel` (or `kvm-amd`); add yourself to the `kvm` group |
| `/dev/vhost-vsock` exists | `sudo modprobe vhost_vsock` |
| `ip` and `tc` on `PATH` | `apt install iproute2` / `pacman -S iproute2` |
| `nft` on `PATH` | `apt install nftables` / `pacman -S nftables` |
| `qemu-system-x86_64` on `PATH` | `apt install qemu-system-x86_64` / `pacman -S qemu-base` |
| Effective `CAP_NET_ADMIN` | `sudo setcap cap_net_admin,cap_net_raw=eip $(which provium)` |

## Provide a kernel and initrd

Provium boots VMs by direct kernel boot (`-kernel` / `-initrd`). You need:

- A bzImage-format kernel.
- An initramfs with a working `/init`. Almost any initrd works — a vanilla distro initramfs, a buildroot image, a from-scratch cpio with just `/init` and busybox.

Provium injects its own agent into your initrd at launch (concatenated cpio, content-hash cached) and chains to your `/init`. You don't need to bake `provium-agent` into your image. To opt out (e.g. when your image already bundles an agent), set `inject_agent = false` on the profile — see [provium.toml reference](~provium/configuration/provium-toml).

For Peios, the kernel + initrd are built by the Peios image-build pipeline. For ad-hoc use, see the [project structure](~provium/getting-started/project-structure) section.

## Create `provium.toml`

Provium loads `./provium.toml` (override with `--config`). The minimum useful config declares one profile:

```toml
[provium]
roots = ["tests"]

[profiles.peios]
kernel  = "/path/to/bzImage"
initrd  = "/path/to/provium-initrd.cpio.gz"
cmdline = "console=hvc0 quiet"
```

`[profiles.<name>]` is the dictionary `provium:vm("name", "<profile>")` looks up. The `roots` setting is the list of directories scanned for `*.test.lua` and `*.fixture.lua` files; it also controls where `require("helper")` resolves.

See [provium.toml reference](~provium/configuration/provium-toml) for every field.

## Write your first test

Create `tests/smoke.test.lua`:

```lua
test("guest boots and runs commands", function(t)
    local vm = provium:vm("smoke", "peios"):boot()
    local r = vm:run("uname -a")
    r:assert_ok()
    t:assert(r.stdout:find("Linux"), "uname should report Linux: " .. r.stdout)
end)

test("filesystem ops round-trip", function(t)
    local vm = provium:vm("smoke", "peios"):boot()
    vm:write_file("/tmp/hello", "world")
    t:assert_eq(vm:read_file("/tmp/hello"), "world")
end)
```

Two things to know:

- Each `test(...)` body runs in its own scope. The two `provium:vm("smoke", "peios")` calls above each create a fresh VM in their respective test scope; the `"smoke"` name in test 1 and test 2 are independent and don't collide. Each VM is silently shut down at end of test.
- To share a VM across tests, declare it at file top-level (`local vm = provium:vm("v", "peios"):boot()`) and either capture the userdata as a Lua local or look it up from inside tests via the 1-arg form `provium:vm("v")`.

## Run it

```
provium tests/
```

You should see:

```
PASS tests/smoke.test.lua (2 passed, 0 failed, 0 skipped)

1 file(s); 2 passed, 0 failed, 0 skipped; 3.42s
```

Useful flags for the development loop:

- `provium tests/ --watch` — re-runs on file change (poll-based, 500 ms).
- `provium tests/smoke.test.lua` — run a single file.
- `provium tests/ --filter smoke` — substring match against the relative path.
- `provium tests/ --rerun-failed` — re-run only files that failed last time.
- `provium tests/ -v` — show passing tests too.
- `provium tests/ --json` — line-delimited JSON output, one object per file.

See [the CLI reference](~provium/reference/cli) for every flag.

## Add an assertion that should fail

Sanity-check the failure path:

```lua
test("fails on purpose", function(t)
    t:assert_eq(1, 2, "1 must equal 2")
end)
```

```
FAIL tests/smoke.test.lua (2 passed, 1 failed, 0 skipped)
    FAIL fails on purpose
        1 must equal 2: 1 ~= 2
```

Provium's exit code is `0` when every file passed (or skipped), `1` when one or more files had a failure or timed out, and `2` for internal errors (config load failure, pre-flight failure, etc.).

## What's next

- Read [project structure](~provium/getting-started/project-structure) to understand how `provium.toml`, `tests/`, fixtures, and the cache directory all fit together.
- Read the [test-framework reference](~provium/reference/test-framework) for everything the `test()` and `t` API expose.
- Read [VMs and profiles](~provium/writing-tests/vms-and-profiles) for the full set of `provium:vm(...)` options.
- Skim the [CLI reference](~provium/reference/cli) to see what's available for the running side.
