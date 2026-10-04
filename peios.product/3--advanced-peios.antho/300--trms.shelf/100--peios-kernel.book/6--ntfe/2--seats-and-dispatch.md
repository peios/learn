---
title: Seats and dispatch
description: The netfilter hooks NTFE stands at, the dispatch law that gives every traversal exactly one proper seat per layer, and how verdicts — refusals included — are applied where they land.
---

## The seats

NTFE registers at four kinds of netfilter hook.

- **Device ingress** (`NF_NETDEV_INGRESS`) and **device egress**
  (`NF_NETDEV_EGRESS`), per interface. A netdevice notifier registers
  both on every `NETDEV_REGISTER` in `init_net` and unregisters them on
  `NETDEV_UNREGISTER`; [*ntfe-seat.device-seats-follow-netdev-notifier] because `register_netdevice_notifier()` replays
  `NETDEV_REGISTER` for devices that already exist, boot-time interfaces
  get their seats too. [*ntfe-seat.boot-time-interfaces-get-seats] These seats see frames — the Ethernet header is
  present, VLAN tags are visible, and on the inbound side conntrack has
  not yet run. [*ntfe-seat.device-seats-see-frames]
- **IP inbound** (`NF_INET_LOCAL_IN`, IPv4 and IPv6) at priority
  `NF_IP_PRI_FILTER`. Conntrack and defragmentation have run; the packet
  is whole and its flow is classified — and still unconfirmed, since
  conntrack confirms at the end of this hook. [*ntfe-seat.ip-inbound-at-local-in-filter-priority]
- **IP outbound** (`NF_INET_LOCAL_OUT`, IPv4 and IPv6) at filter
  priority. The first point after conntrack has classified a locally
  generated packet's flow; the sending socket is attached; the entry is
  unconfirmed until `POST_ROUTING`. [*ntfe-seat.ip-outbound-at-local-out-filter-priority]

Only `init_net` is instrumented: Peios has no container or network
namespace story yet, and the notifier ignores devices in other
namespaces. [*ntfe-seat.only-init-net-instrumented] Of netfilter's other hooks, `FORWARD` is empty on a host that
does not forward, and `PRE_ROUTING` and `POST_ROUTING` see nothing the IP
seats do not, save NAT.

## The dispatch law

The ratified law, with the Flow layer's clause:

> RawPacket matches all traffic at the device seats, unconditionally. [*ntfe-seat.rawpacket-at-device-seats-unconditionally]
> The Packet layer judges every traversal exactly once, at its proper
> seat — inbound IP at the IP hook, everything outbound at egress — [*ntfe-seat.packet-judged-exactly-once-at-proper-seat]
> falling back to the ingress seat iff the traversal will never reach its
> proper seat. [*ntfe-seat.packet-falls-back-to-ingress-iff-unreachable] The Flow layer judges every tracked flow once per local
> endpoint, at the IP seats, [*ntfe-seat.flow-judged-once-per-local-endpoint] and its sentence answers for every later
> packet of the flow. [*ntfe-seat.sentence-answers-for-later-packets]

"Will never reach its proper seat" is decidable at ingress from two
facts, and `peios_ntfe_traversal_reaches_ip_seat()` decides it: the
ethertype (only `ETH_P_IP` and `ETH_P_IPV6` cross the IP hooks) and the
device's disposition (`netif_is_bridge_port()` — a frame on a
bridge-enslaved port is switched at L2 and never enters this device's IP
stack; a copy delivered to the bridge device itself is a separate
traversal on that device, judged there). [*ntfe-seat.reaches-ip-seat-from-ethertype-and-bridge-port]

So at each seat the hook builds one snapshot and judges an ordered list
of layers:

| Seat | Layers, in traversal order |
|---|---|
| Ingress, IP frame on a plain port | `RawPacket` only (the Packet layer is *deferred* to `LOCAL_IN`) [*ntfe-seat.ingress-ip-plain-port-rawpacket-only] |
| Ingress, non-IP frame or bridge port | `RawPacket`, then `Packet` (the *fallback* judgment) [*ntfe-seat.ingress-non-ip-or-bridge-port-rawpacket-then-packet] |
| `LOCAL_IN` | `Packet`, then the flow's sentence or `Flow` [*ntfe-seat.local-in-packet-then-flow] |
| `LOCAL_OUT` | the flow's sentence or `Flow` [*ntfe-seat.local-out-flow-only] |
| Egress | `Packet`, then `RawPacket` [*ntfe-seat.egress-packet-then-rawpacket] |

