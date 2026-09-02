---
title: Network policy reference
type: reference
description: Every registry key, value, fact, operator, action and limit of Peios Network Policy, with the value forms the kernel accepts.
related:
  - peios/networking/network-policy
  - peios/networking/the-pnp-viewer
---

The complete vocabulary of PNP rules as the kernel reads them. The
concepts — layers, the forest, the laws — are in
[Network policy](../410--network-policy.md); this page is the lookup
table.

## Registry layout

```text
Machine\System\Network\Rules
    CurrentReportingLevel        REG_DWORD 1..6   (optional; absent = 1)
    RawPacket\                   the wire-side layer's forest
        <rule>\
    Packet\                      the per-packet layer's forest
        <rule>\                  one tree root
            <exception>\         a subkey: narrower region, same laws
                ...
    Flow\                        the flow layer's forest
        <rule>\
```

A rule key's name is its attribution handle and may not contain `\` or
`/`. Layer keys other than `RawPacket`, `Packet` and `Flow` are ignored.

### Rule values

| Value | Type | Meaning |
|---|---|---|
| `Actions` | `REG_MULTI_SZ` | The action list, one expression per element. Absent or empty = `NULL` (abstain). |
| `Priority` | `REG_DWORD` / `REG_QWORD` | Collation weight. Inherited by subkeys; a root defaults to 0. |
| `Enabled` | `REG_DWORD` 0 or 1 | 0 disables the rule and its whole subtree. Default 1. |
| `<Fact>.<Operator>` | see below | A condition. Any other value name is an error that refuses the generation. |

### The Rules key's own value

| Value | Type | Meaning |
|---|---|---|
| `CurrentReportingLevel` | `REG_DWORD` 1..6 | `REPORT(n)` fires when `n >= CurrentReportingLevel`. Absent = 1 (everything fires); 6 silences all reports. Out of range refuses the generation. |

## Conditions

A condition is a value named `<Fact>.<Operator>`. A rule matches when
every condition holds; a condition over a fact the packet lacks is false
(the absent-fact law).

### Operators

| Operator | Families | Value |
|---|---|---|
| `Equal` | all | Membership: a scalar, or a list (`REG_MULTI_SZ`) meaning *any of*. Integers accept `a-b` ranges; addresses accept CIDR prefixes and (IPv4) `a-b` ranges. |
| `GreaterThan` | integer | A single integer; strictly greater. |
| `LessThan` | integer | A single integer; strictly less. |
| `Has` | flags | A flag name or list; all listed bits set. |
| `Hasnt` | flags | A flag name or list; all listed bits clear. |

Integer values may be written as `REG_DWORD`, `REG_QWORD`, or as decimal
strings; a list of integers is a `REG_MULTI_SZ` of decimal strings and
ranges. Applying an operator a family does not support (`GreaterThan` on
an address, `Has` on a port) refuses the generation.

### Facts

