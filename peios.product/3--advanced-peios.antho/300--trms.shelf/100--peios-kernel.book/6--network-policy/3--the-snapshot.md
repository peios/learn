---
title: The snapshot
description: How one traversal's facts are extracted from the sk_buff into the fixed-size seat snapshot, what the validity bits mean, and what crosses into the Rust core.
---

Every judgment reads a **snapshot**: a fixed-size, stack-allocated
`struct peios_pnp_snapshot` built once per seat by
`peios_pnp_snapshot_from_skb()` and never mutated during evaluation.
That immutability is a ratified law, not an implementation detail —
nothing a rule writes is visible to the same evaluation's matching, so
temporal feedback (the next packet sees it) is the only feedback there
is.

## Validity bits

Many facts have meaningful zero values (port 0, TTL 0, VLAN 0), so
presence is carried separately in `has`, a bitmask of `PEIOS_PNP_HAS_*`:
ethertype, MACs, VLAN, TTL, DSCP, fragment, ports, TCP flags, ICMP, and
time. Address facts use `addr_family` (0, 4 or 6) as their validity; the
protocol is valid iff a family is. Flow state uses its own `ABSENT`
value. The bridge turns each clear bit into `None` on the Rust side, and
the absent-fact law makes every condition over a `None` false.

## Extraction

Seat facts first: seat, direction, interface (`ifindex` and name), the
packet length as the stack sees it (`skb->len` — not the wire length),
and the wall clock (`ktime_get_real_seconds()` through `time64_to_tm()`,
UTC, with `tm_wday` re-based so the `DayOfWeek` fact is ISO: 1 = Monday
.. 7 = Sunday).

Then the frame: the ethertype from `skb->protocol`; the VLAN id if
`skb_vlan_tag_present()`; the MAC pair if the MAC header is set and the
device is `ARPHRD_ETHER`.

Then IP, from `skb_network_offset()`:

- **IPv4** — addresses, TTL, DSCP (`tos >> 2`), the fragment flag (`IP_MF`
  set or a non-zero fragment offset), the protocol, and the L4 facts
  from `ihl * 4` on.
- **IPv6** — addresses, hop limit, DSCP from the traffic class, and a
  bounded walk (eight hops) of the extension-header chain: hop-by-hop,
  routing and destination options are skipped by `(hdrlen + 1) * 8`; a
  fragment header sets the fragment fact, and a *non-first* fragment
  ends the walk with no L4 facts (there are none to read). The protocol
  fact is the header the walk stops at — so an MLD report behind a
  hop-by-hop header reads `Protocol = icmpv6`, as a rule would expect.

Then L4, by protocol: ports for TCP, UDP and SCTP; the flag byte for TCP
(`TcpFlags` is `FIN..CWR` as the eight low bits of the 13th byte, the
same encoding `tcp_flag_byte()` uses); type and code for ICMP and
ICMPv6. Every header read goes through `skb_header_pointer()`, so a
packet whose headers are paged or truncated yields absent facts rather
than a fault.

## Flow state and the flow

At the ingress seat conntrack has not run and the flow state is
`ABSENT`; at `LOCAL_IN` and egress, `nf_ct_get()` gives the entry and
`ctinfo` maps to the fact: `IP_CT_ESTABLISHED` and its reply →
`established`; `IP_CT_RELATED` and reply → `related`; `IP_CT_NEW` →
`new`; anything else, or no entry at all, → `untracked`. The `invalid`
value is reserved: distinguishing an incoherent packet needs conntrack's
own verdict, which this seat does not receive.

The snapshot also carries `flow`: the `struct nf_conn *` itself (never a
template), or NULL. This is the tag store's scope — `TAG` writes land on
that entry's extension, and tag reads come from it. It is the one
pointer in the snapshot that outlives the extraction, and it is valid
because the skb holds a reference to the entry for the duration of the
hook.

## What the core sees

`PnpSnapshotC` in `kacs/pnp_runtime.rs` mirrors the C struct field for
field (`#[repr(C)]`; keep them in lockstep). `snapshot_from_c()` lifts
it into the core's `Snapshot` — an `Option` per fact — and the bridge
then fills in the two machinery fact tables: `tags`, as `(name hash,
value)` pairs for every tag name the forest can read that the flow
carries, and `counter_views`, as `(view index, value)` for every view the
forest reads that the store can answer for this packet. Both are
resolved *before* evaluation, against the forest being evaluated, which
is why the forest carries its name sets (§6.5).

Two visibility laws are enforced here rather than in the core: a
`RawPacket` forest is given no tags whatever the flow says (tags flow
upward only, and RawPacket is the lowest layer), and an ingress snapshot
has no flow, so no tags exist to give.
