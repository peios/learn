---
title: Network policy
type: concept
description: How Peios Network Policy (PNP) decides what a packet may do — rules as registry keys, a forest of trees, verdicts and effects, and the laws an author can rely on.
related:
  - peios/networking/overview
  - peios/networking/network-policy-reference
  - peios/networking/the-pnp-viewer
---

Peios Network Policy (PNP) is the machine's packet filter, and it is
configured the way everything else on Peios is: as registry keys. There
is no rule language file, no `iptables`-style command, and no daemon in
the path — the kernel reads its policy from
`Machine\System\Network\Rules` itself, and every change there becomes a
new **policy generation** within a fraction of a second. The
[PNP viewer](../500--the-pnp-viewer.md) is the place to watch that
happen and to write rules by hand; the
[reference](../420--network-policy-reference.md) lists every fact,
operator and action.

## Rules are keys

A rule is a registry key. Its **name** is its identity — the kernel
attributes every decision to the rule that made it, as a path like
`no-inbound/ssh-from-lan`. Its **values** are its match and its
standing:

- Every value named `<Fact>.<Operator>` is a **condition** — `DstPort.Equal`
  = `22`, `SrcAddr.Equal` = `10.0.0.0/8`, `FlowState.Equal` =
  `established`. A rule matches a packet when *all* of its conditions
  hold. A rule with no conditions matches everything.
- `Actions` is a list of action expressions — `PASS`, `DROP`,
  `REJECT(Prohibited)`, `COUNT(dns)`, `REPORT(3)`, and so on.
- `Priority` is a plain integer (default 0, inherited by subkeys) used to
  collate competing verdicts. `Enabled` = `0` switches a rule and
  everything beneath it off.

**Subkeys are exceptions.** A subkey carves a narrower region out of its
parent: `no-inbound` (`Direction.Equal` = `in`, `DROP`) with a subkey
`ssh` (`DstPort.Equal` = `22`, `PASS`) drops all inbound traffic except
SSH. A child only ever matches a subset of what its parent matches,
because it is judged with its parent's conditions and its own.

The rules under one layer key form a **forest**: any number of
independent trees, in no particular order. Order carries no meaning
anywhere in PNP — two trees that both match a packet are reconciled by
priority and strictness, never by which came first. That is what lets
policy from different sources (a local rule, an organisation's Group
Policy) coexist without merging.

## Three layers

Rules live under one of three layer keys, and a packet meets them in
order:

- `Rules\RawPacket` — the wire-side escape hatch. Judged at the device
  seats for *all* traffic, before conntrack on the way in; it sees
  frames, not flows. Most policy never needs it.
- `Rules\Packet` — the per-packet layer. Every traversal is judged here
  exactly once, at its richest point: inbound IP after conntrack has
  classified the flow, outbound as the frame leaves. It is the cheap
  filter in front of the flow layer: the shipped policy passes every
  tracked packet here and leaves the decisions to `Flow`.
- `Rules\Flow` — the flow layer. A **flow** is what conntrack tracks: a
  TCP connection, a UDP exchange, an ICMP echo and its reply. The flow
  layer judges each flow **once**, on its first packet, and remembers the
  verdict on the flow as its **sentence**; every later packet of the
  flow, in either direction, reads the sentence instead of being judged.
  This is where policy about *who may connect to what* lives, and where
  it stays cheap: a rule here runs once per connection, not once per
  packet.

Traffic that will never reach the packet layer's proper seat — non-IP
frames such as ARP, or frames on a bridge-enslaved port — is judged by
the packet layer at the device seat instead, so nothing escapes it.
Traffic conntrack does not track (a stray reply, an out-of-window
segment) never reaches the flow layer; the packet layer's verdict is its
last word.

## Flows and sentences

