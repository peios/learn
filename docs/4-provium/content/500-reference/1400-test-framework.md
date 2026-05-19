---
title: Test framework
type: reference
description: The test() function registers tests, the t context object provides assertions and skip / fail / log, todo() declaratively skips a whole file, and wait_until() polls a predicate to truthy.
---

Provium's test framework is implemented mostly in Lua and installed onto every test file's state. This page documents every callable: `test`, `todo`, `wait_until`, the `t` context, and the per-test metadata table.

## `test(name, [meta,] fn)`

Register a test in declaration order. Two call shapes:

```lua
test("simple", function(t)
    t:assert(true)
end)

test("with metadata", {tags={"smoke"}, timeout="30s"}, function(t)
    t:assert(true)
end)
```

| Argument | Required | Type | Description |
|---|---|---|---|
| `name` | yes | string | Test name. Must be unique within the file (duplicate names raise at registration). |
| `meta` | no | table | Per-test metadata. See [meta tags](~provium/reference/meta-tags). |
| `fn` | yes | function | The test body, called with `(t)` — the test context. |

Tests run sequentially in declaration order. Each test gets a fresh `t` context. The harness wraps the call in `pcall` semantics — a Lua `error()` becomes a `Failed` outcome; clean return becomes `Passed`; explicit `t:skip()` becomes `Skipped`.

Duplicate names within a file error at registration time:

```
test: duplicate name `foo` in this file
```

## `todo(reason?)`

Declarative file-scope skip. When called at top level (before any `test()` body runs), every registered test is reported `Skipped` with the given `reason`. Test bodies are not executed.

```lua
todo("waiting on the spec")
test("a", function(t) … end)
test("b", function(t) … end)
-- Both report Skipped with reason "waiting on the spec".
```

Without an argument, defaults to `"todo"`.

Skipped tests still emit `TestSkipped` events with the meta intact, so coverage and dashboards see the same shape they would for an inline `t:skip()`.

## `wait_until(predicate, opts?)`

Call `predicate` repeatedly until it returns truthy (and return that value), or until the timeout lapses. Useful for polling guest-side conditions that don't have a stream interface.

```lua
local pid = wait_until(function()
    local r = vm:run("pidof nginx")
    if r:ok() then return r.stdout:match("%d+") end
end, {timeout = "30s", interval = "200ms", desc = "nginx running"})
```

Opts:

| Field | Default | Type | Description |
|---|---|---|---|
| `timeout` | `10` | number (seconds) or string `"30s"` / `"500ms"` / `"5m"` / `"2h"` | Total time to wait before giving up. |
| `interval` | `0.1` | number (seconds) | Time between predicate calls. |
| `desc` | `"condition"` | string | Used in the timeout error message. |

On timeout, errors with `wait_until: <desc> not met within <timeout>s`. The error includes the offending input (e.g. `bad timeout string ...`) when the timeout argument is malformed.

The predicate runs under `pcall` — if it raises, the error propagates immediately (with the raise location) rather than being treated as a "not yet" signal.

`wait_until` uses wall-clock seconds, not CPU time, so the deadline elapses while `_provium_sleep` is pausing.

## The `t` context

A fresh `t` table is built per test. It carries the test's name, metadata, and a sticky `_failed` flag so a `pcall(t:assert(false))` is still classified as a failure (the inner pcall swallows the raise, but the runner inspects `_failed` on the Ok return path).

### Fields

- `t.name` — the test's name.
- `t.meta` — the per-test metadata table (or `{}` if none was given).

### Assertions

Every assertion error includes the offending values in the message — assertion failures are self-explanatory without needing to read context.

#### `t:assert(cond, msg?)`

Raise if `cond` is falsy. `msg` is the failure message; defaults to `"assertion failed"`.

#### `t:assert_eq(a, b, msg?)`

Raise if `a ~= b`. The error message includes both values: `<msg>: <a> ~= <b>`.

#### `t:assert_neq(a, b, msg?)`

Raise if `a == b`. Mirror of `assert_eq`.

#### `t:assert_contains(haystack, needle, msg?)`

Raise unless `string.find(haystack, needle, 1, true)` returns non-nil. **Both arguments must be strings**; non-string args raise immediately with a "slice 2 limit" pointer.

#### `t:assert_raises(fn, msg?)`

Run `fn` under `pcall` and assert that it raised. Returns the error value if the raise happened. Errors with `<msg>: expected to raise` if `fn` returned cleanly.

The sticky `_failed` flag is saved before invoking `fn` and restored on a successful raise — that way an assertion *inside* `fn` (used to trigger the expected raise) doesn't leave `_failed=true` and poison the rest of the test.

### Skip and fail

#### `t:fail(msg?)`

Mark the test failed and raise. `msg` defaults to `"explicit failure (t:fail)"`.

#### `t:skip(reason)`

Mark the test skipped and raise via the internal sentinel. `reason` is recorded in the `TestOutcome` and emitted in the `TestSkipped` event.

```lua
test("only on btrfs", function(t)
    if vm:run("findmnt /"):ok() and not vm:run("findmnt -t btrfs /"):ok() then
        t:skip("not a btrfs root")
    end
    -- … btrfs-specific test body …
end)
```

### Logging

#### `t:log(msg)`

Append `msg` (any value, converted via `tostring`) to the test's log array. The log is included in the `FileOutcome.tests[i].log` and emitted alongside `TestPassed` / `TestFailed` events.

Useful for diagnostic output that should accompany failures. Unlike `print`, `t:log` is structured and tied to the specific test.

## Outcomes

A test ends in one of three states:

| Status | Triggered by |
|---|---|
| **Passed** | Test fn returned without raising AND `_failed` flag wasn't set. |
| **Failed** | Test fn raised (via `error()`, `t:assert*`, `t:fail`), or its `_failed` flag was sticky after pcall caught an inner assertion. A Rust panic during the test also marks Failed and poisons every subsequent test in the file. |
| **Skipped** | `t:skip(reason)` was called, OR `meta.skip = true` / `meta.skip = "reason"`, OR `--tag` / `--no-tag` filtered the test out, OR `--include-slow` was off and `meta.slow = true`, OR file-scope `todo()` was called. |

A skipped test produces no event lifecycle other than `TestSkipped`. A failed test additionally captures the last 4 KiB of every booted VM's console log into the `TestFailed.console_excerpt` field — useful for diagnosing kernel-side regressions without reproducing the run.

## Time and timeouts

Per-test timeouts come from `meta.timeout`. File-default timeouts come from `provium.timeout`. Per-test wins.

The watchdog fires by tearing down the entire file's lab — there is no finer-grained cancellation in v1 because there is no cooperative cancel point in the AgentClient ops. **Practical implication:** for files using `provium.reset_between_tests = true` the lab is restored before the next test anyway, so the lab-wide tear-down is harmless. For files that share live state across tests, a per-test timeout invalidates the rest of the file. Don't put a `meta.timeout = N` on a flaky test in a state-sharing file expecting siblings to be unaffected.

## See also

- [Meta tags](~provium/reference/meta-tags) — full reference for `meta.slow`, `meta.tags`, `meta.skip`, `meta.timeout`, `meta.spec`.
- [provium global](~provium/reference/provium-module) — `provium.reset_between_tests`, `provium.timeout`.
- [The test function](~provium/writing-tests/the-test-function) — patterns for organising a test file.
