---
title: Network policy
type: guide
description: Check active firewall policy, make a narrowly scoped change safely, verify acceptance and connectivity, and understand the rule behavior needed to troubleshoot it.
related:
  - peios/networking/overview
  - peios/networking/network-policy-reference
  - peios/networking/the-pnp-viewer
---

Use Peios Network Policy (PNP) to decide which connections the machine
allows and which interfaces join a network. Settings are registry keys
under `Machine\System\Network`; there is no `iptables` configuration.
The kernel's Network Traffic Filtering Engine (NTFE) enforces packet
policy, while netd applies interface rules and profiles.

For desktop changes, open [Network Manager](~peios/networking/network-manager)
and use **Rules** or **Profile rules**. The
[policy reference](~peios/networking/network-policy-reference) lists exact
values and examples. Experimental also includes the
[PNP viewer](~peios/networking/the-pnp-viewer), with important access risks.

## Check and change policy safely

1. **Identify the symptom.** For a service that cannot be reached, confirm
   that it is listening and has permission to bind its port. A firewall
   allow does not create a listener or grant a port reservation.
2. **Check what is active.** As an administrator, run `net policy` to see
   enforcement, generation and refusals. Use `net status` separately for
   interface rules. A refused update leaves the previous accepted policy
   active.
3. **Preview the smallest change.** In Network Manager, use **Test a
   connection** and **What this changes**. Its firewall exposure and
   activity displays currently include labeled example data; a preview is
   not evidence that a real connection worked.
4. **Keep a recovery path.** Record the old rule values and retain local
   access before changing the path used by a remote session. A rule or
   network-label change can cut an existing connection on its next packet.
5. **Apply, then verify.** After a registry edit, run `net policy wait`,
   then `net policy`, and test the intended connection. Check `net status`
   too if interface rules, profiles or network labels changed.

