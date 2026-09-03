---
title: Network policy reference
type: reference
description: Every registry key, value, fact, operator, action and limit of Peios Network Policy — the packet layers the kernel reads and the interface layer netd executes — with the value forms each accepts.
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
Machine\System\Network
    Hostname                     REG_SZ           operator
    Readiness                    REG_SZ           netd: absent | link | addressed | routed
    Duid                         REG_SZ           shared: DHCPv6 identifier, hex
    Rules\
        CurrentReportingLevel    REG_DWORD 1..6   (optional; absent = 1)
        RawPacket\               the wire-side layer's forest
            <rule>\
        Packet\                  the per-packet layer's forest
            <rule>\              one tree root
                <exception>\     a subkey: narrower region, same laws
                    ...
        Flow\                    the flow layer's forest
            <rule>\
        Interface\               the interface layer's forest (netd's)
            <rule>\
    Profiles\                    how an interface stands on a network
        <profile>\               flat dotted values, see Profiles
            <derived>\           a subkey inherits and overrides
    Interfaces\<id>\             the inventory, one key per interface seen
        ClientId                 REG_SZ           shared: DHCPv4 client identifier
        Status\                  netd-only: Name, Kind, Mac, Path, Driver,
                                 Verdict, Rule, Profile, Readiness, LastNetwork
    Networks\<id>\               one key per network stood on
        Name, Trust              REG_SZ           operator
        RequestedAddress         REG_SZ           shared: IPv4 to ask for next
        Status\                  netd-only: Kind, Server, Gateway, Router,
                                 Prefixes, DnsServers, LastSeen, LastInterface
    Dns\                         name resolution's machine values, see name resolution
