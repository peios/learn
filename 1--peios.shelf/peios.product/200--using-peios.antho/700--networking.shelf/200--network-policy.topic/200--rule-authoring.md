---
title: Network Rule Authoring
type: reference
description: Shared condition and action syntax for interface and packet policy, with links to each executor's contract.
---

Rule paths live beneath `Machine\System\Network\Rules`. `Interface` belongs
to netd; `RawPacket`, `Packet`, and `Flow` belong to NTFE. Each executor can
accept or refuse its own generation independently. A successful registry
write is not an acknowledgment from either executor.

A rule's name identifies it in diagnostics and cannot contain path separators.
Its conditions are ANDed. A matching child specializes its parent's matched
region. Priority inherits from the parent, or defaults to zero at a root.
An empty action list abstains; `Enabled = 0` disables the subtree.

## Conditions

Condition names have the form `<Fact>.<Operator>`. Missing facts do not match,
except through an explicit presence test. Integer operands accept documented
numeric types or decimal text; integer lists accept ranges. Unsupported
operator/type combinations reject the generation.

| Operator | Families | Value |
|---|---|---|
| `Equal` | all | Membership: a scalar, or a list (`REG_MULTI_SZ`) meaning *any of*. Integers accept `a-b` ranges; addresses accept CIDR prefixes and (IPv4) `a-b` ranges. |
| `GreaterThan` | integer | A single integer; strictly greater. |
| `LessThan` | integer | A single integer; strictly less. |
| `Has` | flags | A flag name or list; all listed bits set. |
| `Hasnt` | flags | A flag name or list; all listed bits clear. |
| `Present` | all, and `Tag.<name>` / `Counter.<name>` | `1`: the fact exists for this packet or flow; `0`: it does not. The one operator that looks through the absent-fact law. On a fact its layer never has, it refuses the generation rather than becoming an always-true condition. |

### Fact vocabulary

Availability depends on the layer and the actual subject. A condition using
an unavailable fact cannot make a connection pass. A `Present` test for a
fact that the layer never supplies is rejected. Native endpoint identity
comes from the socket's effective-identity stamp, not a name supplied by the
application.

| Fact | Family | Values | Present when |
|---|---|---|---|
| `Direction` | string | `in`, `out` | always. `Flow`: the originator's side, for the flow's whole life |
| `Interface` | string | interface name, for example, `eth0` | always. `Flow`, outbound: the route's device |
| `EtherType` | integer | number, or `ipv4`, `ipv6`, `arp` | always. Not a `Flow` fact (a flow's family is its addresses') |
| `SrcMac` | MAC | `aa:bb:cc:dd:ee:ff` | frame has an Ethernet header; at the IP seats outbound, the machine's own device address |
| `DstMac` | MAC | `aa:bb:cc:dd:ee:ff` | frame has an Ethernet header. Not a `Flow` fact |
| `Vlan` | integer | VLAN id | the frame is VLAN-tagged (device seats) or the interface is a VLAN device (IP seats) |
| `SrcAddr`, `DstAddr` | address | exact (`10.0.0.5`, `fd00::1`), CIDR (`10.0.0.0/8`, `fd00::/64`), IPv4 range (`10.0.0.1-10.0.0.99`) | IP packet |
| `Protocol` | integer | number, or `tcp`, `udp`, `icmp`, `icmpv6`, `sctp` | IP packet |
| `Ttl` | integer | TTL / hop limit | IP packet. Not a `Flow` fact |
| `Dscp` | integer | 0..63 | IP packet. Not a `Flow` fact |
| `Fragment` | integer | `0` or `1` | IP packet (only ever 1 before defragmentation, that is, at the RawPacket seat). Not a `Flow` fact |
| `SrcPort`, `DstPort` | integer | 0..65535 | TCP, UDP, or SCTP |
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
| `Interface.Path` | string | bus position, for example, `pci-0000:00:03.0` | `Interface` layer only; it is hardware |
| `Interface.Driver` | string | kernel driver | `Interface` layer only; it is hardware |
| `Network.Id` | string | the network record's key name under `Networks\` | every layer: a network has been identified on the interface the packet crossed (see [the network context](~kernel/internals/ntfe/authoring-packet-rules)) |
| `Network.Name` | string | the operator's `Name` on the record | every layer; the record has one |
| `Network.Trust` | string | the operator's `Trust` on the record | every layer; the record has one |
| `Network.Kind` | string | the `Interface.Kind` the network was seen on | `Interface` layer; a network has been identified |
| `Tag.<name>` | integer | the flow tag's value | the flow carries the tag (`Packet` and `Flow` layers; never `RawPacket`) |
| `Counter.<name>[(...)]` | integer | a counter view, see below | the packet has the view's key facts and a cell exists |