> [!WARNING]
> Policy writes apply live, without rebooting. Existing connections are
> re-judged; they are not exempt. Direct registry writes and the PNP viewer
> do not provide Network Manager's documented 30-second keep/undo flow.
> Read [Making a change](~peios/networking/network-manager#making-a-change)
> before relying on that recovery mechanism.

`net policy` and `net policy wait` require access to the kernel device;
ordinary users cannot open it. Editing rules requires registry write
access. A successful write is not yet proof that the kernel ingested it;
`net policy wait` fails on a refused generation or timeout.

## Rules are keys

A rule's path identifies it in diagnostics, such as
`no-inbound/ssh-from-lan`. Its values specify:

- **Conditions:** `<Fact>.<Operator>` values, such as `DstPort.Equal = 22`.
  Every condition must hold. A rule with no conditions matches everything.
- **Actions:** a list such as `PASS`, `DROP`, `REJECT(Prohibited)` or
  `COUNT(dns)`.
- **Priority:** a number, inherited by children and defaulting to 0 at a
  root. `Enabled = 0` disables a rule and its entire subtree.

Create a child key for an exception. The child must satisfy its parent's
conditions as well as its own, so `no-inbound` can drop inbound traffic
while a child allows SSH from a particular subnet. Order in the editor or
registry does not decide which rule wins. Independent rule trees compete
by priority and strictness, allowing local and organization policy to
coexist without merging their trees.

## Three layers, and a fourth

Choose the layer for the question you need to answer:

| Layer | Use it for |
|---|---|
| `Rules\Flow` | Who may connect to what. Most service and port policy belongs here. A flow is a TCP connection, UDP exchange or tracked ICMP echo exchange. |
| `Rules\Packet` | Conditions that must be checked per packet. The baseline passes tracked traffic here and leaves connection decisions to `Flow`. Untracked traffic is decided here. |
| `Rules\RawPacket` | Wire-side frame rules before connection tracking on ingress. Usually unnecessary for host access policy. |
| `Rules\Interface` | Which profile an interface uses, or whether netd leaves it alone or keeps it down. |

Allowing a flow does not override a drop in another layer. A fact absent
at a layer cannot make its condition match. Check the
[layer table](~peios/networking/network-policy-reference#layers) before
moving a rule between layers.

The kernel's exact inbound/outbound order, bridge and non-IP fallback
checks, and untracked-packet handling are in
[Seats and dispatch](~peios/advanced-peios/peios-kernel/ntfe/seats-and-dispatch).

## Flows and sentences

A **sentence** is the flow's cached verdict. Normally the first packet
is judged and later packets use it. The rule's direction is the
originator's: a connection this machine opened remains `out`, including
its replies.

Two changes can trigger a fresh judgment:

- **Policy or network context changes.** The next packet is judged against
  the new generation. A newly forbidden existing connection stops then;
  `REJECT` on an established TCP connection tears down both ends.
- **A consulted `Time.*` condition changes.** `Time.Hour.Equal = 9-17`
  can stop an existing connection at 18:00 UTC, on its next packet. Use
  `Start.Hour` if only new connections should be restricted; it is fixed
  for the flow's life.

A loopback flow has two local endpoints and two judgments. Both must
allow it. `COUNT` and `REPORT` effects at this layer run when a flow is
judged, including a re-judgment, rather than on every packet.

See [The Flow layer](~peios/advanced-peios/peios-kernel/ntfe/the-flow-layer)
for caching, time expiry and the cases where no sentence can be retained.

## Who is speaking

Use `Flow` identity facts for a local program or service. For example,
`Local.Service.Equal = resolvd` with `DstPort.Equal = 53` matches the
resolver service's traffic to that port. Identity comes from the native
token stamped on the socket, not a program path or a claimed name.

`Local.User.Present = 0` means no attributable program user is present.
The endpoint can instead be the kernel, a shared receiver or no listener.
On loopback, `Remote.*` also describes the other local endpoint. Check the
PNP viewer's **Listeners** and **Flows** when a service rule does not
match; an unresolved identity is reported rather than guessed.

[The identity facts](~peios/advanced-peios/peios-kernel/ntfe/the-identity-facts)
describes socket stamping and exactly when each identity is available.

## Joining a network

For addresses and routes, use [Configuring profiles](~peios/networking/configuring-profiles).
An interface is the hardware or virtual link; the network is what is on
the other side. The address, route, DNS and hostname it offers are claims,
not verified trust.

An interface rule selects by `Interface.Kind`, `Interface.Path`,
`Interface.Id`, or an identified network's `Name` and `Trust`. Its verdict
is `JOIN(profile)`, `IGNORE` or `DOWN`; no matching verdict leaves the
interface ignored. Each interface has one profile or one of those other
outcomes. Profiles contain settings, while rules contain the selection.

A child profile inherits all parent values and replaces what it names.
A bare profile accepts no offers; the shipped `default` profile supplies
the friendly wired defaults. Network-dependent profile examples describe
selection once the link and identity exist, not Wi-Fi association, which
remains unfinished.

The interface and firewall read the same network labels, so naming or
reclassifying a network can change both. Identification is not proof:
writing `Trust = home` is your decision to accept that identification.
netd's protected `Status` records report its findings; do not edit them.

netd and the kernel accept their own layers independently. A missing
`JOIN` target can leave netd on its last good configuration while firewall
changes still apply. DHCP and router discovery also need ordinary PNP
allows; the baseline's rules are visible and deletable.

The [interface-layer chapters](~peios/advanced-peios/netd/the-interface-layer/profiles)
cover parsing, generation validation, judgment and reconciliation.

## Verdicts and effects

| Action | What the operator or peer sees |
|---|---|
| `PASS` | This layer allows the traffic; other layers can still refuse it. |
| `DROP` | Silent refusal, usually seen as a timeout. |
| `REJECT` or `REJECT(Refused)` | An explicit refusal, like no listener: TCP reset or ICMP port-unreachable. |
| `REJECT(Prohibited)` | An explicit policy refusal: ICMP admin-prohibited. |
| `NULL` | No decision; an ancestor, another tree or the backstop decides. |

`REJECT` works inbound and outbound. An outbound refusal can fail the local
operation promptly instead of leaving it to time out. Where no refusal
can be sent, it degrades to a counted drop; see
[Where a REJECT can speak](~peios/networking/network-policy-reference#where-a-reject-can-speak).

Effects do not grant access. `TAG` marks a flow, `COUNT` contributes to a
counter stream, and `REPORT` writes an audit event at its configured level.
`PROMPT` currently has no handler transport and takes its fallback
immediately. A rule containing only effects abstains from the verdict.

## The laws

Use these checks when a rule behaves unexpectedly:

- **Backstop:** an ingested empty packet forest drops everything, attributed
  to `backstop`; the interface backstop is `IGNORE`. Before any policy is
  loaded, generation 0 is permissive and reported as such.
- **Absent facts:** a condition on a missing fact is false, including
  missing tags and counter cells. `Present` is the explicit existence test.
- **Exceptions:** a matching child shadows its parent within that tree.
  Trees never shadow one another.
- **Abstention:** a triggered rule without a verdict hands the decision to
  the nearest ancestor with a direct verdict. That ancestor's full action
  list runs once; intervening abstainers do not run.
- **Priority:** highest wins. At equal priority, `DROP` beats `REJECT`
  beats `PASS`, and `Refused` beats `Prohibited`. An interface's verdict
  order is `DOWN`, `IGNORE`, `JOIN`; conflicting profile selections need
  correction rather than relying on rule order.
- **Effects:** triggered rules' effects run even when another rule wins.
  Matching uses the snapshot from before those writes. A count does not
  affect the same evaluation's threshold; a later packet can see it.
- **Whole generations:** malformed packet policy keeps the previous
  generation active. A registry write returning is not acceptance; run
  `net policy wait` before depending on the new rule.
- **Tags:** reads can only go upward through `RawPacket` < `Packet` <
  `Flow`. Downward reads are refused. Tags remain on a flow across policy
  changes.
- **Flow scope:** a flow is judged per local endpoint, then cached until
  a policy change or consulted time condition makes it stale. Loopback
  has two endpoints.
- **Refusals:** PNP does not filter its own generated refusal packets.
  Ordinary traffic, including echo, has no such bypass.

The full [evaluation algorithm](~peios/advanced-peios/peios-kernel/ntfe/evaluation),
[generation ingestion](~peios/advanced-peios/peios-kernel/ntfe/ingestion-and-generations)
and [stores](~peios/advanced-peios/peios-kernel/ntfe/the-stores) belong in
the kernel technical reference; the [reference](~peios/networking/network-policy-reference)
keeps the authoring vocabulary and limits.

## Rate limiting without a throttle verb

PNP expresses a rate limit using a count, a view of that count, and a
verdict. This example observes DNS queries and rejects queries from a
source whose preceding count exceeds the threshold:

```text
Rules\Packet\dns-watch     Protocol.Equal = udp, DstPort.Equal = 53
                           Actions = COUNT(dns)
Rules\Packet\dns-flood     Protocol.Equal = udp, DstPort.Equal = 53
                           Counter.dns(10s, SrcAddr).GreaterThan = 20
                           Actions = REJECT(Prohibited)
```

`dns-watch` counts and abstains. `dns-flood` reads the ten-second view
before the current packet's count lands. Windows are approximations;
check the [counter view](~peios/networking/network-policy-reference#counter-views)
and its observed counts rather than treating this as an exact throttle.
As counts age out, the condition stops matching.

> [!WARNING]
> Keep the protocol and port conditions on the gated verdict. Without
> them, the rule can refuse every packet from a source whose DNS count
> crossed the threshold, including traffic for your remote session.

## Where things are visible

- `net status`: interface verdict, selected rule/profile and refusal.
- `net policy` and `net policy wait`: kernel acceptance and enforcement.
- [Network Manager](~peios/networking/network-manager): configuration and
  connection tests; read its **Example data** disclosures for firewall
  displays.
- [PNP viewer](~peios/networking/the-pnp-viewer): live verdict attribution,
  flows, listeners and counter tables on Experimental, with its safety
  warning observed.
- [Event Viewer](~peios/logs-and-events/event-viewer):
  `ntfe.verdict.reported` events requested by `REPORT` effects.

A packet using a cached sentence has no new evaluation event. Missing
events are not proof that traffic passed; check the sentence and surfaced
drop/refusal counters. The [event-stream chapter](~peios/advanced-peios/peios-kernel/ntfe/the-event-stream)
describes the kernel records and loss accounting.
