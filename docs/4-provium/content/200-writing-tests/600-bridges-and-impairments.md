---
title: Bridges and impairments
type: how-to
description: How to wire VMs into bridges, partition them symmetrically and directionally, inject latency / drop rate / bandwidth limits, isolate single VMs, capture pcap, and route to the outside world via uplink.
---

Provium's networking is real Linux bridges with TAP attachments. You declare a topology, the harness realizes it as the VMs boot, and you can mutate it (partition, impair, capture) at runtime.

The exhaustive method reference is on [Bridge](~provium/reference/bridge) and [Nic](~provium/reference/nic).

## Wiring up

```lua
local lan = provium:bridge("lan")
local a   = provium:vm("a", "peios"):boot()
local b   = provium:vm("b", "peios"):boot()
lan:attach({a, b})  -- atomic; either all attach or none do

-- a can reach b.
a:run("ping -c 1 -W 1 b.lan"):assert_ok()
```

`bridge:attach(vm_or_list)`:

- Single VM: `lan:attach(a)`.
- Bare string (graph-state only — no QMP wiring): `lan:attach("a")`.
- Array: `lan:attach({a, b, c})`. Validated atomically before any element is recorded — a bad type at index N fails before any commit.

The host-side bridge interface and per-VM TAPs come up the first time any attached VM boots.

## Multi-bridge topologies

```lua
local mgmt = provium:bridge("mgmt")
local data = provium:bridge("data")
local a    = provium:vm("a", "peios"):boot()
local b    = provium:vm("b", "peios"):boot()

mgmt:attach({a, b})    -- both VMs on mgmt
data:attach({a, b})    -- both VMs on data too

-- a:nic("mgmt") and a:nic("data") return separate Nic handles.
local mgmt_nic = a:nic("mgmt")
local data_nic = a:nic("data")
```

Inside the guest, each NIC shows up as a separate interface. The mapping from bridge name to guest-side interface name (eth0, eth1, …) is determined by attachment order sorted by bridge name. For portable tests, prefer `vm:nic("mgmt")` (by bridge name) over `vm:nic("eth0")` (by guest-name index).

## Partitions

A partition is a network-layer drop between two specific VMs. Two flavours:

### Symmetric

```lua
lan:partition(a, b)        -- A↔B traffic dropped both ways
lan:unpartition(a, b)      -- restore
```

Symmetric partitions are graph-state — they install drop rules at boot via nft and lift cleanly.

### Directional

```lua
lan:partition({from = a, to = b})    -- only A→B dropped; B→A still flows
lan:unpartition({from = a, to = b})
```

Directional partitions install per-TAP nft rules and require **both endpoints to be already attached and booted**. Otherwise they error with a "call bridge:attach first" pointer (the rule would otherwise install onto a non-existent TAP and silently do nothing).

The directional `unpartition` is more lenient — it doesn't require the endpoints to still be attached, so a `detach()` followed by an `unpartition` is a clean no-op rather than an error.

### Whole-bridge

```lua
lan:partition_all()         -- every pair partitioned
lan:restore_all()           -- every partition lifted
```

### Inspect

```lua
if lan:is_partitioned(a, b) then
    -- A↔B is currently partitioned (symmetric or A→B directional)
end
```

## Impairments

Three knobs: latency, drop rate, bandwidth limit. Each accepts either a scalar (whole-bridge) or a directional table.

### Latency

```lua
lan:add_latency(50)                                -- 50 ms one-way to every flow
lan:add_latency({from = a, to = b, ms = 50})       -- 50 ms only on A→B
```

Implemented as netem qdiscs. For directional, the qdisc is on the `to`-side TAP's egress. Endpoint attachment check applies (same as directional partitions).

### Drop rate

```lua
lan:drop_rate(10)                                  -- ~10 % loss, both ways
lan:drop_rate({from = a, to = b, p = 10})          -- only on A→B
```

### Bandwidth limit

```lua
lan:bandwidth_limit(1024 * 1024)                       -- 1 Mbit/s, both ways
lan:bandwidth_limit({from = a, to = b, bps = 500000})  -- 500 kbit/s leaving A
```

The number is **bits per second**, not bytes — matches `tc rate Nbit`. The whole-bridge form installs a TBF qdisc on the bridge interface. The directional form installs an HTB qdisc on the source TAP, with a netem child if latency or drop is set on the same source.

The `to` argument is graph-recorded but the realization shapes **every packet leaving the source TAP** — HTB on a Linux bridge can't reliably select packets by destination MAC. If you set `(from=a, to=b, bps=X)` and `(from=a, to=c, bps=Y)`, the realized rate is `max(X, Y)` so no recorded pair is over-shaped.

Combine directional bandwidth with directional latency / drop on the same source for a complete profile:

```lua
lan:bandwidth_limit({from = a, to = b, bps = 1_000_000})
lan:add_latency({from = a, to = b, ms = 25})
lan:drop_rate({from = a, to = b, p = 1})
```

Whole-bridge bandwidth + whole-bridge latency on the same bridge still falls back to bandwidth-only (a known v1 limitation noted in code) — for combined shaping use the directional form on each source.

### Reset

```lua
lan:reset()    -- tear down every netem/tbf qdisc, clear every partition
```

`reset` is a clean way to go back to "default" without enumerating every impairment you applied.

### Inspect

```lua
lan:latency_ms()        -- current whole-bridge latency
lan:drop_rate_pct()     -- current whole-bridge drop rate
lan:bandwidth_bps()     -- current whole-bridge bandwidth cap
```

These return the most recently applied whole-bridge value. They don't enumerate per-direction impairments.