## Actions

Names are case-insensitive. An action list can combine effects and a verdict;
effects do not themselves authorize traffic. Unknown expressions or invalid
operands reject the generation. `PROMPT` has no handler transport in the
implemented engine and applies its fallback immediately.

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
| `TAG(Name, Clear)` | effect | Remove the tag; it reads as absent afterward. |
| `COUNT(Name[, n])` | effect | Emit `n` (default 1) into stream `Name`. |
| `COUNT(Name, Length)` | effect | Emit the packet's byte length — the bandwidth primitive. |
| `REPORT(level)` | effect | Emit an `ntfe.verdict.reported` audit event, level 1..5, if the level clears `CurrentReportingLevel`. One report per rule per evaluation, at the highest level listed. |
| `JOIN(profile)` | verdict, `Interface` layer | Bring the interface up and stand in the named profile: a path under `Profiles\`, using either path separator. |
| `IGNORE` | verdict, `Interface` layer | Never touch the interface; something else owns it. |
| `DOWN` | verdict, `Interface` layer | Keep the interface administratively down. |

Interface actions are limited to its verdicts, `NULL`, and `REPORT`.
`JOIN` requires an existing profile; a disabled profile causes abstention.
Conflicting equal-priority profile choices have special startup/reload
handling in [netd's judgment
reference](~peios/reference/netd/the-interface-layer/judging-an-interface).

## Counter and tag references

`Counter.<name>(window, key)` reads a stream written by `COUNT`. A window is
seconds, minutes, hours, or days, at most one day; omission selects a
cumulative total. A key selects `SrcAddr`, `DstAddr`, `Interface`, or a
`+`-joined combination; omission selects a global cell. For example,
`Counter.dns(10s, SrcAddr)` reads a per-source ten-second view.

A view requires some rule to write its stream. Sliding windows use eight
buckets and can be stale by an eighth of a window. Matching reads the state
before the current evaluation's effects, so a count does not affect its own
threshold check. Missing cells and tags remain absent, rather than reading
as zero in every condition.

Tag dependencies can only flow upward through `RawPacket`, `Packet`, and
`Flow`; downward dependencies reject the generation. Tags survive policy
generation changes. The kernel's [store
reference](~kernel/internals/ntfe/the-stores) owns capacity, lifetime, and
refusal accounting.

## Executor references

| Question | Owning reference |
|---|---|
| Profile values, inheritance, and accepted offers | [Configuring Profiles](~peios/network-configuration/configuring-profiles) and netd's registry manual |
| Interface fact and action rules | [Interface judgment](~peios/reference/netd/the-interface-layer/judging-an-interface) |
| Packet seat order and available facts | [Seats and dispatch](~kernel/internals/ntfe/seats-and-dispatch) and [snapshot](~kernel/internals/ntfe/the-snapshot) |
| Validation, rule limits, and reporting level | [Policy ingestion](~kernel/internals/ntfe/policy-ingestion-and-validation) |
| Priority, abstention, and effects | [Evaluation](~kernel/internals/ntfe/evaluation) |
| Cached verdicts, time changes, and refusals | [Flow layer](~kernel/internals/ntfe/the-flow-layer) |
| Native endpoint identity | [Identity facts](~kernel/internals/ntfe/the-identity-facts) |

Image seeds add ordinary, deletable rules; this reference does not promise
which services an image exposes. DHCP and router discovery need policy too.
Inspect installed rules and their accepted generation before changing them.
For worked packet-policy patterns, see [Authoring Packet
Rules](~kernel/internals/ntfe/authoring-packet-rules).