The flow layer's facts are the ones that are the same for every packet
of the flow — addresses, ports, protocol, direction, interface, VLAN —
plus two of its own: `Related` (the flow was expected by another, like
an FTP data connection) and `Start.*`, the wall clock at the moment the
flow began. `Direction` is the originator's side: a flow your machine
opened is `out` for its whole life, replies included.

A sentence answers for the flow until one of two things makes it stale.
**The policy changes**: a new generation re-judges every flow on its
next packet, so a rule that now forbids a running connection cuts it
then — with a TCP reset, if the rule says `REJECT`. PNP does not
grandfather old connections past a new policy; the registry always says
what is enforced. **The clock moves**: a rule that consulted `Time.Hour`
(matched or not — a higher-priority rule that missed only on the hour
may match later) makes the sentence expire at the moment that condition
would next flip, and the flow is re-judged then. So `Time.Hour.Equal` =
`9-17` → `PASS` cuts a connection at 18:00, on its next packet. If you
mean *no new connections after 18:00, existing ones may finish*, write
`Start.Hour` instead: it is fixed for the flow's life and never expires
a sentence.

Two endpoints, two sentences: a loopback flow is both an outbound
connection from one local program and an inbound one to another, so the
flow layer judges it twice, once as `out` and once as `in`, and the flow
lives only if both said `PASS`.

## Verdicts and effects

Actions come in two species. **Verdicts** decide the packet's fate:
`PASS` (this layer approves), `DROP` (refuse silently), and `REJECT`
(refuse and tell the sender). A `REJECT` names the story it tells:
`REJECT(Refused)` — the default — looks like nothing is listening (a TCP
reset or ICMP port-unreachable); `REJECT(Prohibited)` admits that policy
refused the packet (ICMP admin-prohibited). PNP never impersonates a
routing failure: when it speaks, it does not speak falsely, and `DROP` is
the option for saying nothing. A refusal is sent from every layer and in
both directions: an outbound `REJECT` fails the local program's connect
at once with *connection refused* or *host unreachable*, instead of
leaving it to time out. Only a protocol with no refusal vocabulary (ARP,
other non-IP frames) drops instead, and says so in the event.

In the flow layer, a verdict applies to the whole flow: a `DROP` or
`REJECT` sentence refuses every later packet of it too, and effects run
when the flow is judged, never per packet — `COUNT` there counts
connections, `REPORT` fires once per connection.

**Effects** never decide anything; they happen alongside whatever is
decided. `TAG` writes a named number onto the packet's flow, for later
packets of that flow to read. `COUNT` emits into a named counter stream,
which other rules read through windows and keys. `REPORT` emits an audit
event. `PROMPT` defers to a userspace handler (in this release no handler
transport exists, so a prompt takes its fallback immediately, and the
prompt is still visible as an effect). `NULL` does nothing at all — an
explicit abstention.

A rule with no verdict in its actions **abstains**: it is a pure observer
(`COUNT(dns), REPORT(3)` with nothing else is a perfectly good rule), and
the decision belongs to someone else.

## The laws

These hold without exception, and an author can lean on them.

**The backstop is DROP, compiled in.** If nothing in the forest yields a
verdict for a packet, it is dropped, and the drop is attributed to
`backstop`. Every permissive statement is therefore a visible, deletable
rule. An empty forest drops everything; a machine boots *without* any
policy loaded is loudly permissive (generation 0) until its first
generation ingests.

**A condition over a fact the packet does not have is false.** An ARP
frame has no `DstPort`; `DstPort.Equal` = `22` simply does not match it
— it does not error, and it does not match by accident. This is the
*absent-fact law*, and it applies to tags and counters too: a tag never
set, a counter cell that does not exist, a counter keyed by an address on
a packet with no address — all absent, all false.

**The most specific matching rule in a lineage speaks.** Within one tree,
a rule triggers only if it matches and none of its children match — a
matching child shadows its parent. Shadowing exists only within a
lineage; trees never shadow each other.

