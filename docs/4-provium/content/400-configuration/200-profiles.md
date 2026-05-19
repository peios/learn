---
title: Profiles
type: how-to
description: Patterns for using multiple profiles — testing across kernel versions, separating production from debug builds, gating slow tests on the mainline-only profile, and what happens to the fixture cache when profiles change.
---

A profile is one named `(kernel, initrd, cmdline, guest_os)` tuple in `provium.toml`. Tests pick a profile by name when they create a VM. This page covers the practical patterns.

The configuration field reference is on [provium.toml](~provium/configuration/provium-toml).

## When you need more than one profile

For most projects, one profile is enough — `peios`, pointing at the latest build. You'd add more when:

- You're testing across kernel versions (`peios-stable`, `peios-mainline`).
- You want a debug build available for diagnosing failures (`peios-debug`).
- You're gating tests on a feature flag in the kernel (`peios-prefeatx`, `peios-postfeatx`).
- You're testing a port to a new architecture (`peios-arm64`).

## Declaring multiple profiles

```toml
[profiles.peios]
kernel   = "/build/peios/bzImage"
initrd   = "/build/peios/initrd.cpio.gz"
cmdline  = "console=hvc0 quiet"

[profiles.peios-debug]
kernel   = "/build/peios-debug/bzImage"
initrd   = "/build/peios-debug/initrd.cpio.gz"
cmdline  = "console=hvc0 debug loglevel=7 nokaslr"

[profiles.peios-stable]
kernel   = "/build/peios-stable/bzImage"
initrd   = "/build/peios-stable/initrd.cpio.gz"
cmdline  = "console=hvc0 quiet"
```

Tests pick:

```lua
provium:vm("v",        "peios")
provium:vm("debug-v",  "peios-debug")
provium:vm("stable-v", "peios-stable")
```

A test can mix profiles in the same file — useful for compatibility testing:

```lua
test("stable client can talk to mainline server", function(t)
    local lan    = provium:bridge("lan")
    local server = provium:vm("server", "peios"):boot()
    local client = provium:vm("client", "peios-stable"):boot()
    lan:attach({server, client})

    -- Run a real protocol against the mismatched pair.
    server:run("python3 -m http.server 8080 &")
    wait_until(function()
        return server:run("ss -ltn | grep :8080"):ok()
    end, {timeout = "5s"})
    client:run("curl -s http://server.lan:8080/"):assert_ok()
end)
```

## Profile choice patterns

### Default vs debug

The most common split: a fast `peios` build for the default loop, and a `peios-debug` build with `loglevel=7`, `nokaslr`, and (probably) `KASAN`/`UBSAN` enabled. Use the debug profile when reproducing a kernel bug:

```lua
test("debug build reveals the leak", {tags = {"slow", "debug"}}, function(t)
    local vm = provium:vm("v", "peios-debug"):boot()
    vm:run("…workload that leaks…")
    local r = vm:run("dmesg | grep -i 'BUG:'")
    -- KASAN / UBSAN reports show up here in the debug build.
end)
```

### Cross-version compatibility

Two profiles, one per release line. Ship a small handful of cross-version tests:

```lua
test("rolling upgrade: stable client + mainline server", function(t)
    -- … as above …
end)

test("rolling upgrade: mainline client + stable server", function(t)
    -- … inverse …
end)
```

Tag these `cross-version` and gate via `--no-tag cross-version` in the dev loop. CI runs them on a nightly cadence with `--include-slow`.

### Feature-flag gating

Two profiles built from the same source with one feature toggled:

```toml
[profiles.peios-prefeatx]
kernel  = "/build/peios-prefeatx/bzImage"   # FEATX disabled
# …

[profiles.peios-postfeatx]
kernel  = "/build/peios-postfeatx/bzImage"  # FEATX enabled
# …
```

Tests that exercise FEATX-specific behaviour pick `peios-postfeatx`; regression tests run against both.

```lua
test("featx changes API behaviour", function(t)
    local before = provium:vm("v1", "peios-prefeatx"):boot()
    local after  = provium:vm("v2", "peios-postfeatx"):boot()

    local r1 = before:run("…")
    local r2 = after:run("…")
    t:assert_neq(r1.stdout, r2.stdout)
end)
```

## Per-VM cmdline overrides

The profile's `cmdline` is the default; `boot_opts.kernel_cmdline` overrides it for one VM:

```lua
local vm = provium:vm("v", "peios", {
    kernel_cmdline = "console=hvc0 quiet maxcpus=1 isolcpus=0",
}):boot()
```

This is useful for one-off testing of cmdline-sensitive features. For cmdline configurations you use repeatedly, declare a dedicated profile.

## Default profile selection

A few CLI subcommands take an optional profile arg — when omitted, they fall back to "the first profile in `provium.toml` sorted by name":

| Subcommand | Behaviour |
|---|---|
| `provium repl --fixture <path>` (no profile) | First profile by sorted name. |
| `provium fixture build <path>` | Uses the first profile's kernel/initrd as the cache-key kernel inputs. |

To make the default predictable, name your most common profile so it sorts first alphabetically. `aaa-default` is ugly but it works; `peios` is fine when it's your only profile.

## What happens to the cache when profiles change

The fixture cache key folds in the kernel and initrd identifiers of **every profile** in `provium.toml`, sorted by name for determinism. Practical consequences:

| Action | Cache effect |
|---|---|
| Edit a kernel image (any profile) | Every fixture invalidates. |
| Edit an initrd image (any profile) | Every fixture invalidates. |
| Add a new profile | Every fixture invalidates (the new profile's kernel/initrd are folded in). |
| Remove a profile | Every fixture invalidates. |
| Rename a profile | Every fixture invalidates (sort order changes). |
| Edit `cmdline` on a profile | Cache is unaffected (cmdline isn't in the key). |
| Change `cache_dir` | Cache is unaffected — the new dir is just empty. |

This is deliberately conservative. A new profile means a new kernel could behave differently, so the existing fixtures might be subtly stale. Rather than guess, the harness rebuilds.

If you need to add a profile without invalidating the cache, you can't. Either accept the rebuild or use a sibling `provium.toml` with `--config alt-config.toml`.

## Multi-arch profiles (preview)

In v1, the QemuVmm backend invokes `qemu-system-x86_64` exclusively — there's no per-profile arch field yet. To run on aarch64, you'd have to swap the binary at the harness level (not currently exposed).

When multi-arch lands, the profile is the natural place for an `arch = "x86_64"` / `arch = "aarch64"` field.

## See also

- [provium.toml reference](~provium/configuration/provium-toml) — every field.
- [VMs and profiles](~provium/writing-tests/vms-and-profiles) — `provium:vm(name, profile, opts?)`.
- [Fixtures and dependencies](~provium/running-tests/fixtures-and-dependencies) — what triggers a fixture rebuild.