| Fact | Family | Values | Present when |
|---|---|---|---|
| `Direction` | string | `in`, `out` | always. `Flow`: the originator's side, for the flow's whole life |
| `Interface` | string | interface name, e.g. `eth0` | always. `Flow`, outbound: the route's device |
| `EtherType` | integer | number, or `ipv4`, `ipv6`, `arp` | always. Not a `Flow` fact (a flow's family is its addresses') |
| `SrcMac` | MAC | `aa:bb:cc:dd:ee:ff` | frame has an Ethernet header; at the IP seats outbound, the machine's own device address |
| `DstMac` | MAC | `aa:bb:cc:dd:ee:ff` | frame has an Ethernet header. Not a `Flow` fact |
| `Vlan` | integer | VLAN id | the frame is VLAN-tagged (device seats) or the interface is a VLAN device (IP seats) |
| `SrcAddr`, `DstAddr` | address | exact (`10.0.0.5`, `fd00::1`), CIDR (`10.0.0.0/8`, `fd00::/64`), IPv4 range (`10.0.0.1-10.0.0.99`) | IP packet |
| `Protocol` | integer | number, or `tcp`, `udp`, `icmp`, `icmpv6`, `sctp` | IP packet |
| `Ttl` | integer | TTL / hop limit | IP packet. Not a `Flow` fact |
| `Dscp` | integer | 0..63 | IP packet. Not a `Flow` fact |
| `Fragment` | integer | `0` or `1` | IP packet (only ever 1 before defragmentation, i.e. at the RawPacket seat). Not a `Flow` fact |
| `SrcPort`, `DstPort` | integer | 0..65535 | TCP, UDP or SCTP |
| `TcpFlags` | flags | `FIN`, `SYN`, `RST`, `PSH`, `ACK`, `URG`, `ECE`, `CWR` | TCP. Not a `Flow` fact |
| `IcmpType`, `IcmpCode` | integer | ICMP / ICMPv6 type and code | ICMP or ICMPv6 |
| `Length` | integer | packet length in bytes at the seat (stack view) | always. Not a `Flow` fact |
| `FlowState` | string | `new`, `established`, `related`, `invalid`, `untracked` | Packet layer at its proper seat; never at the RawPacket or Flow layers |
| `Related` | integer | `0` or `1`: the flow was expected by another (an ICMP error for a live flow, FTP data) | `Flow` layer only |
| `Time.Year`, `Time.Month`, `Time.DayOfMonth`, `Time.DayOfWeek`, `Time.Hour`, `Time.Minute`, `Time.Second` | integer | wall clock, UTC; `DayOfWeek` is ISO (1 = Monday .. 7 = Sunday) | always. In `Flow`, a consulted condition expires the sentence at its next flip |
| `Start.Year`, `Start.Month`, `Start.DayOfMonth`, `Start.DayOfWeek`, `Start.Hour`, `Start.Minute`, `Start.Second` | integer | the wall clock when the flow began, UTC | `Flow` layer only; fixed for the flow's life, never expires a sentence |
| `Tag.<name>` | integer | the flow tag's value | the flow carries the tag (`Packet` and `Flow` layers; never `RawPacket`) |
| `Counter.<name>[(...)]` | integer | a counter view, see below | the packet has the view's key facts and a cell exists |

Address families are strict: an IPv4 pattern never matches an IPv6
address and vice versa, so `0.0.0.0/0` does not swallow IPv6.

A `Flow` fact is one that is identical for every packet of the flow. The
per-packet facts marked "not a `Flow` fact" are legal in a `Flow` rule
but never present there, so the condition never holds; the viewer flags
it. `Related` and `Start.*` are the reverse: never present outside
`Flow`.

### Counter views

`Counter.<name>` reads the stream `<name>` that some rule's `COUNT`
writes. In parentheses, in any order, at most one of each:

| Argument | Form | Meaning |
|---|---|---|
| window | `<n>s`, `<n>m`, `<n>h`, `<n>d` — at most `1d` | Sliding window; omitted = the cumulative total since the cell was created. |
| key | `SrcAddr`, `DstAddr`, `Interface`, or a `+`-compound (`SrcAddr+DstAddr`) | Which facts partition the count; omitted = one global cell. |

Examples: `Counter.dns` (total, global); `Counter.dns(10s)` (last ten
seconds, global); `Counter.dns(SrcAddr)` (total, per source);
`Counter.dns(1h, SrcAddr+DstAddr)` (last hour, per source–destination
pair). A view over a stream that no rule anywhere writes refuses the
generation; a stream nobody reads is fine. Windows are approximated by
eight buckets, so a value can be up to an eighth of a window stale.

## Actions

`Actions` is a list of expressions. Names are case-insensitive;
whitespace is ignored. A rule's actions may contain any mix; at most one
verdict results (the strictest listed).

| Expression | Species | Meaning |
|---|---|---|
| `NULL` | abstention | Nothing. A rule whose actions yield no verdict abstains. |
| `PASS` | verdict | This layer approves. |
| `DROP` | verdict | Refuse silently. |
| `REJECT` / `REJECT(Refused)` | verdict | Refuse; look like nothing is listening — TCP RST, else ICMP port-unreachable. |
| `REJECT(Prohibited)` | verdict | Refuse; say policy did it — ICMP admin-prohibited for every protocol. |
| `PROMPT(Handler[, Fallback])` | deferral | Ask a userspace handler; on no answer apply `Fallback` (an action expression, nesting up to 4 deep). No handler transport exists in this release: the fallback applies immediately and the prompt is recorded. |
| `TAG(Name, Set[, n])` | effect | Set flow tag `Name` to `n` (default 1). |
| `TAG(Name, Add[, n])` | effect | Add `n` (default 1) to the tag; an absent tag counts as 0 first. |
| `TAG(Name, Clear)` | effect | Remove the tag; it reads as absent afterwards. |
| `COUNT(Name[, n])` | effect | Emit `n` (default 1) into stream `Name`. |
| `COUNT(Name, Length)` | effect | Emit the packet's byte length — the bandwidth primitive. |
| `REPORT(level)` | effect | Emit a `network-report` audit event, level 1..5, if the level clears `CurrentReportingLevel`. One report per rule per evaluation, at the highest level listed. |

