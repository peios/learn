---
title: "network.*"
description: "Every field the evman catalogue defines under network: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `network`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="network.bridge.name"></a>`network.bridge.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The name of the bridge device an interface was enslaved to or released
from. Enslaving an interface to a bridge moves its traffic off the IP seats
and onto its device seats alone, which changes which rules can apply to it.

**Carried by:**

No event carries this field yet.

## <a id="network.direction"></a>`network.direction`

- **Type:** `str.enum`
- **Values:** `in` · `out`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

Which way the traffic was moving relative to this machine.

**Carried by:**

- [`ntfe.verdict.reported`](~peios/events/ntfe/ntfe-verdict-reported)

## <a id="network.ether-type"></a>`network.ether-type`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The link-layer protocol number of the frame.

**Carried by:**

- [`ntfe.verdict.reported`](~peios/events/ntfe/ntfe-verdict-reported)

## <a id="network.family"></a>`network.family`

- **Type:** `uint.enum`
- **Values:** `0 AF_UNSPEC` · `2 AF_INET` · `10 AF_INET6`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The address family of the addresses in this record. `AF_UNSPEC` when the
traffic was evaluated below the layer where addresses exist, in which case
no address, port or protocol field is present.

**Carried by:**

- [`ntfe.verdict.reported`](~peios/events/ntfe/ntfe-verdict-reported)

## <a id="network.hop-limit"></a>`network.hop-limit`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The packet's remaining hop count: the IPv4 TTL or the IPv6 hop limit, as
the packet carried it at the seat that judged it. Absent below the layer
where an IP header exists.

**Carried by:**

No event carries this field yet.

## <a id="network.interface.disposition"></a>`network.interface.disposition`

- **Type:** `str.enum`
- **Values:** `policed` · `bridge-port` · `seats-failed` · `other-namespace`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

How NTFE stands towards a network device. `policed` has its device seats in
place, and its IP traffic also reaches the IP seats, where the flow layer
and conntrack facts exist. `bridge-port` has its device seats, but its
frames are switched at the link layer and never reach the IP seats, so only
the device seats judge them and no flow-state or identity rule applies.
`seats-failed` is a device that registered but whose seats could not be
attached: its raw-packet traffic is never judged. `other-namespace` is
outside the initial network namespace and is not policed at all.

**Carried by:**

No event carries this field yet.

## <a id="network.interface.disposition-previous"></a>`network.interface.disposition-previous`

- **Type:** `str.enum`
- **Values:** `policed` · `bridge-port` · `seats-failed` · `other-namespace`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The disposition a network device had before the change a record reports,
in the terms of `network.interface.disposition`. A change from `policed` to
`bridge-port` is the one that quietly withdraws every flow-layer rule from
the device.

**Carried by:**

No event carries this field yet.

## <a id="network.interface.index"></a>`network.interface.index`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The kernel's index for that interface. Zero when no interface was
determined. Indexes are reused across interface teardown, so
`network.interface.name` is the durable one.

**Carried by:**

- [`ntfe.verdict.reported`](~peios/events/ntfe/ntfe-verdict-reported)

## <a id="network.interface.name"></a>`network.interface.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The network interface the traffic was seen on.

**Carried by:**

- [`ntfe.verdict.reported`](~peios/events/ntfe/ntfe-verdict-reported)

## <a id="network.length"></a>`network.length`

- **Type:** `uint.bytes`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The length of the traffic unit evaluated.

**Carried by:**

- [`ntfe.verdict.reported`](~peios/events/ntfe/ntfe-verdict-reported)

## <a id="network.namespace"></a>`network.namespace`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The network namespace a device or flow belongs to, by the kernel's
namespace number. NTFE polices only the initial namespace, so today this
field exists to say that something was in a different one and was not
judged at all.

**Carried by:**

No event carries this field yet.

## <a id="network.protocol"></a>`network.protocol`

- **Type:** `uint.enum`
- **Values:** `1 ICMP` · `2 IGMP` · `6 TCP` · `17 UDP` · `47 GRE` · `50 ESP` · `51 AH` · `58 IPv6-ICMP` · `132 SCTP` · `136 UDPLite`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The transport protocol number, from the IANA protocol numbers registry. A
number not listed is still a protocol, rendered as its number.

**Carried by:**

- [`ntfe.verdict.reported`](~peios/events/ntfe/ntfe-verdict-reported)

## <a id="network.tcp-flags"></a>`network.tcp-flags`

- **Type:** `uint.flags`
- **Values:** `0x1 FIN` · `0x2 SYN` · `0x4 RST` · `0x8 PSH` · `0x10 ACK` · `0x20 URG` · `0x40 ECE` · `0x80 CWR`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The flag bits of the TCP header, taken whole from the flags byte at offset
13.
Absent on any protocol other than TCP, and also absent on a TCP packet
whose header NTFE could not read, which a reader cannot otherwise tell from
a protocol without flags.

**Carried by:**

No event carries this field yet.

## <a id="network.vlan"></a>`network.vlan`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The VLAN id the traffic belongs to. At the device seats it is the tag on
the frame; at the IP seats the tag has already been stripped and it is the
id of the VLAN device the packet arrived on or leaves by. Absent when the
traffic is not on a VLAN.

**Carried by:**

No event carries this field yet.

*Generated from `ntfe.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
