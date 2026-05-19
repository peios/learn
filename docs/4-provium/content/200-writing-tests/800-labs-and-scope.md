---
title: Labs and scope
type: how-to
description: How to use sub-labs to organise multi-VM topologies, claim resources from the pool, synchronise across workers with barriers, snapshot and restore whole labs, and use lab fixtures for cached setups.
---

A Lab is the unit of resource ownership in Provium. The `provium` global is the root Lab; sub-labs let you carve out scoped subsets. This page covers the patterns for using labs effectively.

The exhaustive method reference is on [Lab](~provium/reference/lab).

## Per-test scope

Each `test()` body runs in its own ephemeral sub-Lab. Resources you create inside a test are local to that test; resources declared at file scope are visible (via lookup fallthrough) and persist across tests.

```lua
-- File scope: persists across all tests
local shared = provium:vm("shared", "peios"):boot()

test("first", function(t)
    local local_vm = provium:vm("local", "peios"):boot()  -- test scope
    -- both `shared` and `local_vm` work here
end)
-- `local_vm` is shutdown silently here

test("second", function(t)
    local local_vm = provium:vm("local", "peios"):boot()  -- DIFFERENT VM
    -- The "local" name in test 1 and test 2 are independent — no collision.
    -- `shared` is still here, with whatever state test 1 left.
end)
```

The rules:

| Operation | What happens in a test() body |
|---|---|
| `provium:vm(name, profile)` | Creates in the test scope. Auto-shutdown at test end. |
| `provium:vm(name)` | Looks up name: test scope first, then file root. Errors if not found. |
| `provium.foo` (dot access) | Same lookup as above; returns `nil` on miss. |
| `provium:bridge(name, opts?)` | Same as VMs: create local, lookup walks up. |
| `provium:lab(name)` | Creates a sub-lab in the test scope (auto-cleaned). |
| `provium:vm_fixture(name)` / `provium:lab_fixture(name)` | Always materialises at file root, regardless of where called. The fixture cache stays warm across tests. |

**Shadow detection.** Declaring a name at test scope when it already exists at file scope is an error, not a silent shadow:

```lua
local shared = provium:vm("shared", "peios"):boot()

test("oops", function(t)
    -- This errors: "name already declared at parent scope (lab `provium`).
    -- Pick a different name, or use `provium:vm("shared")` to reuse it."
    local v = provium:vm("shared", "peios")
end)
```

The intent: if you wanted the file-scope VM, use the lookup form (`provium:vm("shared")`). If you wanted a fresh independent VM, pick a different name.

**Federation sub-labs are isolated.** A sub-lab created via `provium:lab("dc1")` has no parent chain — `dc1.web` doesn't fall through to find a sibling DC's "web". This is intentional; federation models distinct sites.

**Things that don't walk parents** (each by design):

- `vm_names` / `bridge_names` / `members` — return only the local scope's contents.
- `boot` / `shutdown` / `pause` / `resume` — batch ops on the local scope's VMs.
- `snapshot` / `restore` — operate on the local scope plus its sub-labs (downward, not upward).
- `claim`, `barrier` — file-scope coordination primitives; test-scope claims/barriers are isolated.

## Per-test scope vs `reset_between_tests`

These solve different problems and compose well together — they're not alternatives.

| | Per-test scope (default, automatic) | `reset_between_tests = true` (opt-in) |
|---|---|---|
| **What it isolates** | New declarations made inside a `test()` body. | Mutable state of file-scope resources. |
| **Mechanism** | Test-scope sub-Lab; auto-shutdown at test end. | Snapshot after file setup; restore between tests. |
| **Per-test cost** | Booting the test-scope VMs you declared. | Snapshot restore (cheaper than full boot, slower than nothing). |
| **What it doesn't help with** | File-scope VMs accumulating cruft across tests. | Name collisions across tests for ad-hoc VMs. |

The typical heavy test file uses both:

```lua
provium.reset_between_tests = true

-- File-scope setup: expensive cluster build, snapshot baseline.
local lan = provium:bridge("lan")
local web = provium:vm("web", "peios"):boot()
local db  = provium:vm("db",  "peios"):boot()
lan:attach({web, db})
db:run("psql -c 'CREATE TABLE t (...)'")  -- baseline schema

test("api writes propagate to db", function(t)
    -- web and db are restored to baseline at start of every test.
    web:run("curl -X POST http://localhost/items -d '...'")
    t:assert_eq(db:run("psql -c 'SELECT count(*) FROM t'"):row(), "1")
end)

test("scratch VM joins the network", function(t)
    -- Throwaway VM, test-scope, auto-shutdown at test end.
    local probe = provium:vm("probe", "peios"):boot()
    lan:attach(probe)  -- bridge is file-scope, found via parent walk
    probe:run("curl -s http://web/health"):assert_ok()
end)
```

