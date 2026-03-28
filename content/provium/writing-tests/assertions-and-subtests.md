---
title: Assertions and Sub-tests
type: concept
order: 30
description: Provium provides assert helpers and a test() function for organizing multiple named test cases in a single file.
related:
  - getting-started/quick-start
  - writing-tests/running-commands
---

Provium provides assertion helpers and a sub-test system for organizing tests within a single file.

## Assertions

Three assertion functions are available globally in every test script:

### assert(condition, message)

Raises an error if the condition is falsy (false or nil):

```lua
assert(fd >= 0, "open failed: " .. fd)
assert(r.ok, "command failed")
assert(r.stdout.contains("expected"))
```

Provium overrides Lua's built-in `assert` with a version that produces clearer error messages.

### assert_eq(expected, actual, message)

Checks equality between two values. On failure, the error message shows both values:

```lua
assert_eq(0, r.exit_code, "expected success")
assert_eq("hello\n", r.stdout.value, "wrong output")
assert_eq(data, h.SID_SYSTEM, "expected SYSTEM SID")
```

### assert_contains(haystack, needle, message)

Checks that a string contains a substring:

```lua
assert_contains(r.stdout.value, "Linux", "not Linux")
assert_contains(log, "initialized", "module not loaded")
```

## Sub-tests

The `test(name, fn)` function runs a named test case within the file. Each sub-test has isolated failure handling — a failure in one does not prevent others from running.

```lua
local vm = provium.create("minimal")
vm:boot()
vm:mount_vfs()

test("kernel boots", function()
    local r = vm:exec("uname -r")
    assert(r.ok)
end)

test("proc mounted", function()
    local r = vm:exec("cat /proc/version")
    assert(r.ok)
end)

test("sysfs mounted", function()
    local r = vm:exec("ls /sys/kernel/")
    assert(r.ok)
end)

vm:shutdown()
```

### How sub-tests are reported

Each sub-test is reported individually:

```
  boot.lua ... ok (3 tests, 2.1s)
    · kernel boots ... ok
    · proc mounted ... ok
    · sysfs mounted ... ok
```

If any sub-test fails, the file is marked as failed:

```
  boot.lua ... FAIL (2.1s)
    · kernel boots ... ok
    · proc mounted ... FAIL: /proc/version: No such file or directory
    · sysfs mounted ... ok
```

### Shared setup

Code outside `test()` blocks runs once and is shared across all sub-tests. Use this for VM setup:

```lua
local h = dofile("tests/helpers.lua")
local vm = provium.fixture("kacs")

-- This token is available to all sub-tests
local fd = h.open_self_token(vm)

test("token is primary", function()
    local data = h.query_token(vm, fd, h.TOKEN_CLASS_TYPE)
    local ttype = provium.unpack("u32", data)
    assert_eq(ttype, 1, "expected Primary")
end)

test("token is SYSTEM", function()
    local data = h.query_token(vm, fd, h.TOKEN_CLASS_USER)
    assert_eq(data, h.SID_SYSTEM)
end)

vm:shutdown()
```

### When to use sub-tests

Use `test()` blocks when a file contains multiple logically distinct assertions that share the same VM setup. Without sub-tests, a failure on the first assertion stops the entire file. With sub-tests, every test case runs and all failures are visible at once.

For simple tests with a single assertion or a linear sequence where each step depends on the previous, sub-tests are unnecessary.

## Marking tests as not yet implemented

The `todo()` function marks a test case as not yet implemented. It counts as a skip, not a failure:

```lua
test("complex scenario", function()
    todo("waiting on kernel feature X")
end)

test("another todo", function()
    todo()
end)
```

Output:

```
    · complex scenario ... todo: waiting on kernel feature X
    · another todo ... todo
```

Use `todo()` as a placeholder for test cases you plan to write later. It documents intent without producing false failures.
