---
title: The stores
description: The three machinery stores behind NTFE's effects — flow tags on a conntrack extension, counter tables materialized from the forest's views, and REPORT emission into KMES — with their bounds and confessions.
---

Effects need somewhere to land. Three stores, each with a small C
surface the bridge calls during evaluation, each confessing what it
refuses into the engine status.

## Identities

Tag and stream names cross into the stores as 64-bit **FNV-1a hashes**
(`pnp_core::hash::name_hash`). [*ntfe-store.names-cross-as-fnv1a-hashes] The stores never see a string on the
packet path, and never a generation: a flow's tag table holds `(hash,
value)` pairs, a counter table is keyed by its stream's hash. [*ntfe-store.stores-hold-no-strings-or-generations] Two
consequences: tags survive policy reloads by construction (the table
knows nothing to invalidate), [*ntfe-store.tags-survive-policy-reload] and a hash must be a deterministic
identity, not a probabilistic one — which ingestion guarantees by
refusing any generation whose distinct names collide (§6.5). [*ntfe-store.colliding-names-refuse-generation] Within a
running policy a collision is impossible; across generations the
residual is a 64-bit birthday bound over a handful of names, documented
and not defended.

## Flow tags

A tag is a named unsigned integer on a conntrack entry. The store is the
`tags` pointer of NTFE's **conntrack extension** — `NF_CT_EXT_NTFE`,
`struct peios_ntfe_ct` (`include/linux/peios_ntfe.h`), added to every flow
at creation (`init_conntrack()`, by the `ntfe-conntrack-ext.patch`), [*ntfe-store.ct-extension-added-at-flow-creation] with
the pointer NULL until the flow's first `TAG`. [*ntfe-store.tag-table-null-until-first-tag] The extension *block* of
a confirmed conntrack entry is immutable (upstream removed post-confirm
resizing as an RCU-reader race), and NTFE's egress seat runs after
confirmation, so the extension must exist before it is needed; a fixed
extension on every flow is the cheapest way to guarantee that. Since the
Flow slice the extension also holds the flow's start time and its two
sentences (§6.8) — 88 bytes per flow, most of it the sentences — [*ntfe-store.ct-extension-holds-start-and-sentences] while
untagged flows, nearly all of them, still pay nothing for a table.

The first `TAG` allocates (`GFP_ATOMIC`) a table of eight `(hash, value,
present)` entries; [*ntfe-store.first-tag-allocates-eight-entries] a full table is replaced by one twice the size —
copy, `rcu_assign_pointer()`, `kfree_rcu()` the old — [*ntfe-store.full-tag-table-doubles] up to the tripwire
of 64 distinct tags per flow. [*ntfe-store.tag-tripwire-64-per-flow] Readers walk the table under RCU with no
lock (the hook path already holds the read lock); [*ntfe-store.tag-readers-lockless-under-rcu] writers serialize on
the flow's own `ct->lock`. [*ntfe-store.tag-writers-serialize-on-ct-lock] `Clear` tombstones an entry (`present = 0`)
rather than compacting, so a concurrent reader never sees the table
shift under it, [*ntfe-store.clear-tombstones-without-compacting] and a later `Set` reuses the slot. [*ntfe-store.set-reuses-tombstoned-slot] `Add` saturates at
`U64_MAX`. [*ntfe-store.tag-add-saturates] The entry's identity is published before the length that
exposes it (`smp_wmb()` then `WRITE_ONCE(len)`), so a reader that sees
the new length sees a complete entry. [*ntfe-store.tag-entry-published-before-length]

When the flow dies, `nf_conntrack_free()` calls `peios_ntfe_ct_destroy()`
(the same patch), which `kfree_rcu()`s the table — a reader that found
the entry under RCU may still be walking it. [*ntfe-store.tag-table-freed-after-grace-on-flow-death]

Confessions: `tag_writes` (ops applied), [*ntfe-store.tag-writes-counts-applied-ops] `tag_untracked` (a `TAG` on a
packet with no flow — untracked traffic, or the ingress seat — is a
no-op), [*ntfe-store.tag-without-flow-is-untracked-no-op] `tag_refused` (the tripwire, an allocation failure, or a flow
whose extension could not be allocated at creation). [*ntfe-store.tag-refused-confessions] Clearing an absent
tag is a no-op, not a refusal. [*ntfe-store.clearing-absent-tag-is-no-op]

## Counters

`COUNT(Name[, amount])` emits into a **stream**; every
`Counter.Name([window][, key])` a rule reads is a **view**. Nothing is
declared: views are compile-time constants (rules are their only
source), so at publication (§6.5) the store receives the complete view
set of all three forests — `Packet`, `RawPacket` and `Flow` — and materializes exactly that — one **table** per
distinct `(stream hash, key-spec)`, each answering every window any
view of that pair asks for, plus the cumulative total. [*ntfe-store.one-table-per-stream-and-key-spec] A `COUNT`
increments every table of its stream; [*ntfe-store.count-increments-every-table-of-stream] the amplification is bounded by
what policy authors wrote, the trusted side of the trust asymmetry.

A table is a 1024-bucket hash of **cells** (`jhash` over the cell key)
under a per-table spinlock (`_bh`, since the publisher runs in process
context). [*ntfe-store.table-is-1024-bucket-hash-under-bh-lock] A cell key is built from the packet by the table's key-spec:
address family, source and destination address (16 bytes each, v4 in
the first four), interface index — only the facts the spec names, the
rest zero. [*ntfe-store.cell-key-holds-only-named-facts] A packet lacking a keyed fact (an ARP frame for a
`SrcAddr`-keyed table) has no cell: its `COUNT` no-ops into that table
(`count_key_absent`) [*ntfe-store.count-without-key-fact-no-ops] and its view reads absent — the absent-fact law on
both sides. [*ntfe-store.view-without-key-fact-reads-absent]

A cell holds a cumulative `total`, the seconds of its last write, and
one **ring** per table window: eight buckets, each stamped with the
*period* it belongs to (`now / bucket_secs`, where `bucket_secs =
max(1, window / 8)`). [*ntfe-store.ring-is-eight-period-stamped-buckets] A write zeroes a bucket whose stamp is stale
before adding; [*ntfe-store.write-zeroes-stale-bucket] a read sums the buckets whose stamp is within the last
eight periods. [*ntfe-store.read-sums-last-eight-periods] Advancement is lazy — there are no timers — and the
window is an approximation up to one bucket wide, by design. [*ntfe-store.window-approximate-to-one-bucket]

The keyspace of a keyed table is chosen by whoever sends packets, so
tables are hard-capped at **4096 cells**. [*ntfe-store.table-capped-at-4096-cells] At the cap the store first
reaps cells idle for longer than the table's longest window (floor
60 s); [*ntfe-store.cap-reaps-idle-cells-first] if none are idle the new key is refused and confessed
(`count_refused`). [*ntfe-store.cap-refuses-new-key-when-none-idle] Never silent eviction.

The store outlives generations. [*ntfe-store.counter-store-outlives-generations] Re-publication keeps tables whose window
set did not change, [*ntfe-store.republish-keeps-unchanged-tables] creates new ones, [*ntfe-store.republish-creates-new-tables] **migrates** tables whose windows
changed (each cell is re-allocated in the new ring layout; the total and
any window both sets share carry over, new windows start empty and
converge), [*ntfe-store.republish-migrates-changed-tables] and retires tables no forest views any more — `list_del_rcu()`
then free after grace, cells included. [*ntfe-store.republish-retires-unviewed-tables] Reads on the packet path walk the
table list and the cell lists under RCU; [*ntfe-store.counter-reads-under-rcu] the publisher holds a mutex.

`PEIOS_NTFE_IOC_COUNTERS` dumps every cell of every table for the viewer:
stream name, key-spec, the key, the total, the last-write time, and the
current value of each window. [*ntfe-store.counters-ioctl-dumps-every-cell] It is a best-effort snapshot, which is fine
for counters that are approximate by design: the cells are gathered
into a kernel batch under one RCU read section and copied out after
it, and a store with more cells than a batch holds (4096) takes
further passes, each resuming after the cells already written, so a
cell created or retired between passes may be missed or seen twice. [*ntfe-store.counters-dump-is-best-effort]

## Reports

`REPORT(level)` at or above `CurrentReportingLevel` becomes one KMES event:
origin class `KMES_ORIGIN_NTFE` (4), event type `ntfe.verdict.reported`, [*ntfe-store.report-becomes-one-kmes-event] and a
msgpack payload laid out as the event catalogue's `ntfe` fragment
says: nested string-keyed maps, one per path segment. `rule` carries
the attribution (`name`, the path, and `hash`, the FNV-1a-64 of the
whole path), the `report-level`, and where the judgment stood
(`layer`: `raw-packet`, `packet` or `flow`; `seat`). `outcome` carries
what it said (`verdict`: `pass`, `reject` or `drop`; and `reason`,
`prohibited` or `refused`, when it was a reject). The packet is
`network` (`direction`, `interface` with its `name` and `index`,
`ether-type`, `family` as the `AF_*` number, `protocol`, `length`),
`source` and `destination` (each an `address` as text and a `port`),
and `flow` (`state`). `policy` carries the `generation`. The time is
the KMES header's; the payload does not repeat it. [*ntfe-store.report-payload-keys] A packet key whose fact can be
absent is present only when the packet has it: `network.protocol`,
`source` and `destination` when it has an address family, their ports
when it has ports, `flow` when the flow-state fact is present.
`network.direction`, `network.interface.index`, `network.ether-type`,
`network.family` and `network.length` are always emitted — an
interface index of 0 and a family of `AF_UNSPEC` (0) are the catalogue's
own values for none. `network.interface.name` is left out when no
device was there to name; no key is ever written as an empty string. [*ntfe-store.report-omits-absent-packet-keys]

The payload is built on the stack (512 bytes) [*ntfe-store.report-payload-built-on-stack] because the packet path runs in softirq and
`pkm_kmes_emit_kernel()` is a preempt-disabled per-CPU ring write with
no allocation of its own. Every map's size is known before it is
written, save `rule`'s, whose one-byte header is settled once the
name's fate is. Every value but `rule.name` is bounded, so `rule` goes
in last and `name` last within it: a path too long for the room left
is cut at a character boundary to fit, and `rule.name-truncated`
(`true`, absent when the name is whole) says so. The event is always
emitted, and `rule.hash` still names the whole path, so a reader
resolves the rule against the policy. [*ntfe-store.report-long-rule-cut-and-said] Flood control is the author's by design — the
level gate — with KMES's own ring accounting as the backstop.
`reports_emitted` counts what reached the ring. [*ntfe-store.reports-emitted-counts-ring-arrivals]
