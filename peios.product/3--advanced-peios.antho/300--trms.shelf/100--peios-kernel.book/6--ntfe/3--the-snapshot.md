---
title: The snapshot
description: How one traversal's facts are extracted from the sk_buff into the fixed-size seat snapshot, what the validity bits mean, and what crosses into the Rust core.
---

Every judgment reads a **snapshot**: a fixed-size, stack-allocated
`struct peios_ntfe_snapshot` built once per seat by
`peios_ntfe_snapshot_from_skb()` and never mutated during evaluation. [*ntfe-snapshot.built-once-per-seat-never-mutated]
That immutability is a ratified law, not an implementation detail —
nothing a rule writes is visible to the same evaluation's matching, so
temporal feedback (the next packet sees it) is the only feedback there
is. [*ntfe-snapshot.writes-invisible-to-same-evaluation]

## Validity bits

Many facts have meaningful zero values (port 0, TTL 0, VLAN 0), so
presence is carried separately in `has`, a bitmask of `PEIOS_NTFE_HAS_*`:
ethertype, MACs, source MAC alone, VLAN, TTL, DSCP, fragment, ports, TCP
flags, ICMP, time, the flow's start time, and the network context. [*ntfe-snapshot.has-bitmask-carries-presence] Address facts use
`addr_family` (0, 4 or 6) as their validity; [*ntfe-snapshot.addr-family-is-address-validity] the protocol is valid iff a
family is. [*ntfe-snapshot.protocol-valid-iff-family] Flow state uses its own `ABSENT` value; [*ntfe-snapshot.flow-state-has-own-absent-value] `flow_related` is
valid iff `flow` is. [*ntfe-snapshot.flow-related-valid-iff-flow] The bridge turns each clear bit into `None` on the
Rust side, [*ntfe-snapshot.clear-bit-lifts-to-none] and the absent-fact law makes every condition over a `None`
false. [*ntfe-snapshot.condition-over-none-is-false]

## Extraction

