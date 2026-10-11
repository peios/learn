---
title: The PNP viewer
type: guide
description: Reach the Experimental PNP viewer safely, find live listener and firewall evidence, and verify policy changes without confusing captured frames with delivered traffic.
related:
  - peios/networking/overview
  - peios/networking/the-net-command
---

Experimental editions run **pnpd**, the observation and authoring surface of
Peios Network Policy (PNP). Browse to port **8081** on a running machine and
you are looking at its network life five ways at once: every frame on the
wire, the firewall engine's verdict on every evaluation, the policy that
produced those verdicts — editable in place — every live flow with the
sentence the flow layer gave it, and the counters that policy is keeping.

pnpd is development-phase tooling, and deliberately *not* part of
enforcement: the kernel reads its policy from the registry itself. pnpd
watches, explains, and writes the registry like any other author.

The Experimental edition is a development-machine image, not a production
deployment profile. Its pnpd service listens on every interface and does not
authenticate viewers; a viewer can inspect captured traffic and change network
policy. Run it only on a trusted development network, and expose port 8081 to
the host through a loopback-only forward. Do not deploy the Experimental image
or expose pnpd to an untrusted network.

## Reaching it

On QEMU user-mode networking, forward the port:
`make boot NET='-nic user,hostfwd=tcp:127.0.0.1:8081-:8081'`,
or `drive.py --hostfwd tcp:127.0.0.1:8081-:8081`, then open
`http://localhost:8081`.

## Start with the question

| Question | Where to look |
|---|---|
| Did my firewall edit take effect? | Check enforcement, generation and any refusal banner in the header, then the **Policy** tab. |
| Is this service actually listening, and as whom? | **Listeners** shows the native owner stamp the Flow layer uses. |
| Which rule allowed or blocked this connection? | **Flows** shows the cached sentence and its rule; **Wire** shows individual evaluation badges. |
| Why is there no packet beside a drop? | An outbound drop can occur before the transmit tap; the verdict is still shown as its own row. |
| Did a rate-limit rule count what I expected? | **Counters**, including refusal counts and window approximation. |