Without per-test scope, the second test couldn't introduce `probe` without colliding (or having to pick a unique name per test). Without `reset_between_tests`, the first test's row in `t` would be visible to subsequent tests.

When to use which:

- **Per-test scope alone** is enough when each test is self-contained: declare what you need, do work, done. The smoke-test shape — `local vm = provium:vm("v", "peios"):boot(); vm:run(...)` repeated per test.
- **Add `reset_between_tests`** when you have a non-trivial setup at file scope (configured cluster, populated DB, attached topology) and tests mutate it. Pays for itself once a per-test setup-cost crosses the snapshot/restore time.
- **Skip both** by declaring `reset_between_tests = false` AND being careful with naming when you actually want state to accumulate across tests (e.g. progressive integration scenarios).

## Why sub-labs

Most simple tests use only the root lab — `provium:vm("a", "peios")`, `provium:bridge("lan")`. Sub-labs are useful when:

- You're modeling multi-DC topologies (`provium:lab("dc1")`, `provium:lab("dc2")`).
- You want to snapshot or restore a coherent subset of resources.
- You want to use `lab_fixture` to cache an entire topology.

```lua
local dc1 = provium:lab("dc1")
dc1:vm("a", "peios")
dc1:vm("b", "peios")
dc1:bridge("lan"):attach({dc1.a, dc1.b})

local dc2 = provium:lab("dc2")
dc2:vm("c", "peios")
dc2:bridge("lan"):attach(dc2.c)
```

`dc1.a` is shorthand for `dc1:vm("a")`. The dot lookup tries vm → bridge → sub-lab in order; missing names return `nil` (no error).

## Anonymous sub-labs

```lua
local sub = provium:lab()  -- name auto-generated: __lab_0, __lab_1, ...
```

Useful for one-shot subsets that don't need a stable name.

## Membership: include and remove

You can move resources between labs:

```lua
local v = provium:vm("v", "peios")
local sub = provium:lab("sub")
sub:include(v)            -- v is now in sub
provium:remove(v)         -- and gone from root
```

`lab:include` accepts:

- A single VM, Bridge, or sub-Lab userdata.
- An array of those.

It errors on duplicate names within the lab (`DuplicateVmName`, `DuplicateBridgeName`), reserved names (`pack`, `unpack`, `vm_fixture`, `lab_fixture`), and on shadow conflicts when called from a test scope and the name is already declared at a parent scope.

`lab:remove` is graph-state only — the underlying VM, bridge, or sub-lab is NOT shut down. It's removed from the lab's child list. Useful when you want to take ownership of a resource somewhere else.

Both forms accept either a name or a userdata.

## Listing members

```lua
provium:vm_names()          -- {"v", "v2"}
provium:bridge_names()      -- {"lan"}
provium:sub_lab_names()     -- {"dc1", "dc2"}
provium:members()           -- [{kind="vm", name="v"}, {kind="bridge", name="lan"}, …]
```

`members()` is the unified accessor; the others are sliced by kind.

## Batch lifecycle

The lifecycle methods on a lab apply to every direct VM child (not recursive):

```lua
provium:boot()       -- boot every VM in the root lab
provium:shutdown()   -- shutdown every VM
provium:pause()
provium:resume()
```

Useful when a test sets up the topology declaratively and wants to bring it up atomically:

```lua
local lan = provium:bridge("lan")
local a   = provium:vm("a", "peios")
local b   = provium:vm("b", "peios")
lan:attach({a, b})
provium:boot()                -- boots a and b together
```

For per-sub-lab control:

```lua
local dc1 = provium:lab("dc1")
dc1:vm("a", "peios"):boot()
dc1:vm("b", "peios"):boot()
-- dc1 boots independently of the root lab
```

## Resource claims

Each test file may make at most one claim against the dispatcher's resource pool:

```lua
provium:claim({memory = "4G", cpus = 4})

test("…", function(t) end)
test("…", function(t) end)
```

The claim sits across the file's lifetime; it's released at file end. A second `:claim` errors with `claim already taken`. When no pool is wired (REPL / single-file ad-hoc runs) the call is still one-shot but otherwise a no-op.

Why claim? The dispatcher won't oversubscribe — it tracks total RAM and CPU budget across files and only schedules a file when its claim plus the per-file overhead fits. A file that needs 4 VMs at 2 GiB each should claim ~10 GiB so it doesn't get scheduled alongside other heavy files and OOM the host.

```lua
-- For a 3-VM, 2-CPU-each, 1-GiB-each test:
provium:claim({memory = "5G", cpus = 7})  -- 3 GiB + per-file overhead, 6 + 1 vCPU
```

The claim emits `claim_acquired` and `claim_released` events for observability.

## Barriers

Barriers synchronise across workers (or between workers and the test driver):

