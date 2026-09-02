---
title: Seats and dispatch
description: The netfilter hooks PNP stands at, the dispatch law that gives every traversal exactly one proper seat per layer, and how verdicts are applied where they land.
---

## The seats

PNP registers at three kinds of netfilter hook.

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
  is whole and its flow is classified. The `nf_reject` helpers can send
  from here.

Only `init_net` is instrumented: Peios has no container or network
namespace story yet, and the notifier ignores devices in other
namespaces.

## The dispatch law

The ratified law is stated in two sentences:

> RawPacket matches all traffic at the device seats, unconditionally.
> The Packet layer judges every traversal exactly once, at its proper
> seat — inbound IP at the IP hook, everything outbound at egress —
> falling back to the ingress seat iff the traversal will never reach its
> proper seat.

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
| `LOCAL_IN` | `Packet` |
| Egress | `Packet`, then `RawPacket` |

Traversal order is wire order: `RawPacket` is wire-proximate, so it is
first in and last out. Each layer is evaluated once per traversal, and
the first non-`PASS` verdict ends the traversal. A layer with no
published forest is *permissive* and counted as such — at generation 0
that is every layer.

## Applying a verdict

`PASS` continues to the next layer, then `NF_ACCEPT`. `DROP` is
`NF_DROP`. `REJECT` is `NF_DROP` plus a refusal, phrased by the kind the
rule chose and the packet's protocol:

| Kind | IPv4 | IPv6 |
|---|---|---|
| `Refused` (default) | TCP: `nf_send_reset()`; else ICMP port-unreachable | TCP: `nf_send_reset6()`; else ICMPv6 port-unreachable |
| `Prohibited` | ICMP `ICMP_PKT_FILTERED` (type 3, code 13) | ICMPv6 `ICMPV6_ADM_PROHIBITED` (type 1, code 1) |

A refusal can only be sent from `LOCAL_IN`, where the hook state carries
a route and a socket to answer with. A `REJECT` decided at a device seat
— every outbound packet, and non-IP frames — **degrades to `DROP`**: the
packet is dropped, the degradation is counted (`reject_degraded`), and
the verdict event still says `REJECT` with its kind and the
`REJECT_DEGRADED` flag, so nothing about the decision is hidden. The
outbound case is a known limitation of the seat geometry (an egress hook
has no `nf_reject` path), recorded in the design's care list.

## Failing closed

Evaluation can fail: the core allocates `GFP_ATOMIC` during a walk and
an allocation can be refused. The hook then drops the packet, counts
`fail_closed`, and emits an event attributed to `fail-closed` with the
`FAIL_CLOSED` flag. Totality does not take "no answer" for an answer.

A snapshot that cannot be built — a frame too mangled to describe — is
counted (`parse_errors`) and judged on its seat facts alone; the
absent-fact law does the rest.