```

A rule key's name is its attribution handle and may not contain `\` or
`/`. The kernel reads `RawPacket`, `Packet` and `Flow`; `Interface` is
read by netd, the interface layer's executor (see [Layers](#layers)); any
other layer key is ignored by both. *Shared* values are written by netd
when absent and may be set by the operator; `Status` keys carry a
descriptor that lets only netd write, so a hand edit is refused rather
than silently reverted.

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
| `Present` | all, and `Tag.<name>` / `Counter.<name>` | `1`: the fact exists for this packet or flow; `0`: it does not. The one operator that looks through the absent-fact law. On a fact its layer never has, it refuses the generation rather than becoming an always-true condition. |

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
| `Local` | string | `program`, `kernel`, `shared`, `none`: what stands at this machine's end of the flow | `Flow` layer only; always present there |
| `Local.User` | SID | `S-1-5-19`, or a well-known name (`SYSTEM`, `LocalService`, `NetworkService`, `Everyone`, `Administrators`, `Users`, …) | `Flow`, `Local` is `program` |
| `Local.Group` | SID set | SIDs or well-known names; *any of* the token's enabled groups (deny-only groups are invisible; the logon SID is among them) | `Flow`, `Local` is `program` |
| `Local.Integrity` | integer | a level, or `untrusted`, `low`, `medium`, `high`, `system` | `Flow`, `Local` is `program` |
| `Local.Confinement` | SID | the confinement SID | `Flow`, the program is confined |
| `Local.Capability` | SID set | *any of* the confinement's capability SIDs | `Flow`, the program is confined |
| `Local.Service` | SID | a service *name* (`resolvd`), or its `S-1-5-80-…` SID | `Flow`, the program is a service |
| `Local.Process` | string | the process GUID, `8-4-4-4-12` hex (case-insensitive) | `Flow`, `Local` is `program` |
| `Remote`, `Remote.*` | as `Local` | the other end of the flow, when it is on this machine too | `Flow`, loopback flows only |
| `Interface.Kind` | string | `wired`, `wireless`, `loopback`, `tunnel`, `bridge`, `other` | `Interface` layer only; always |
| `Interface.Id` | string | the stable interface id (the inventory key name) | `Interface` layer only; always |
| `Interface.Mac` | MAC | `aa:bb:cc:dd:ee:ff` | `Interface` layer only; the interface has a hardware address |
| `Interface.Path` | string | bus position, e.g. `pci-0000:00:03.0` | `Interface` layer only; it is hardware |
| `Interface.Driver` | string | kernel driver | `Interface` layer only; it is hardware |
| `Network.Id` | string | the network record's key name under `Networks\` | `Interface` layer only; a network has been identified on the link |
| `Network.Name` | string | the operator's `Name` on the record | `Interface` layer only; the record has one |
| `Network.Trust` | string | the operator's `Trust` on the record | `Interface` layer only; the record has one |
| `Network.Kind` | string | the `Interface.Kind` the network was seen on | as `Network.Id` |
| `Tag.<name>` | integer | the flow tag's value | the flow carries the tag (`Packet` and `Flow` layers; never `RawPacket`) |
| `Counter.<name>[(...)]` | integer | a counter view, see below | the packet has the view's key facts and a cell exists |

Address families are strict: an IPv4 pattern never matches an IPv6
address and vice versa, so `0.0.0.0/0` does not swallow IPv6.

A `Flow` fact is one that is identical for every packet of the flow. The
per-packet facts marked "not a `Flow` fact" are legal in a `Flow` rule
but never present there, so the condition never holds; the viewer flags
it. `Related`, `Start.*` and the identity facts are the reverse: never
present outside `Flow`. The `Interface.*` and `Network.*` families exist
only at the `Interface` layer, where `Interface` (the name) is the one
packet fact shared with them; a packet fact in an `Interface` rule is
likewise dead. `Tag.*` and `Counter.*` do not exist at the `Interface`
layer at all — there is no store behind them — and refuse the generation.

### Who is at this end

`Local` says what answers at this machine's end of a flow: a
`program` (a socket some process owns — the identity the kernel stamped
on it at the last act that committed it: creation, bind, listen,
connect, accept, or an explicit restamp), the `kernel` itself (resets,
ICMP errors, neighbour discovery, tunnel outers, kernel sockets),
`shared` (inbound multicast or broadcast, delivered to every socket
bound to the port — one flow, many receivers), or `none` (nothing
listens; the stack will refuse it). Only a `program` has `Local.*`
facts, so `Local.User.Present = 0` is "no program stands here".

Identity is decided once, at the flow's first judgment, and kept for
the flow's life. A service thread acting for a client is the client
(the *effective* identity governs, as it does for files); a listener
handed to another program is governed by the program that last
committed it. SIDs are written as `S-1-…`; a user or group may instead
be a well-known name, a service its name — the name is turned into the
service's SID exactly as the service's token was minted, so the rule
matches the token, not a string. A misspelt name refuses the
generation rather than quietly matching nothing.

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
| `JOIN(profile)` | verdict, `Interface` layer | Bring the interface up and stand in the named profile: a path under `Profiles\`, `/`- or `\`-separated. |
| `IGNORE` | verdict, `Interface` layer | Never touch the interface; something else owns it. |
| `DOWN` | verdict, `Interface` layer | Keep the interface administratively down. |

The three interface verdicts are legal only in the `Interface` layer,
and that layer speaks nothing but them, `NULL` and `REPORT`; either way
round refuses the generation. Their strictness order is `DOWN` > `IGNORE`
> `JOIN`. `JOIN` must name a profile that exists (a path that names no
key refuses the generation); naming a *disabled* profile makes the rule
abstain, as if its action were `NULL`.

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
the flow the same way, so a retransmitted SYN gets its reset too. When
the refused packet belongs to an *established* TCP connection (a flow
re-judged after a policy change or at a time edge), the other end is
torn down as well: the refused packet is turned into a reset and sent
where it was going, so both sockets fail at once. New flows and UDP have
no far end to tear down.

## Layers

| | `RawPacket` | `Packet` | `Flow` |
|---|---|---|---|
| Judged | at the device seats, for all traffic, per packet | once per traversal, at the richest seat, per packet | once per flow (per local endpoint), at the IP seats, on the flow's first packet |
| Order | first inbound, last outbound | between | last inbound (after `Packet`), first outbound (before `Packet`) |
| `FlowState` | never (the seat stands before conntrack) | yes | never (the layer is the judgment of a flow) |
| `Related`, `Start.*` | never | never | yes |
| `Local`, `Local.*`, `Remote.*` | never | never | yes (`Remote` on loopback only) |
| Per-packet facts (`Length`, `TcpFlags`, `Fragment`, `Ttl`, `Dscp`, `EtherType`, `DstMac`) | yes | yes | never |
| `Tag.<name>` reads | never | tags `RawPacket` or `Packet` rules write | any tag |
| `TAG` writes | yes | yes | yes |
| `Fragment` | may be 1 | always 0 | — |
| Effects run | per packet | per packet | per evaluation of the flow |
| Verdict scope | the packet | the packet | the flow: cached as its sentence |

A rule conditioned on a fact its layer never has is legal but can never
match; the viewer flags it. A `Packet` or `RawPacket` rule that reads a
tag a `Flow` rule writes is a downward read and refuses the generation.

### The interface layer

`Rules\Interface` is the fourth layer, and the one the kernel does not
read. Its subject is an interface, not a packet: a rule is judged for each
interface (loopback excepted) whenever an interface appears or changes,
whenever a network is identified on it, and whenever a generation lands.
Its executor is netd, which builds and judges the forest with the same
engine the kernel uses, so a rule means the same thing in every layer.

| | `Interface` |
|---|---|
| Judged | per interface, by netd, on interface and generation change |
| Facts | `Interface`, `Interface.*`, `Network.*` |
| Verdicts | `JOIN(profile)`, `IGNORE`, `DOWN`; strictness in that order, rising |
| Effects | `REPORT` only |
| Backstop | `IGNORE`: an interface no rule speaks for is left as the kernel left it |
| Result | an interface is in exactly one profile, or ignored, or down |

The collation laws are the packet layers': highest priority wins, ties
go to the strictest verdict, a subkey is an exception, an abstaining rule
hands up its parentage. One case has no packet-layer analogue: two rules
tied on priority naming *different* profiles for one interface. That is a
conflict, not a choice, and it refuses the generation; `net status` names
both rules.

**Executor independence.** A generation is one registry state read by
two executors. Each validates and refuses its own layers on its own: a
dangling `JOIN` keeps netd on its last good interface forest and never
stalls the firewall, and a bad `Flow` rule never stops an interface
joining.

**The executor's own traffic.** Joining needs netd to send and receive
DHCP and router discovery, and PNP grants that nothing implicitly: the
permission is the `dhcp-client` and `icmpv6-housekeeping` rules of the
baseline below, ordinary and deletable. netd cannot yet read the verdict
stream to name a rule that refused it (the stream has one reader, the
viewer); `net status` reports an unanswered request as a warning.

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
packet of it answers to the stricter of the two. Each judgment sees its
own end as `Local` and the other as `Remote`.

## Profiles

`Profiles\<path>` is how an interface stands on a network, named by a
`JOIN`. A profile is a key with flat dotted values and no match block.

**Inheritance.** A subkey inherits every value of its ancestors and
overrides those it names — per value name, wholesale: a list replaces a
list, never appends. A present-but-empty value means *none*; an absent
value means *inherit*. This is the same law as in `Rules\`: a subkey
specialises its parent. A locally written profile may nest under one
pushed by policy. `Enabled` = `0` makes a key and its subtree invisible.

**Vocabulary.** Bundles are the claims a network can make; each has an
`Offered` that says whether to believe it. Every compiled default is
"believe nothing, do nothing": a bare profile brings the link up and
nothing else. Unknown value names refuse the generation.

| Bundle | Value | Type | Meaning | Default |
|---|---|---|---|---|
| `Address` | `Offered` | 0/1 | take the address the network offers (DHCPv4, IPv6 autoconfiguration) | 0 |
| | `Families` | list | `ipv4`, `ipv6`: which families the bundle deals in at all; filters `Static` too | both |
| | `Static` | list | CIDR addresses, either family | none |
| | `LinkLocal` | 0/1 | self-assign 169.254/16 while nobody answers; dropped when a lease arrives | 0 |
| | `Temporary` | 0/1 | add daily-rotating IPv6 privacy addresses beside the stable one | 0 |
| | `OnExpiry` | `Drop` / `Keep` | an offered address the network stops renewing | `Drop` |
| `Route` | `Offered` | 0/1 | take the way out, and extra routes, the network offers | 0 |
| | `Gateway` | list | pinned way out, either family | none |
| | `Metric` | number | rank of this interface's way out | 100 wired, 600 wireless |
| `Dns` | `Offered` | 0/1 | take the servers and search domains the network offers, after our own | 0 |
| | `Servers` | list | own servers, in order | none |
| | `Domains` | list | domains these servers answer for | none |
| | `Default` | 0/1/absent | take names no domain claims; absent follows the default route | absent |
| | `Exclusive` | 0/1 | while up, nobody else's servers are consulted | 0 |
| `Hostname` | `Offered` | 0/1 | adopt the network's name for us if `Hostname` is unset | 0 |
| | `Announce` | 0/1 | tell the network our name | 0 |
| `Mtu` | `Offered` | 0/1 | take the packet size limit the network offers | 0 |
| | `Value` | number, 68+ | pin it | leave alone |

The `Dns` bundle is provisional until the name-resolution pass of PNP.

**The laws of `JOIN`**, whatever the profile says: the executor owns
every address on a joined interface and only the routes it added itself;
exactly one place decides what a router advertisement means (the
executor; the kernel's own handling is off); a link-local address is
dropped the moment a real lease arrives; IPv6 lifetimes follow the RFCs
with the two-hour floor; `Route.Metric` defaults by kind; the network's
`RequestedAddress` is asked for first; a manual change to a joined
interface lasts until the next reconcile; restarting the executor
changes nothing visible.

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

`Profiles` and `Rules\Interface` — every wired interface joins the network
it is plugged into, taking what it offers:

| Key | Values |
|---|---|
| `Profiles\default` | `Address.Offered` = 1, `Address.LinkLocal` = 1, `Route.Offered` = 1, `Dns.Offered` = 1 |
| `Rules\Interface\wired` | `Interface.Kind.Equal` = `wired`, `Priority` = 10, `Actions` = `JOIN(default)` |

Wireless is not in the baseline until a supplicant exists. An interface
no rule speaks for meets the `Interface` backstop, `IGNORE`.

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

**A static server as an exception** — every wired interface takes what
the network offers, except the card in slot 3, which stands in a derived
profile that changes only the address and the way out:

```text
Profiles\default                 Address.Offered = 1, Address.LinkLocal = 1
                                 Route.Offered = 1, Dns.Offered = 1
