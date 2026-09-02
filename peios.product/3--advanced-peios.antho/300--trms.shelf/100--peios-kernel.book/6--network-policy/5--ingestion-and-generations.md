---
title: Ingestion and generations
description: How the kernel walks Machine\System\Network\Rules into a validated forest, what refuses a generation, and how a generation is published under RCU and retired.
---

The kernel reads its own policy. There is no daemon that compiles rules
and pushes them down; `ingest.c` walks the registry through the LCS
source interface, feeds what it finds to the `pnp-core` builder over the
bridge, and publishes the result as a generation — or keeps the previous
one, loudly.

## Discovery and change notification

At LCS bootstrap, PNP's rules root is discovered fifth alongside the
other kernel-owned subtrees: `pkm_lcs_walk_absolute_components()`
resolves `Machine\System\Network\Rules` (the leading `Machine` hive
component is resolved locally against the hive root, not round-tripped),
and its absence is not an error — no key, no policy, generation stays
where it is. When the key exists an internal watch is armed on it,
depth-unbounded, for every mutation.

Watch events arrive per key and uncoalesced. `peios_pnp_rules_registry_changed()`
records the source and key, sets a pending flag, and
`mod_delayed_work()`s a re-walk with a 50 ms debounce: a burst of writes
(a transaction touching a rule and its values, an autoapply seeding a
whole policy) yields one re-walk after the burst goes quiet. The walk
itself runs in process context on `system_wq`.

## The walk

`peios_pnp_rules_refresh_from_key()` snapshots the LCS runtime limits,
sequence and layer view, then:

1. reads the Rules key's own values for `CurrentReportingLevel`
   (`REG_DWORD`, `REG_DWORD_BIG_ENDIAN` or `REG_QWORD`; 1..6; absent =
   1; anything else refuses);
2. enumerates its children for the layer keys `Packet`, `RawPacket` and
   `Flow` (other names are ignored — someone else's future);
3. for each present layer, opens a builder and walks the layer key's
   subkeys as rule roots. Each rule is one `RSI_QUERY_VALUES` round trip
   (its effective, layering-resolved values, delivered in the batch
   record format `u32 name_len | name | u32 type | u32 data_len | data`)
   followed by one `RSI_ENUM_CHILDREN` round trip for its exceptions,
   recursively, bounded by depth 12 and 4096 rules per layer.

Registry types are lowered as the builder ABI expects: `REG_SZ` and
`REG_EXPAND_SZ` to strings (NUL termination stripped), `REG_DWORD` and
`REG_DWORD_BIG_ENDIAN` to integers, `REG_QWORD` to a signed 64-bit
integer, `REG_MULTI_SZ` to a list of strings. Any other type in a rule
refuses the walk: atomic transitions prefer a loud rejection over a
silently half-read rule.

## Building and validating

The builder (`pnp_rust_builder_*`) accumulates `RuleInput` trees; `build`
runs `pnp_core::ingest::build_forest`, which parses every condition key
and action expression, orders each rule's conditions with the live-time
ones last (§6.4), resolves priority inheritance, lints layer-impossible
facts (a `FlowState` or tag condition in a `RawPacket` forest; a
per-packet fact — `Length`, `TcpFlags`, `Fragment`, `Ttl`, `Dscp`,
`EtherType`, `DstMac`, `FlowState` — in a `Flow` forest; `Related` or
`Start.*` anywhere but `Flow` — all legal, never true; the kernel drops
lints, the authoring surface shows them), and collects the forest's
**name sets**: every tag name mentioned in a `TAG` action, a `PROMPT`
fallback, or a `Tag.<n>` condition, split into the names the forest
*writes* and the first rule reading each; every stream a `COUNT` writes;
every distinct counter view a `Counter.<n>(...)` condition reads, with
the first rule and value that mentioned it. Views are deduplicated and
conditions refer to them by index — that index is what the bridge uses
when it fills `counter_views` (§6.3).

Refusals, each carrying the offending rule's path (`BuildError`):
unknown fact, unsupported operator, unparsable pattern, a counter view
that does not parse (bad duration, unknown key fact, duplicate
arguments, a window over the one-day horizon), a non-list `Actions`, an
unparsable action, a `REJECT` kind that is not `Refused` or
`Prohibited`, a `Priority` that is not an integer, an `Enabled` that is
not 0 or 1, a rule name containing a path separator — and, over the
name sets, two distinct tag names (or stream names) whose 64-bit hashes
collide.

After all three layers build, `pnp_rust_forests_check()` runs the checks
that span forests, because the stores are machine-wide: tag and stream
hashes must be distinct across *every* forest; every counter view must
have a writer in *some* forest — a view over a stream no rule writes is
statically dead (it can only ever read absent) and is refused with the
rule and key that read it; and no forest may read a tag a *higher*
forest writes (`RawPacket` < `Packet` < `Flow`) — tags flow strictly
upward, and since rules are the only source of tag names the downward
read is refused statically, with the reading rule and the name.

## Publication

`peios_pnp_policy_publish(packet, raw, flow, reporting_level)` is
process context under a mutex. It runs the cross-forest check, then
materializes the counter store for the union of every forest's views
(§6.6) — so a store that cannot be built (allocation, more than eight
windows on one table) refuses the generation before anything is
swapped. Only then does it advance the generation counter, allocate the
new `struct peios_pnp_policy` (three opaque forest pointers plus the
reporting level) and `rcu_assign_pointer()` it into place. Hook-path
readers dereference it under `rcu_read_lock()` and never block; they see
the old generation or the new one, never a mix. The old policy is
released by `call_rcu()`, and its forests by `pnp_rust_forest_free()` in
the callback after grace.

Every walk records its outcome: `last_ingest_error` (0, or the positive
errno of the last failed walk) and `last_ingest_t_ns`, both in the
status. A refusal leaves the previous generation active and says so in
the kernel log.

## Generation 0

Until the first successful ingestion there is no policy at all, and
every layer is permissive: `judged` stays 0, `permissive` counts
traversals, no events are emitted (there is no decision to attribute),
and the status reports `enforcing = 0`. The init log line says it
plainly. This is the ratified loud default — the alternative, a
compiled-in policy the registry cannot see, was rejected.

A new generation does not touch the flows: every sentence written under
the old one is stale by generation and is re-judged on its flow's next
packet (§6.8). That is how a policy change reaches running connections
without a walk of the conntrack table.