## Isolation

Isolation puts one VM behind a hairpin filter — it can't reach any other VM on the bridge, but the bridge stays up:

```lua
lan:isolate(a)
local r = a:run("ping -c 1 -W 1 b.lan")
-- r:ok() is false; a is isolated

lan:unisolate(a)
a:run("ping -c 1 -W 1 b.lan"):assert_ok()
```

`lan:is_isolated(vm)` returns `true` if the VM is currently isolated.

## NICs

```lua
local nic = a:nic("lan")              -- by bridge name
local nic = a:nic("eth0")             -- by guest-name index
local nic = lan:nic(a)                -- equivalent
```

The Nic gives you per-NIC capabilities the bridge can't:

```lua
nic:counters()         -- {rx_bytes, tx_bytes, rx_packets, tx_packets, errors}
nic:disconnect()       -- link-down via QMP set_link(false)
nic:reconnect()        -- link-up
nic:capture()          -- pcap on this NIC's TAP
nic:vm_name()          -- "a"
nic:bridge()           -- "lan"
```

`counters` are presented from the **guest's perspective** — `rx_bytes` is bytes the guest received (host TAP's `tx_bytes`).

`disconnect` / `reconnect` drive QMP `set_link` so the guest sees a real link-down event. With a bare-string Nic (`bridge:nic("name")` — no VM userdata), the QMP step is skipped and the call is graph-state only.

## Packet capture

Two scopes:

### Bridge-wide capture

```lua
local cap = lan:capture()
vm:run("ping -c 5 b.lan")
local frames = cap:drain("2s")
local pcap = table.concat(frames)
-- pcap is now standard pcap-format bytes, parseable by tshark, etc.
```

`bridge:capture()` spawns `tcpdump -i <bridge> -U -w -` and returns a [Capture](~provium/reference/streams) stream. Reads pcap bytes off tcpdump's stdout.

Requires `tcpdump` on `PATH` and `CAP_NET_RAW`. The capture pins the bridge's `active_captures` counter so a `vm:snapshot()` while the capture is live errors instead of silently producing a half-captured pcap.

### Per-NIC capture

```lua
local nic = a:nic("lan")
local cap = nic:capture()    -- captures only A's TAP, not the whole bridge
```

Useful when multiple VMs are on the bridge and you only want one VM's perspective.

`nic:capture()` errors if the VM hasn't been booted yet (the per-VM TAP doesn't exist):

```
nic:capture: vm `a` has no TAP on bridge `lan` (not booted?). Call lab:boot() / vm:boot() first.
```

## Uplink (NAT to the outside world)

```lua
lan:enable_uplink()
vm:run("curl -s https://example.com/"):assert_ok()
lan:disable_uplink()
```

`enable_uplink` installs an nft NAT masquerade rule between the bridge and the host's default-route interface. Failures (e.g. no default-route interface) error with the underlying detail.

## L3 routing (preview)

```lua
lan:route(other_bridge)
-- prints once: "bridge:route on `lan` is graph-state only in v1
-- (no nft forward rules installed). Cross-bridge IP traffic will
-- not actually flow until the L3 routing slice lands."
```

`bridge:route` records the routing intent in the graph but installs no nft forward rules in v1. `bridge:routes()` returns the recorded routes. Plan tests around the limitation.

## Common patterns

### Test split-brain recovery

```lua
test("application recovers after partition heals", function(t)
    local lan = provium:bridge("lan")
    local a, b = provium:vm("a", "peios"):boot(), provium:vm("b", "peios"):boot()
    lan:attach({a, b})

    -- Baseline: a can talk to b.
    a:run("ping -c 1 -W 1 b.lan"):assert_ok()

    -- Partition.
    lan:partition(a, b)
    local r = a:run("ping -c 1 -W 1 b.lan")
    t:assert(not r:ok())

    -- Heal.
    lan:unpartition(a, b)
    -- Wait for ARP / route to re-converge.
    wait_until(function()
        return a:run("ping -c 1 -W 1 b.lan"):ok()
    end, {timeout = "10s", desc = "post-heal connectivity"})
end)
```

### Test latency-sensitive code

```lua
test("client retries on slow link", function(t)
    local lan = provium:bridge("lan")
    -- … attach VMs …
    lan:add_latency(500)  -- 500 ms each way ≈ 1s RTT
    local r = vm:run("curl --max-time 0.5 http://server.lan/")
    t:assert(not r:ok())  -- timeout fires

    lan:reset()
    r = vm:run("curl --max-time 0.5 http://server.lan/")
    r:assert_ok()
end)
```

### Test packet loss tolerance

```lua
test("client succeeds with 30% drop", function(t)
    lan:drop_rate(30)
    -- Apps should retry; some will succeed.
    local successes = 0
    for _ = 1, 20 do
        if vm:run("curl --max-time 5 http://server.lan/"):ok() then
            successes = successes + 1
        end
    end
    t:assert(successes >= 5)  -- pessimistic floor
end)
```

### Inspect packet flow with capture

```lua
test("DNS query produces UDP traffic", function(t)
    local cap = lan:capture()
    vm:run("dig @8.8.8.8 example.com")
    local pcap = table.concat(cap:drain("3s"))
    cap:close()
    -- Pipe pcap through tshark or pyshark to assert UDP/53.
end)
```

## See also

- [Bridge reference](~provium/reference/bridge) — every method on the Bridge userdata.
- [Nic reference](~provium/reference/nic) — per-NIC handle.
- [Streams reference](~provium/reference/streams) — what `bridge:capture()` and `nic:capture()` return.