Unknown action names, wrong argument counts, negative or non-integer
operands, unminted `REJECT` kinds, and a `TAG` operation other than the
three above all refuse the generation.

### Where a REJECT can speak

Everywhere, for IP traffic. Inbound, the refusal goes back to the peer.
Outbound, the answer the peer would have sent is delivered to the local
socket, so the program's connect fails at once with *connection refused*
(`Refused`, TCP) or *host unreachable* (`Prohibited`, or any UDP
refusal). Only a packet with no refusal vocabulary — ARP and other
non-IP frames, a broadcast or multicast destination, a fragment — is
applied as a `DROP` and counted as *degraded*; the verdict event still
says `REJECT` and names the kind. The refusals PNP sends pass its own
seats unjudged.

In the `Flow` layer a `REJECT` sentence answers every later packet of
the flow the same way, so a retransmitted SYN gets its reset too.

## Layers

| | `RawPacket` | `Packet` | `Flow` |
|---|---|---|---|
| Judged | at the device seats, for all traffic, per packet | once per traversal, at the richest seat, per packet | once per flow (per local endpoint), at the IP seats, on the flow's first packet |
| Order | first inbound, last outbound | between | last inbound (after `Packet`), first outbound (before `Packet`) |
| `FlowState` | never (the seat stands before conntrack) | yes | never (the layer is the judgment of a flow) |
| `Related`, `Start.*` | never | never | yes |
| Per-packet facts (`Length`, `TcpFlags`, `Fragment`, `Ttl`, `Dscp`, `EtherType`, `DstMac`) | yes | yes | never |
| `Tag.<name>` reads | never | tags `RawPacket` or `Packet` rules write | any tag |
| `TAG` writes | yes | yes | yes |
| `Fragment` | may be 1 | always 0 | — |
| Effects run | per packet | per packet | per evaluation of the flow |
| Verdict scope | the packet | the packet | the flow: cached as its sentence |

A rule conditioned on a fact its layer never has is legal but can never
match; the viewer flags it. A `Packet` or `RawPacket` rule that reads a
tag a `Flow` rule writes is a downward read and refuses the generation.

### Sentences

The `Flow` layer's verdict for a flow is cached on the flow with the
policy generation that judged it and an expiry. A packet of a flow whose
sentence is current is not evaluated (and emits no event). A sentence is
stale, and the flow re-judged on its next packet, when:

- the policy generation has changed since the judgment, or
- a live-time condition (`Time.*`) the judgment consulted — true or
  false — would have flipped by now. Hour, minute, second and day-of-week
  conditions flip exactly when their value would next change the
  condition's answer; day-of-month, month and year conditions
  re-judge daily at midnight UTC.

A re-judgment is a full evaluation: effects run again. A flow that
conntrack could not give an extension (allocation failure at creation)
holds no sentence and is evaluated on every packet, counted.

A loopback flow has two local endpoints and two sentences: judged as
`out` at the outbound seat and as `in` at the inbound seat, and every
packet of it answers to the stricter of the two.

## Limits

| Limit | Value | When exceeded |
|---|---|---|
| Distinct tags per flow | 64 | the write is refused and counted |
| Keys per counter table | 4096 | idle keys are reaped; if none are idle the new key is refused and counted |
| Windows per (stream, key) | 8 | the generation is refused |
| Longest window | 1 day | the generation is refused |
| Rule nesting depth | 12 | the generation is refused |
| Rules per layer | 4096 | the generation is refused |
| Attribution path in events | 96 bytes | truncated |
| Tags reported per flow in the flows dump | 8 | the rest are counted, not listed |

## The development baseline

Experimental images ship a seed policy so a fresh machine works while
still refusing unsolicited inbound connections. The compiled-in backstop
is `DROP` in every layer; each line below is a visible, deletable yes.

