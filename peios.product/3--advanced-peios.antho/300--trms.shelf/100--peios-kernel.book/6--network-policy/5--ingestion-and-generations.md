---
title: Ingestion and generations
description: How the kernel walks Machine\System\Network into a validated forest and a network context table, what refuses a generation, what is republished and what is not, and how a generation is published under RCU and retired.
---

The kernel reads its own policy. There is no daemon that compiles rules
and pushes them down; `ingest.c` walks the registry through the LCS
source interface, feeds what it finds to the `pnp-core` builder over the
bridge, and publishes the result as a generation — or keeps the previous
one, loudly. The same walk reads netd's inventory beside the rules into
the network context table (§6.3), because to a flow the two change
together: a network being recognised on an interface is as much a
policy change as a rule being written.

## Discovery and change notification

At LCS bootstrap, PNP's key is discovered fifth alongside the other
kernel-owned subtrees: `pkm_lcs_walk_absolute_components()` resolves
`Machine\System\Network` (the leading `Machine` hive component is
resolved locally against the hive root, not round-tripped), and its
absence is not an error — no key, no policy and no context, generation
stays where it is. When the key exists one internal watch is armed on
it, depth-unbounded, for every mutation: `Rules\`, `Interfaces\` and
`Networks\` beneath it are what PNP reads; `Profiles\` and `Dns\` are
netd's and resolvd's, and a write there fires the watch and costs a
walk that publishes nothing.

Watch events arrive per key and uncoalesced.
`peios_pnp_network_registry_changed()` records the source and key, sets
a pending flag, and `mod_delayed_work()`s a re-walk with a 50 ms
debounce: a burst of writes (a transaction touching a rule and its
values, an autoapply seeding a whole policy, netd syncing every
interface's `Status` after a link event) yields one re-walk after the
burst goes quiet. The walk itself runs in process context on
`system_wq`, one at a time under a mutex, since the bootstrap refresh
and the deferred work may overlap.

## The walk

`peios_pnp_network_refresh_from_key()` snapshots the LCS runtime limits,
sequence and layer view, enumerates the Network key's children for
`Rules`, `Interfaces` and `Networks`, and runs two independent stages —
the rules, then the context; a failure in the first does not skip the
second, and the walk reports the first error. No `Rules` key leaves the
previous generation standing, exactly as a walk that refused would.

The rules stage:

1. reads the Rules key's own values for `CurrentReportingLevel`
   (`REG_DWORD`, `REG_DWORD_BIG_ENDIAN` or `REG_QWORD`; 1..6; absent =
   1; anything else refuses);
2. enumerates its children for the layer keys `Packet`, `RawPacket` and
   `Flow` (`Interface` is netd's — the interface layer is built and judged
   in userspace with the same `pnp-core`, and the kernel never reads it;
   any other name is ignored);
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

Everything the stage feeds the builder — layer, rule name and depth,
value name, type and bytes, and the reporting level — also goes through
an FNV-1a digest. When the digest equals the one of the last walk that
published and a policy is in force, the forests are discarded unbuilt
into a generation: the active one already *is* this policy, and
republishing would only make every sentence stale for nothing. A walk
fired by an inventory write, or by the second of the two watch
deliveries a transaction produces, therefore changes no generation.

### The context stage

The inventory is read into one `struct peios_pnp_context_table`, at
most 64 entries of interface name, network id, name and trust:

1. every child of `Networks\` is a record; its key name is the id (a
   UUID — a longer name is ignored, once loudly), and one
   `RSI_QUERY_VALUES` round trip reads its `Name` and `Trust`
   (`REG_SZ`; absent or unreadable is empty, and the id is still a
   fact), up to 256 records;
2. every child of `Interfaces\` is an interface; its `Status` subkey is
   found by one `RSI_ENUM_CHILDREN` and read by one `RSI_QUERY_VALUES`
   for `Name` (the kernel interface name) and `Network` (the id netd
   identified on it). Both present make an entry, joined to the record
   of that id for its name and trust; either absent — no link, no
   offer yet, an `IGNORE`d or `DOWN` interface — makes none.

Nothing in the stage refuses. A record that cannot be read is logged
and skipped, an interface beyond the 64th carries no context, a value
longer than its field is truncated with one warning. The table then
goes to `peios_pnp_context_publish()` (§6.3): if it equals the active
one entry for entry it is freed and nothing happens; otherwise it is
`rcu_assign_pointer()`ed into place, the generation counter advances,
the old table is freed after grace, and the kernel log says how many
interfaces carry a context. The generation advance is the whole
mechanism by which a context change reaches running flows: every
sentence is now stale and is re-judged on its flow's next packet
(§6.8), the same path a rule change takes.

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
the kernel log. The status does not yet count the interfaces carrying a
context; that field waits on the next ABI revision, and the kernel log
line at each context publication is the record meanwhile.

## Generation 0

Until the first successful ingestion there is no policy at all, and
every layer is permissive: `judged` stays 0, `permissive` counts
traversals, no events are emitted (there is no decision to attribute),
and the status reports `enforcing = 0`. The init log line says it
plainly. This is the ratified loud default — the alternative, a
compiled-in policy the registry cannot see, was rejected.

A new generation does not touch the flows: every sentence written under
the old one is stale by generation and is re-judged on its flow's next
packet (§6.8). That is how a policy change — and a context change,
which advances the same counter — reaches running connections without
a walk of the conntrack table.