After narrowing the interface, protocol, address or port, compare the flow's
rule with the policy and the native listener identity. Do not infer delivery
from a captured packet alone. Read [Honesty rules](#honesty-rules) before
treating a missing frame or badge as evidence.

> [!WARNING]
> Editing here writes live registry policy and can cut off this viewer or
> another remote session. Keep the old rule values and a local recovery
> path. The viewer does not document Network Manager's keep/undo countdown.
> After a save, check the generation or refusal banner and test the intended
> connection; an administrator can also use `net policy wait`.

## The wire tab

Every frame on every interface, both directions, decoded in the browser:
Ethernet, ARP, IPv4/IPv6, TCP, UDP, ICMP, ICMPv6 (router and neighbor
discovery spelled out), DNS, DHCP and DHCPv6. Each packet expands into a
per-layer field view and a hex dump; filter by protocol or free text.

Packets carry a **verdict badge** — PASS, DROP, or REJECT — painted from
the engine's own event stream (`/dev/peios-ntfe`), never inferred: each badge
names the rule that decided, as a registry path like
`no-inbound/ssh-from-lan`, plus the layer and standing seat. A REJECT badge
also names the story it told the sender: `REJECT·Refused` (nothing is
listening — a TCP reset or ICMP port-unreachable) or `REJECT·Prohibited`
(policy refused you — ICMP admin-prohibited). A verdict with no matching tap
packet renders as its own row, slotted into the timeline by its timestamp —
for an outbound drop that row is the only possible trace, because the
transmit tap stands after the filter and never saw the packet.

A packet answered by a flow's cached sentence carries no badge of its own:
there was no evaluation. The sentence is on the flows tab.

The header shows the engine itself: the policy **generation**, whether it is
**enforcing** (generation 0 boots loudly permissive), the running
pass/drop/reject counts, and the machinery stores' own accounting — tag
writes, counter emissions, reports emitted to the KMES event stream, live
counter cells, the active reporting level, flows judged, and refusals
sent. Hover a count for what the store *refused* or what it did instead
(a flow past its tag tripwire, a table at its key cap, a packet lacking a
view's key fact, packets answered from a cached sentence, flows re-judged
after a policy change or at a time edge, a REJECT with nothing to send):
refusals are counted, never silent. A failed policy ingestion shows as a
banner: the previous generation stays active. Correct the named failure
and verify a new generation rather than assuming the saved edit is active.

## The policy tab

The rule forest under `Machine\System\Network\Rules`, rendered as nested
cards: conditions, actions, priority, exceptions indented under their
parents. Rules can be edited, given exceptions, created, and deleted in
place; every save commits in one registry transaction, the kernel re-walks
the subtree, and the generation bump — or the refusal — appears in the
header within a second. The backstop is compiled-in DROP, so everything in
the tree is a visible, deletable permissive statement.

## The flows tab

Each flow shows its **owner**: the program at this machine's end —
its comm and pid, and the service or principal it runs as — or what
stood there instead (the kernel, a shared receiver, nobody). A loopback
flow shows both ends. Service names are resolved from the service
definitions in the registry; a SID the viewer cannot name is shown as
is. Hover a verdict badge to see the same for the judgment that
produced it.

Every flow conntrack is tracking, refreshed while the tab is open: the
protocol and both ends (originator first), which side opened it, the
interface it was judged on, conntrack's state and remaining lifetime, the
flow's age, packets and bytes in each direction, and the flow layer's
**sentence** — the cached verdict, the rule that gave it (resolved from
the policy by the same hash the kernel keys it by), the generation that
judged it, and a ⏱ when a consulted time condition will expire it. A
loopback flow shows two sentences, one per local endpoint. Tags the flow
carries are listed by name where the policy mentions them.

A missing sentence can mean permissive operation or no Flow policy, but it
can also mean the kernel could not allocate storage for the sentence and
judges each packet instead. Check `flow_uncached`; see
[The Flow layer](~peios/advanced-peios/peios-kernel/ntfe/the-flow-layer).

## The listeners tab

What the machine is prepared to receive right now, without waiting for
a packet: every TCP socket that is listening and every UDP socket that
is bound, by protocol, address and port, with the program that owns it
— comm, pid, and the service or principal it runs as — or "kernel" for
a socket the kernel opened. Wildcards show as `*`; a member of a
`SO_REUSEPORT` group is marked as one. This is the attack surface as a
list, and the first place to look when a rule about a service does not
match: the stamp shown here is the one the Flow layer will read.

## The counters tab

Every cell of every counter table the policy materialized, refreshed while
the tab is open. `COUNT(name)` in a rule emits into a stream; every
`Counter.name(window, key)` some rule reads is a table here — one block per
(stream, key), one row per key the wire has produced, one column per window
the table answers plus the cumulative total and the age of the last write.
Windows are eight-bucket sliding approximations, so a value can run up to
an eighth of a window stale. A stream nobody views has no table and nothing
to show.

## Honesty rules

The viewer never silently lies:

- **Drops are confessed** — both the tap's kernel drop count and the
  verdict ring's overwrite count are surfaced.
- **Its own traffic is counted, not vanished.** pnpd excludes its own HTTP
  flow from the packet ring and shows how many frames that hid. The viewer
  description says its verdicts remain visible, while the kernel manual's
  [event-stream chapter](~peios/advanced-peios/peios-kernel/ntfe/the-event-stream)
  says pnpd hides and counts its own-port verdict events too. Do not rely on
  complete visibility of the viewer's own connection when diagnosing it.
- **Placement is stated.** Inbound frames are captured before the IP stack;
  outbound as handed to the driver. Verdicts come from the engine's seats,
  which stand elsewhere — the two views disagreeing is a diagnostic, not a
  bug to hide.