Traversal order is wire order: `RawPacket` is wire-proximate, so it is
first in and last out; `Flow` is innermost, last in and first out. [*ntfe-seat.traversal-order-is-wire-order] Each
per-packet layer is evaluated once per traversal, [*ntfe-seat.per-packet-layer-once-per-traversal] and the first non-`PASS`
verdict ends the traversal. [*ntfe-seat.first-non-pass-ends-traversal] A layer with no published forest is
*permissive* and counted as such — at generation 0 that is every layer. [*ntfe-seat.unpublished-layer-permissive-and-counted]

At the IP seats, a packet goes on to the flow dispatch (§6.8) — at
`LOCAL_IN` once the Packet layer has passed it, at `LOCAL_OUT` before
any Packet judgment, since the Packet layer judges outbound traffic at
egress, after it: an untracked packet has no flow to judge and is
accepted, so inbound the Packet verdict stands and outbound egress
judges it next; [*ntfe-seat.untracked-packet-keeps-packet-verdict] a tracked packet with a current sentence gets that
sentence, [*ntfe-seat.tracked-packet-gets-current-sentence] and one without is evaluated by the Flow forest and sentenced. [*ntfe-seat.unsentenced-flow-evaluated-and-sentenced]

## Applying a verdict

`PASS` continues to the next layer, then `NF_ACCEPT`. [*ntfe-seat.pass-continues-then-accept] `DROP` is
`NF_DROP`. [*ntfe-seat.drop-is-nf-drop] `REJECT` is `NF_DROP` plus a refusal, phrased by the kind the
rule chose and the packet's protocol: [*ntfe-seat.reject-is-drop-plus-refusal]

| Kind | IPv4 | IPv6 |
|---|---|---|
| `Refused` (default) | TCP: RST; else ICMP port-unreachable | TCP: RST; else ICMPv6 port-unreachable [*ntfe-seat.refused-kind-rst-or-port-unreachable] |
| `Prohibited` | ICMP `ICMP_PKT_FILTERED` (type 3, code 13) | ICMPv6 `ICMPV6_ADM_PROHIBITED` (type 1, code 1) [*ntfe-seat.prohibited-kind-admin-filtered] |

Every seat can refuse IP traffic — the ingress seat only on an Ethernet
device. [*ntfe-seat.every-seat-can-refuse-ip] `refuse.c` builds the answer with the
kernel's frame-less reject builders (`nf_reject_skb_v4_tcp_reset()`,
`nf_reject_skb_v4_unreach()` and the v6 pair — the ones nftables' netdev
reject uses), attaches the flow to it (`nf_ct_attach()`, so conntrack
files it as the reply it claims to be), marks it, and delivers it: [*ntfe-seat.refusal-attached-to-flow-and-marked]

- from the **ingress** seat, to the peer on the wire — `dev_hard_header()`
  with the offending frame's MACs swapped, then `dev_queue_xmit()`; [*ntfe-seat.ingress-refusal-sent-to-wire-peer]
  that needs an Ethernet device (`ARPHRD_ETHER`) and a link header to
  swap, so at the ingress seat of any other device — the loopback
  device, a tunnel — a `REJECT` always degrades (below); [*ntfe-seat.ingress-refusal-needs-ethernet]
- from **every other seat**, to ourselves — `skb_dst_set_noref()` from
  the offending packet's route, `ip_route_me_harder()` (or the v6
  helper), then `ip_local_out()`. [*ntfe-seat.non-ingress-refusal-routed-through-local-out] Inbound, that routes the answer out to
  the peer with our address as its source; [*ntfe-seat.inbound-refusal-routed-to-peer] outbound, the answer is the
  peer's, addressed to us, so the route lands on the loopback device and
  the stack's own RST and ICMP-error handlers fail the local socket at
  once, with the error the kernel maps the answer to: `ECONNREFUSED`
  for a reset or a port unreachable, `EHOSTUNREACH` for IPv4's
  admin-filtered, `EACCES` for IPv6's admin-prohibited. TCP takes an
  ICMP error that reaches a socket its owner is holding as a soft error,
  and a refused SYN is refused inside `connect()`, which holds it: so an
  ICMP answer to a held TCP socket is sent a tick later (one jiffy, on
  the system workqueue), once the call has let go. A reset needs no
  wait: TCP queues it on the socket's backlog. [*ntfe-seat.outbound-refusal-fails-local-socket-at-once] The loopback device retains
  the route the packet was sent with, so the foreign source address
  never meets source validation. [*ntfe-seat.outbound-refusal-skips-source-validation]