**An abstaining rule hands the decision up its own parentage.** If the
triggered rule yields no verdict, the decision walks up to the nearest
ancestor whose actions contain a direct verdict, and that ancestor
speaks for the region — executing its full action list once. Ancestors
in between execute nothing.

**Highest priority wins; ties go to the strictest verdict.** Among every
verdict yielded across the forest, the highest `Priority` wins. At equal
priority, `DROP` beats `REJECT` beats `PASS`; between two rejects the
quieter story (`Refused`) wins. Priority is inherited by subkeys unless
they set their own, and a root's default is 0.

**Side effects always execute.** Every triggered rule's effects run,
whether or not its verdict wins — an out-prioritised rule's `COUNT` and
`REPORT` still happen. Observation is not authority.

**Matching reads a snapshot taken before the rule ran.** Nothing a rule
writes is visible to the same evaluation's matching. A `COUNT` lands
after this packet's own reads, so a rule cannot trip its own threshold;
the *next* packet sees the new count. A `TAG` written on a request is
read on the reply of the same flow. This is temporal feedback, and it is
the only kind PNP allows.

**A generation is all or nothing.** The kernel validates the whole forest
before publishing it. A malformed rule, an unknown fact, an unminted
`REJECT` kind, or a counter view over a stream no rule writes refuses
the *entire* new generation — and the previous one stays in force,
loudly (the viewer shows a banner; the status reports the error). Policy
never half-applies.

**Tags flow upward only.** A layer reads tags written at or below its
own height (`RawPacket` < `Packet` < `Flow`): a `Flow` rule may read a
tag a `Packet` rule wrote, and the reverse is refused at ingestion. Tags
themselves live on the flow and survive policy changes.

**A flow is judged once per local endpoint.** The flow layer runs on a
flow's first packet and its sentence answers for the rest, until the
policy changes or a consulted time condition flips. A loopback flow has
two local endpoints and is judged twice.

**PNP does not judge its own refusals.** The reset or ICMP error a
`REJECT` sends passes every seat unjudged. An outbound rule can never
drop the refusal an inbound rule asked for, and the forged peer answer
that fails a local connect is not inbound traffic for the policy to see.

## Rate limiting without a throttle verb

PNP has no `THROTTLE`. Rate limiting is the pair `COUNT` + a counter
view + a verdict, each of which obeys the laws above:

```text
Rules\Packet\dns-watch     Protocol.Equal = udp, DstPort.Equal = 53
                           Actions = COUNT(dns)
Rules\Packet\dns-flood     Protocol.Equal = udp, DstPort.Equal = 53
                           Counter.dns(10s, SrcAddr).GreaterThan = 20
                           Actions = REJECT(Prohibited)
```

`dns-watch` emits every DNS query into the `dns` stream and abstains.
`dns-flood` reads that stream sliced ten seconds wide and keyed by source
address, and refuses the twenty-first query in any ten-second window
from one source. Because the count lands after the packet's own reads,
the refusal starts on the *next* packet, and because refused queries
slow the sender, the count decays and the window reopens — a throttle,
assembled from parts that each mean one thing.

**Scope a gated verdict to the traffic you mean.** `dns-flood` without
its `Protocol` and `DstPort` conditions would refuse *every* packet from
a source whose DNS count crossed the threshold — a machine-wide ban of
that source, including its replies to the machine you are administering
from. That is exactly what the rule says, and PNP will do it.

## Where things are visible

Every evaluation emits an event on `/dev/peios-pnp` carrying the verdict,
the attributing rule's path, the layer and seat, and how many effects
ran; the [viewer](../500--the-pnp-viewer.md) paints those onto the wire,
lists every live flow with its sentence, and shows the counter store
live. A packet answered by a cached sentence emits no event — there was
no evaluation — and is counted instead. `REPORT` effects become KMES
`network-report` events for the audit pipeline. Everything the stores
refuse — a flow past its tag tripwire, a counter table at its key cap, a
packet lacking a view's key, a refusal that could not be sent — is
counted and shown; nothing is silent.