```lua
local w1 = vm:spawn_worker()
local w2 = vm:spawn_worker()

co.wrap(function()
    -- … worker 1 prep work …
    provium:barrier("ready", 2)
    -- … now safe to proceed …
end)()

co.wrap(function()
    -- … worker 2 prep work …
    provium:barrier("ready", 2)
    -- … now safe to proceed …
end)()
```

`lab:barrier(name, count, timeout?)` blocks the caller until `count` callers have hit the same `name`-keyed barrier. Default timeout: 60 seconds. Raises on timeout.

For inter-VM coordination (e.g. between two guests), use a guest-side primitive (file in a shared mount, fifo, network message). Barriers are host-side only.

## Snapshot and restore

```lua
local snap = provium:snapshot()           -- to a tempdir, returns LabSnapshot
local snap = provium:snapshot("/tmp/x")   -- to that path, returns the path string
```

The `LabSnapshot` userdata gives you `snap:path()`, `snap:size()`, `snap:delete()`. Restore with:

```lua
provium:restore(snap)             -- from LabSnapshot userdata
provium:restore("/tmp/x")         -- from path
```

The restore reads `lab.json` from the snapshot directory, then per-VM `.snap` files.

The same precondition that blocks `vm:snapshot()` blocks `lab:snapshot()` — open streams cause the snapshot to refuse with the offending stream's creation site.

## Lab fixtures

A lab fixture builds a multi-VM topology once, caches the snapshot, and restores it per test:

```lua
-- tests/fixtures/cluster.fixture.lua
local lan = provium:bridge("lan")
local a = provium:vm("a", "peios"):boot()
local b = provium:vm("b", "peios"):boot()
lan:attach({a, b})
return provium:snapshot()
```

```lua
-- tests/uses-cluster.test.lua
test("cluster has both VMs reachable", function(t)
    local cluster = provium:lab_fixture("fixtures/cluster")
    cluster.a:run("ping -c 1 -W 1 b.lan"):assert_ok()
end)
```

`provium:lab_fixture(path)` returns a Lab userdata wrapping a fresh sub-lab with the fixture restored. The cache key folds source bytes + transitive fixture refs + helper requires + every profile's kernel and initrd identifier.

For single-VM fixtures, use `provium:vm_fixture(path)` — same cache mechanism, returns a VM directly.

## Common patterns

### Multi-DC topology

```lua
local function dc(name, vms)
    local d = provium:lab(name)
    for _, n in ipairs(vms) do d:vm(n, "peios") end
    d:bridge("lan"):attach(d:vm_names())
    return d
end

local dc1 = dc("dc1", {"a", "b"})
local dc2 = dc("dc2", {"c", "d"})
provium:boot()  -- boot every VM
```

### File-level resource claim

```lua
provium:claim({memory = "8G", cpus = 6})

test("3-VM cluster", function(t)
    -- The dispatcher won't run another file alongside this one
    -- if the pool can't afford 8G + 6 CPUs.
end)
```

### Cached cluster fixture

```lua
-- fixture builder
return provium:snapshot()  -- after building the topology

-- test usage
local cluster = provium:lab_fixture("fixtures/big-cluster")
local a = cluster.a  -- look up by name from the restored sub-lab
```

### Reset-between-tests with a sub-lab snapshot

`provium.reset_between_tests = true` snapshots the root lab. To reset only a subset:

```lua
local sub = provium:lab("workspace")
local v = sub:vm("v", "peios"):boot()
local snap = sub:snapshot()

test("a", function(t)
    v:write_file("/tmp/data", "1")
end)

test("b", function(t)
    sub:restore(snap)  -- explicit restore
    t:assert_eq(v:read_file("/tmp/data"), "")  -- back to baseline
end)
```

This pattern is more verbose than `provium.reset_between_tests = true` but works when only part of the lab needs resetting.

## Auto-close ordering

When a test scope ends (per-test or per-file), the harness's resource graph walker closes resources in reverse-dependency order:

1. Streams (Tails, Captures, ConsoleStreams).
2. Processes (`vm:run_async`, `worker:run_async`).
3. Files (`vm:open_file`, `worker:open_file`).
4. Workers.
5. VMs and bridges (file-end only).

This is implemented as a Lua-side registry that every `register_resource` call appends to. Resources are closed in priority order, then within a priority by registration order.

You don't usually need to call `:close` yourself — the walker fires it automatically. Calling explicitly is fine (the methods are idempotent) and useful when the resource's lifetime is bounded by a clear point in the test.

## See also

- [Lab reference](~provium/reference/lab) — every method.
- [provium global](~provium/reference/provium-module) — file-scope configuration globals.
- [VM reference](~provium/reference/vm), [Bridge reference](~provium/reference/bridge) — what lives in a lab.
- [Pool and parallelism](~provium/running-tests/pools-and-parallelism) — how the dispatcher uses claims.