Seat facts first: seat, direction, interface (`ifindex` and name), the
network context of that interface (below), whether the device is the
loopback (`IFF_LOOPBACK` — the flow dispatch's "two endpoints" test), [*ntfe-snapshot.loopback-flag-from-iff-loopback]
the packet length as the stack sees it
(`skb->len` — not the wire length), [*ntfe-snapshot.length-is-skb-len] and the wall clock
(`ktime_get_real_seconds()` through `time64_to_tm()`, UTC, with
`tm_wday` re-based so the `DayOfWeek` fact is ISO: 1 = Monday .. 7 =
Sunday), [*ntfe-snapshot.clock-is-utc-with-iso-day-of-week] kept alongside as epoch seconds (`t_secs`) for the time-flip
arithmetic (§6.4) and the sentence expiry check (§6.8). [*ntfe-snapshot.clock-kept-as-epoch-seconds]

Then the frame: the ethertype from `skb->protocol`. [*ntfe-snapshot.ethertype-from-skb-protocol] The VLAN id is the
frame's tag if `skb_vlan_tag_present()`, else the device's if
`is_vlan_dev()` — the VLAN is a fact of the frame at the device seats
and of the device at the IP seats, where inbound the VLAN code has
already stripped the tag and re-parented the packet onto the VLAN
device, and outbound the tag is pushed only when that device transmits. [*ntfe-snapshot.vlan-from-frame-tag-else-device]
(Before the Flow slice the IP seats read the stripped tag and `Vlan` was
absent on VLAN interfaces there.) The MAC pair if the MAC header is set
and the device is `ARPHRD_ETHER`; [*ntfe-snapshot.mac-pair-on-ethernet-with-mac-header] failing that, at an IP seat on an
Ethernet device — a locally generated packet with no link header yet —
the source alone, from the device's own address (`HAS_SRC_MAC`): present
so every flow carries the same fact set, and not useful. [*ntfe-snapshot.headerless-ip-seat-gets-device-source-mac] The destination
is unknown until neighbour resolution, after the seat: absent. [*ntfe-snapshot.headerless-ip-seat-dst-mac-absent]

Then IP, from `skb_network_offset()`:

- **IPv4** — addresses, TTL, DSCP (`tos >> 2`), the fragment flag (`IP_MF`
  set or a non-zero fragment offset), the protocol, and the L4 facts
  from `ihl * 4` on. [*ntfe-snapshot.ipv4-facts]
- **IPv6** — addresses, hop limit, DSCP from the traffic class, and a
  bounded walk (eight hops) of the extension-header chain: hop-by-hop,
  routing and destination options are skipped by `(hdrlen + 1) * 8`; [*ntfe-snapshot.ipv6-extension-walk-bounded-eight-hops] a
  fragment header sets the fragment fact, [*ntfe-snapshot.ipv6-fragment-header-sets-fragment] and a *non-first* fragment
  ends the walk with no L4 facts (there are none to read). [*ntfe-snapshot.ipv6-non-first-fragment-has-no-l4] The protocol
  fact is the header the walk stops at — so an MLD report behind a
  hop-by-hop header reads `Protocol = icmpv6`, as a rule would expect. [*ntfe-snapshot.ipv6-protocol-is-walk-terminus]

Then L4, by protocol: ports for TCP, UDP and SCTP; [*ntfe-snapshot.ports-for-tcp-udp-sctp] the flag byte for TCP
(`TcpFlags` is `FIN..CWR` as the eight low bits of the 13th byte, the
same encoding `tcp_flag_byte()` uses); [*ntfe-snapshot.tcp-flags-encoding] type and code for ICMP and
ICMPv6. [*ntfe-snapshot.icmp-type-and-code] Every header read goes through `skb_header_pointer()`, so a
packet whose headers are paged or truncated yields absent facts rather
than a fault. [*ntfe-snapshot.truncated-headers-yield-absent-facts]

## Flow state and the flow

At the ingress seat conntrack has not run and the flow state is
`ABSENT`; [*ntfe-snapshot.ingress-flow-state-absent] at `LOCAL_IN`, `LOCAL_OUT` and egress, `nf_ct_get()` gives the
entry and `ctinfo` maps to the fact: `IP_CT_ESTABLISHED` and its reply →
`established`; `IP_CT_RELATED` and reply → `related`; `IP_CT_NEW` →
`new`; anything else, or no entry at all, → `untracked`. [*ntfe-snapshot.ctinfo-maps-to-flow-state] The `invalid`
value is reserved: distinguishing an incoherent packet needs conntrack's
own verdict, which this seat does not receive. [*ntfe-snapshot.invalid-flow-state-reserved]

The snapshot also carries `flow`: the `struct nf_conn *` itself (never a
template), or NULL. [*ntfe-snapshot.flow-is-conn-never-template] This is the tag store's and the sentence's scope —
`TAG` writes land on that entry's extension, tag reads come from it, and
the Flow layer's verdict is cached there. [*ntfe-snapshot.flow-scopes-tags-and-sentence] It is the one pointer in the
snapshot that outlives the extraction, and it is valid because the skb
holds a reference to the entry for the duration of the hook. [*ntfe-snapshot.flow-pointer-valid-for-hook]

With the flow come two facts that exist only on a flow: `flow_related`
(`ct->master != NULL` — the flow was expected by another) [*ntfe-snapshot.flow-related-is-ct-master-set] and the
flow's start time, read from the extension's `start_secs` (stamped when
conntrack created the entry) through the same `time64_to_tm()` lowering
as the clock, into the `s_*` fields (`HAS_START`). [*ntfe-snapshot.flow-start-from-extension-start-secs] These are the Flow
layer's `Related` and `Start.*` facts. `flow_reply` says whether this
packet travels in the flow's reply direction — the Flow layer's view
builder (§6.8) uses it to turn the packet's tuple back into the flow's. [*ntfe-snapshot.flow-reply-marks-reply-direction]

## What the core sees

`NtfeSnapshotC` in `kacs/ntfe_runtime.rs` mirrors the C struct field for
field (`#[repr(C)]`; keep them in lockstep). [*ntfe-snapshot.rust-mirror-matches-c-struct] `snapshot_from_c()` lifts
it into the core's `Snapshot` — an `Option` per fact — and the bridge
then fills in the two machinery fact tables: `tags`, as `(name hash,
value)` pairs for every tag name the forest can read that the flow
carries, and `counter_views`, as `(view index, value)` for every view the
forest reads that the store can answer for this packet. [*ntfe-snapshot.bridge-fills-tags-and-counter-views] Both are
resolved *before* evaluation, against the forest being evaluated, which
is why the forest carries its name sets (§6.5). [*ntfe-snapshot.machinery-facts-resolved-before-evaluation]

Three visibility laws are enforced here rather than in the core: a
`RawPacket` forest is given no tags whatever the flow says (tags flow
upward only, and RawPacket is the lowest layer; `Packet` and `Flow`
forests read them); [*ntfe-snapshot.rawpacket-forest-gets-no-tags] an ingress snapshot has no flow, so no tags exist to
give; [*ntfe-snapshot.ingress-snapshot-has-no-tags] and the flow-only facts (`Related`, `Start.*`, and the identity
facts) are given to a `Flow` forest alone — everywhere else they are
absent by law, exactly as ingestion's lint says (§6.5). [*ntfe-snapshot.flow-only-facts-for-flow-forest-alone] The clock is
given to every layer, and so is the trace of consulted time conditions
(§6.4); [*ntfe-snapshot.clock-and-time-trace-given-to-every-layer] only the Flow seat acts on it. [*ntfe-snapshot.only-flow-seat-acts-on-time-trace]

## The network context

Three string fields are not read from the packet either:
`network_id`, `network_name` and `network_trust`, the `Network.*` facts.
`peios_ntfe_context_fill()` (`context.c`) looks the device's name up in
the active context table — the kernel's reading of netd's inventory,
one entry per interface standing on an identified network, built by
ingestion (§6.5) and published under RCU — and copies the entry's three
strings in, setting `HAS_NETWORK`. [*ntfe-snapshot.context-filled-from-active-table] The bridge lifts the id whenever the
bit is set, [*ntfe-snapshot.network-id-lifted-when-bit-set] and the name and trust only when non-empty (a record the
operator has not labelled). [*ntfe-snapshot.empty-network-name-and-trust-absent] No entry, no bit: an interface no network
has been identified on carries no context, and every condition over the
three facts is false there. [*ntfe-snapshot.no-context-entry-no-network-facts] The strings are bounded (40, 64 and 32
bytes, `PEIOS_NTFE_NETWORK_*_LEN`); [*ntfe-snapshot.network-strings-bounded] a longer registry value is truncated
at ingestion and the truncation logged once. [*ntfe-snapshot.long-network-value-truncated-and-logged-once]

The fields are the same as the interface layer's (§6.1): netd fills
them from the interface record when it judges an interface, the kernel
from the table when it judges a packet, so `Network.Trust.Equal` reads
the same record in either layer. [*ntfe-snapshot.network-facts-match-interface-layer]

## The identity fields

The snapshot's last fields are not extracted from the packet at all.
The Flow layer's view builder (§6.8) sets them from the flow's
extension: for the local end, and on loopback for the other end, the
kind (`program`, `kernel`, `shared`, `none`), the process GUID, pid and
comm, and a *borrowed* pointer to the KACS token the socket was stamped
with — the extension holds the reference for the flow's life, so the
pointer is valid for the hook. [*ntfe-snapshot.identity-fields-set-from-flow-extension] The bridge lifts a program end into a
`Principal` the core's `Local.*` and `Remote.*` conditions question
(§6.9); [*ntfe-snapshot.program-end-lifts-to-principal] every other snapshot leaves the fields zero, which lifts to
absent. [*ntfe-snapshot.identity-fields-zero-elsewhere-lift-absent]