`Rules\RawPacket`:

| Rule | Conditions | Actions |
|---|---|---|
| `all` | — | `PASS` |

`Rules\Packet` — passes every tracked packet through to `Flow`, and the
untracked housekeeping a host needs:

| Rule | Conditions | Actions |
|---|---|---|
| `tracked` | `FlowState.Equal` = `new`, `established`, `related` | `PASS` |
| `outbound-ok` | `Direction.Equal` = `out` | `PASS` |
| `loopback` | `Interface.Equal` = `lo` | `PASS` |
| `arp` | `EtherType.Equal` = `arp` | `PASS` |
| `icmpv6-housekeeping` | `Protocol.Equal` = `icmpv6`, `IcmpType.Equal` = `130-137`, `143` | `PASS` |
| `dhcp-client` | `Protocol.Equal` = `udp`, `SrcPort.Equal` = `67`, `DstPort.Equal` = `68` | `PASS` |

`Rules\Flow` — the decisions:

| Rule | Conditions | Actions |
|---|---|---|
| `outbound-ok` | `Direction.Equal` = `out` | `PASS` |
| `loopback` | `Interface.Equal` = `lo` | `PASS` |
| `dev-viewer-ports` | `Direction.Equal` = `in`, `Protocol.Equal` = `tcp`, `DstPort.Equal` = `8080`, `8081` | `PASS` |

Every other inbound flow meets the `Flow` backstop, once, on its first
packet; untracked inbound packets meet the `Packet` backstop.

## Worked examples

**An exception under a broad rule** — drop all inbound except SSH from
the LAN, and tell other SSH sources that policy said no:

```text
Rules\Packet\no-inbound            Direction.Equal = in
                                   Actions = DROP
Rules\Packet\no-inbound\ssh        DstPort.Equal = 22
                                   Actions = REJECT(Prohibited)
Rules\Packet\no-inbound\ssh\lan    SrcAddr.Equal = 10.0.0.0/8
                                   Actions = PASS
```

**A flow tag read on the reply** — mark DNS queries, report on the
replies of marked flows:

```text
Rules\Packet\tag-dns        Protocol.Equal = udp, DstPort.Equal = 53
                            Actions = TAG(dnsq, Add)
Rules\Packet\tagged-reply   Protocol.Equal = udp, SrcPort.Equal = 53
                            Tag.dnsq.GreaterThan = 0
                            Actions = REPORT(4)
```

**Byte accounting per interface** — count outbound bytes and refuse a
source that pushes more than 100 MB in a minute:

```text
Rules\Packet\egress-bytes   Direction.Equal = out
                            Actions = COUNT(egress, Length)
Rules\Packet\egress-cap     Direction.Equal = out
                            Counter.egress(1m, SrcAddr).GreaterThan = 104857600
                            Actions = DROP
```

**A connection-level allow** — let the machine connect out, accept SSH
in from the LAN, and refuse every other inbound connection with a reset,
each decided once per flow:

```text
Rules\Flow\outbound-ok      Direction.Equal = out
                            Actions = PASS
Rules\Flow\inbound          Direction.Equal = in
                            Actions = REJECT
Rules\Flow\inbound\ssh-lan  Protocol.Equal = tcp, DstPort.Equal = 22
                            SrcAddr.Equal = 10.0.0.0/8
                            Actions = PASS
```

**A curfew that lets downloads finish** — no new outbound connections
between 22:00 and 06:00 UTC, existing ones run on:

```text
Rules\Flow\curfew           Direction.Equal = out
                            Start.Hour.Equal = 22-23, 0-5
                            Priority = 10
                            Actions = REJECT(Prohibited), REPORT(3)
```

Written with `Time.Hour` instead of `Start.Hour`, the same rule cuts
every running outbound connection at 22:00 — on its next packet, with
an ICMP admin-prohibited — and the report says which rule did it.

**Connection rate limiting** — count connections, not packets, by
counting in the flow layer:

```text
Rules\Flow\conn-count       Direction.Equal = in, Protocol.Equal = tcp
                            Actions = COUNT(conns)
Rules\Flow\conn-flood       Direction.Equal = in, Protocol.Equal = tcp
                            Counter.conns(1m, SrcAddr).GreaterThan = 100
                            Actions = DROP
```
