---
title: Seats and dispatch
description: The netfilter hooks PNP stands at, the dispatch law that gives every traversal exactly one proper seat per layer, and how verdicts — refusals included — are applied where they land.
---

## The seats

PNP registers at four kinds of netfilter hook.

- **Device ingress** (`NF_NETDEV_INGRESS`) and **device egress**
  (`NF_NETDEV_EGRESS`), per interface. A netdevice notifier registers
  both on every `NETDEV_REGISTER` in `init_net` and unregisters them on
  `NETDEV_UNREGISTER`; because `register_netdevice_notifier()` replays
  `NETDEV_REGISTER` for devices that already exist, boot-time interfaces
  get their seats too. These seats see frames — the Ethernet header is
  present, VLAN tags are visible, and on the inbound side conntrack has
  not yet run.
- **IP inbound** (`NF_INET_LOCAL_IN`, IPv4 and IPv6) at priority
  `NF_IP_PRI_FILTER`. Conntrack and defragmentation have run; the packet
  is whole and its flow is classified — and still unconfirmed, since
  conntrack confirms at the end of this hook.
- **IP outbound** (`NF_INET_LOCAL_OUT`, IPv4 and IPv6) at filter
  priority. The first point after conntrack has classified a locally
  generated packet's flow; the sending socket is attached; the entry is
  unconfirmed until `POST_ROUTING`.

Only `init_net` is instrumented: Peios has no container or network
namespace story yet, and the notifier ignores devices in other
namespaces. Of netfilter's other hooks, `FORWARD` is empty on a host that
does not forward, and `PRE_ROUTING` and `POST_ROUTING` see nothing the IP
seats do not, save NAT.

## The dispatch law

The ratified law, with the Flow layer's clause:

> RawPacket matches all traffic at the device seats, unconditionally.
> The Packet layer judges every traversal exactly once, at its proper
> seat — inbound IP at the IP hook, everything outbound at egress —
> falling back to the ingress seat iff the traversal will never reach its
> proper seat. The Flow layer judges every tracked flow once per local
> endpoint, at the IP seats, and its sentence answers for every later
> packet of the flow.

"Will never reach its proper seat" is decidable at ingress from two
facts, and `peios_pnp_traversal_reaches_ip_seat()` decides it: the
ethertype (only `ETH_P_IP` and `ETH_P_IPV6` cross the IP hooks) and the
device's disposition (`netif_is_bridge_port()` — a frame on a
bridge-enslaved port is switched at L2 and never enters this device's IP
stack; a copy delivered to the bridge device itself is a separate
traversal on that device, judged there).

So at each seat the hook builds one snapshot and judges an ordered list
of layers:

| Seat | Layers, in traversal order |
|---|---|
| Ingress, IP frame on a plain port | `RawPacket` only (the Packet layer is *deferred* to `LOCAL_IN`) |
| Ingress, non-IP frame or bridge port | `RawPacket`, then `Packet` (the *fallback* judgment) |
| `LOCAL_IN` | `Packet`, then the flow's sentence or `Flow` |
| `LOCAL_OUT` | the flow's sentence or `Flow` |
| Egress | `Packet`, then `RawPacket` |

Traversal order is wire order: `RawPacket` is wire-proximate, so it is
first in and last out; `Flow` is innermost, last in and first out. Each
per-packet layer is evaluated once per traversal, and the first non-`PASS`
verdict ends the traversal. A layer with no published forest is
*permissive* and counted as such — at generation 0 that is every layer.

At the IP seats, a packet the Packet layer passed goes on to the flow
dispatch (§6.8): an untracked packet has no flow to judge and the Packet
verdict stands; a tracked packet with a current sentence gets that
sentence, and one without is evaluated by the Flow forest and sentenced.

## Applying a verdict

`PASS` continues to the next layer, then `NF_ACCEPT`. `DROP` is
`NF_DROP`. `REJECT` is `NF_DROP` plus a refusal, phrased by the kind the
rule chose and the packet's protocol:

| Kind | IPv4 | IPv6 |
|---|---|---|
| `Refused` (default) | TCP: RST; else ICMP port-unreachable | TCP: RST; else ICMPv6 port-unreachable |
| `Prohibited` | ICMP `ICMP_PKT_FILTERED` (type 3, code 13) | ICMPv6 `ICMPV6_ADM_PROHIBITED` (type 1, code 1) |

Every seat can refuse IP traffic. `refuse.c` builds the answer with the
kernel's frame-less reject builders (`nf_reject_skb_v4_tcp_reset()`,
`nf_reject_skb_v4_unreach()` and the v6 pair — the ones nftables' netdev
reject uses), attaches the flow to it (`nf_ct_attach()`, so conntrack
files it as the reply it claims to be), marks it, and delivers it:

- from the **ingress** seat, to the peer on the wire — `dev_hard_header()`
  with the offending frame's MACs swapped, then `dev_queue_xmit()`;
- from **every other seat**, to ourselves — `skb_dst_set_noref()` from
  the offending packet's route, `ip_route_me_harder()` (or the v6
  helper), then `ip_local_out()`. Inbound, that routes the answer out to
  the peer with our address as its source; outbound, the answer is the
  peer's, addressed to us, so the route lands on the loopback device and
  the stack's own RST and ICMP-error handlers fail the local socket with
  `ECONNREFUSED` or `EHOSTUNREACH` at once. The loopback device retains
  the route the packet was sent with, so the foreign source address
  never meets source validation.

The answer is not sent, and the `REJECT` **degrades to `DROP`** (counted
in `reject_degraded`, flagged `REJECT_DEGRADED` in the event, the kind
still named), when there is nothing to send: a non-IP frame, a broadcast
or multicast destination, a builder that declines (a fragment, a failed
checksum, a refusal of a refusal), a packet with no route to reason from,
or an allocation failure. Refusals sent are counted in
`refusals_emitted`.

## The refusal law

**PNP does not judge its own refusals.** The answer `refuse.c` builds
carries `skb->pnp_refusal`, a bit the `pnp-refusal-bit` patch adds to
`struct sk_buff` inside its `headers` group (so clones and copies keep
it); every hook checks it first and returns `NF_ACCEPT` without a
snapshot, an evaluation or an event, counting `refusals_bypassed`.
Refusals are verdict machinery, not traffic: without the bit, an inbound
`REJECT`'s RST would cross the egress seat and could be dropped — and
attributed — by an outbound rule, and an outbound `REJECT`'s forged peer
answer would be judged as inbound traffic on its way to the socket.

## Failing closed

Evaluation can fail: the core allocates `GFP_ATOMIC` during a walk and
an allocation can be refused. The hook then drops the packet, counts
`fail_closed`, and emits an event attributed to `fail-closed` with the
`FAIL_CLOSED` flag. Totality does not take "no answer" for an answer.

A snapshot that cannot be built — a frame too mangled to describe — is
counted (`parse_errors`) and judged on its seat facts alone; the
absent-fact law does the rest.
