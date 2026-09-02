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
    Packet\                      the packet layer's forest
        <rule>\                  one tree root
            <exception>\         a subkey: narrower region, same laws
                ...
    RawPacket\                   the wire-side layer's forest
        <rule>\
```

A rule key's name is its attribution handle and may not contain `\` or
`/`. Layer keys other than `Packet` and `RawPacket` are ignored.

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
| `Direction` | string | `in`, `out` | always |
| `Interface` | string | interface name, e.g. `eth0` | always |
| `EtherType` | integer | number, or `ipv4`, `ipv6`, `arp` | always |
| `SrcMac`, `DstMac` | MAC | `aa:bb:cc:dd:ee:ff` | frame has an Ethernet header |
| `Vlan` | integer | VLAN id | frame is VLAN-tagged |
| `SrcAddr`, `DstAddr` | address | exact (`10.0.0.5`, `fd00::1`), CIDR (`10.0.0.0/8`, `fd00::/64`), IPv4 range (`10.0.0.1-10.0.0.99`) | IP packet |
| `Protocol` | integer | number, or `tcp`, `udp`, `icmp`, `icmpv6`, `sctp` | IP packet |
| `Ttl` | integer | TTL / hop limit | IP packet |
| `Dscp` | integer | 0..63 | IP packet |
| `Fragment` | integer | `0` or `1` | IP packet (only ever 1 before defragmentation, i.e. at the RawPacket seat) |
| `SrcPort`, `DstPort` | integer | 0..65535 | TCP, UDP or SCTP |
| `TcpFlags` | flags | `FIN`, `SYN`, `RST`, `PSH`, `ACK`, `URG`, `ECE`, `CWR` | TCP |
| `IcmpType`, `IcmpCode` | integer | ICMP / ICMPv6 type and code | ICMP or ICMPv6 |
| `Length` | integer | packet length in bytes at the seat (stack view) | always |
| `FlowState` | string | `new`, `established`, `related`, `invalid`, `untracked` | Packet layer at its proper seat; never at the RawPacket layer |
| `Time.Year`, `Time.Month`, `Time.DayOfMonth`, `Time.DayOfWeek`, `Time.Hour`, `Time.Minute`, `Time.Second` | integer | wall clock, UTC; `DayOfWeek` is ISO (1 = Monday .. 7 = Sunday) | always |
| `Tag.<name>` | integer | the flow tag's value | the flow carries the tag (Packet layer only) |
| `Counter.<name>[(...)]` | integer | a counter view, see below | the packet has the view's key facts and a cell exists |

Address families are strict: an IPv4 pattern never matches an IPv6
address and vice versa, so `0.0.0.0/0` does not swallow IPv6.

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

A refusal can only be sent from the inbound IP seat. A `REJECT` decided
at a device seat — every outbound packet, and non-IP frames — is applied
as a `DROP` and counted as *degraded*; the verdict event still says
`REJECT` and names the kind.

## Layers

| | `Packet` | `RawPacket` |
|---|---|---|
| Judged | once per traversal, at the richest seat | at the device seats, for all traffic |
| `FlowState` | yes | never (the seat stands before conntrack) |
| `Tag.<name>` reads | yes | never — tags flow upward only |
| `TAG` writes | yes | yes |
| `Fragment` | always 0 | may be 1 |

A `RawPacket` rule conditioned on `FlowState` or a tag is legal but can
never match; the viewer flags it.

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

## The development baseline

Experimental images ship a seed policy under `Rules\Packet` so a fresh
machine works while still dropping unsolicited inbound traffic:

| Rule | Conditions | Actions |
|---|---|---|
| `outbound-ok` | `Direction.Equal` = `out` | `PASS` |
| `established` | `FlowState.Equal` = `established`, `related` | `PASS` |
| `loopback` | `Interface.Equal` = `lo` | `PASS` |
| `arp` | `EtherType.Equal` = `arp` | `PASS` |
| `icmpv6-housekeeping` | `Protocol.Equal` = `icmpv6`, `IcmpType.Equal` = `130-137`, `143` | `PASS` |
| `dhcp-client` | `Protocol.Equal` = `udp`, `SrcPort.Equal` = `67`, `DstPort.Equal` = `68` | `PASS` |
| `dev-viewer-ports` | `Direction.Equal` = `in`, `Protocol.Equal` = `tcp`, `DstPort.Equal` = `8080`, `8081` | `PASS` |

Everything else inbound meets the backstop.

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