The builders read the offending packet from `skb->data` as though it
pointed at the network header, as it does at the IP hooks; at the
egress seat it points at the link header the device has pushed, so
`refuse.c` pulls the packet to its network header for the build and
pushes it back after. [*ntfe-seat.refusal-built-from-network-header]

When the refused packet belongs to an **established TCP** flow, the far
end is torn down too: `peios_ntfe_teardown_build()` turns the refused
packet itself into a reset — same addresses, ports, sequence and
acknowledgement numbers, `RST` set, no data — marks it, and sends it
where the packet was going by the same routed path (outbound, to the
peer on the wire; inbound, to our own socket over loopback). [*ntfe-seat.established-tcp-reject-tears-down-far-end] The refused
end gets the kind's story; the far end gets the only story TCP listens
to mid-connection. Counted in `teardowns_emitted`. [*ntfe-seat.teardowns-counted] New flows and UDP
have no far end; [*ntfe-seat.no-teardown-for-new-flow-or-udp] a reset is never answered with a reset; [*ntfe-seat.no-teardown-of-a-reset] the ingress
seat has no flow facts and never tears down. [*ntfe-seat.ingress-never-tears-down]

The answer is not sent, and the `REJECT` **degrades to `DROP`** (counted
in `reject_degraded`, flagged `REJECT_DEGRADED` in the event, the kind
still named), when there is nothing to send: a non-IP frame, a broadcast
or multicast destination, an ingress frame on a non-Ethernet device, a
builder that declines (a non-first fragment, which has no transport
header to answer from; a failed checksum; a refusal of a refusal), a
packet with no route to reason from, or an allocation failure. [*ntfe-seat.reject-degrades-to-drop-when-nothing-to-send] A
*first* fragment passes the builders' fragment check and is declined by
their checksum check instead — its transport checksum covers a payload
it carries only part of — so one whose checksum the builder does not
verify (one the stack has already marked as checked, or a protocol the builders
skip: UDP with a zero checksum, SCTP, ESP, AH, GRE, UDP-Lite) is
answered. Fragments meet the builders only at the device seats:
`LOCAL_IN` sees reassembled packets. [*ntfe-seat.first-fragment-declined-by-checksum] Refusals sent are counted in
`refusals_emitted`. [*ntfe-seat.refusals-sent-counted]

## The refusal law

**NTFE does not judge its own refusals.** The answer `refuse.c` builds
carries `skb->ntfe_refusal`, a bit the `ntfe-refusal-bit` patch adds to
`struct sk_buff` inside its `headers` group (so clones and copies keep
it); [*ntfe-seat.refusal-bit-survives-clone-and-copy] every hook checks it first and returns `NF_ACCEPT` without a
snapshot, an evaluation or an event, counting `refusals_bypassed`. [*ntfe-seat.refusals-bypass-every-hook]
Refusals are verdict machinery, not traffic: without the bit, an inbound
`REJECT`'s RST would cross the egress seat and could be dropped — and
attributed — by an outbound rule, and an outbound `REJECT`'s forged peer
answer would be judged as inbound traffic on its way to the socket.

## Failing closed

Evaluation can fail: the core allocates `GFP_ATOMIC` during a walk and
an allocation can be refused. The hook then drops the packet, counts
`fail_closed`, and emits an event attributed to `fail-closed` with the
`FAIL_CLOSED` flag. [*ntfe-seat.evaluation-failure-drops-counts-and-reports] Totality does not take "no answer" for an answer.

A snapshot that cannot be built — a frame too mangled to describe — is
counted (`parse_errors`) and judged on its seat facts alone; the
absent-fact law does the rest. [*ntfe-seat.unbuildable-snapshot-judged-on-seat-facts]