Profiles\default\db1             Address.Offered = 0, Address.Static = 10.0.0.5/24
                                 Route.Offered = 0, Route.Gateway = 10.0.0.1
Rules\Interface\wired            Interface.Kind.Equal = wired
                                 Actions = JOIN(default)
Rules\Interface\wired\db1        Interface.Path.Equal = pci-0000:00:03.0
                                 Actions = JOIN(default/db1)
```

`default/db1` still takes the network's name servers: `Dns.Offered` is
inherited.

**The laptop** — one radio, three configurations, chosen by the network
on the other side:

```text
Rules\Interface\radio            Interface.Kind.Equal = wireless
                                 Actions = JOIN(untrusted)
Rules\Interface\radio\home       Network.Name.Equal = palfrey-home
                                 Actions = JOIN(home)
Rules\Interface\radio\office     Network.Trust.Equal = corporate
                                 Actions = JOIN(corp)
```

`Network.Name` and `Network.Trust` are what the operator wrote on the
record under `Networks\`; until a network has been identified on the
link they are absent, so the radio stands in `untrusted` first.

**A card that stays dark, and one another program owns:**

```text
Rules\Interface\dead-card        Interface.Id.Equal = 3f2a1b8e-…
                                 Priority = 100
                                 Actions = DOWN
Rules\Interface\tap              Interface.Equal = tap0
                                 Actions = IGNORE
```

**Connection rate limiting** — count connections, not packets, by
counting in the flow layer:

```text
Rules\Flow\conn-count       Direction.Equal = in, Protocol.Equal = tcp
                            Actions = COUNT(conns)
Rules\Flow\conn-flood       Direction.Equal = in, Protocol.Equal = tcp
                            Counter.conns(1m, SrcAddr).GreaterThan = 100
                            Actions = DROP
```
