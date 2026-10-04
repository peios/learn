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
set of both forests and materializes exactly that — one **table** per
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
current value of each window. [*ntfe-store.counters-ioctl-dumps-every-cell] It is a best-effort snapshot (the RCU read
lock is dropped around each `copy_to_user()`), which is fine for
counters that are approximate by design. [*ntfe-store.counters-dump-is-best-effort]

## Reports

`REPORT(level)` past `CurrentReportingLevel` becomes one KMES event:
origin class `KMES_ORIGIN_NTFE` (4), event type `network-report`, [*ntfe-store.report-becomes-one-kmes-event] and a
msgpack payload — a string-keyed map of the attribution (`rule`), the
`level`, where the judgment stood (`layer`, `seat`), what it said
(`verdict`, and `reject_kind` when it was a reject), the packet
(`direction`, `interface`, `ifindex`, `ether_type`, `family`,
`protocol`, `src`, `dst`, `src_port`, `dst_port`, `flow_state`,
`length`), the `generation`, and `t_ns`. [*ntfe-store.report-payload-keys] Only keys the packet has are
present. [*ntfe-store.report-omits-absent-packet-keys]

The payload is built on the stack (512 bytes, map16 header patched with
the final count; [*ntfe-store.report-payload-built-on-stack] a hypothetical overflow drops the event rather than
emit a lie) [*ntfe-store.report-overflow-drops-event] because the packet path runs in softirq and
`pkm_kmes_emit_kernel()` is a preempt-disabled per-CPU ring write with
no allocation of its own. Flood control is the author's by design — the
level gate — with KMES's own ring accounting as the backstop.
`reports_emitted` counts what reached the ring. [*ntfe-store.reports-emitted-counts-ring-arrivals]
