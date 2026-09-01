---
title: The PNP viewer
type: concept
description: pnpd serves the PNP viewer on port 8081 of Experimental images — the wire, the engine's verdicts, the policy editor, and the counter store, live.
related:
  - peios/networking/overview
  - peios/networking/the-net-command
---

Experimental editions run **pnpd**, the observation and authoring surface of
Peios Network Policy (PNP). Browse to port **8081** on a running machine and
you are looking at its network life four ways at once: every frame on the
wire, the firewall engine's verdict on every evaluation, the policy that
produced those verdicts — editable in place — and the counters that policy
is keeping.

pnpd is development-phase tooling, and deliberately *not* part of
enforcement: the kernel reads its policy from the registry itself. pnpd
watches, explains, and writes the registry like any other author.

## The wire tab

Every frame on every interface, both directions, decoded in the browser:
Ethernet, ARP, IPv4/IPv6, TCP, UDP, ICMP, ICMPv6 (router and neighbor
discovery spelled out), DNS, DHCP and DHCPv6. Each packet expands into a
per-layer field view and a hex dump; filter by protocol or free text.

Packets carry a **verdict badge** — PASS, DROP, or REJECT — painted from
the engine's own event stream (`/dev/peios-pnp`), never inferred: each badge
names the rule that decided, as a registry path like
`no-inbound/ssh-from-lan`, plus the layer and standing seat. A REJECT badge
also names the story it told the sender: `REJECT·Refused` (nothing is
listening — a TCP reset or ICMP port-unreachable) or `REJECT·Prohibited`
(policy refused you — ICMP admin-prohibited). A verdict with no matching tap
packet renders as its own row, slotted into the timeline by its timestamp —
for an outbound drop that row is the only possible trace, because the
transmit tap stands after the filter and never saw the packet.

The header shows the engine itself: the policy **generation**, whether it is
**enforcing** (generation 0 boots loudly permissive), the running
pass/drop/reject counts, and the machinery stores' own accounting — tag
writes, counter emissions, reports emitted to the KMES event stream, live
counter cells, and the active reporting level. Hover a count for what the
store *refused* (a flow past its tag tripwire, a table at its key cap, a
packet lacking a view's key fact): refusals are counted, never silent. A
failed policy ingestion shows as a banner — the previous generation stays
active, and the banner says so.

## The policy tab

The rule forest under `Machine\System\Network\Rules`, rendered as nested
cards: conditions, actions, priority, exceptions indented under their
parents. Rules can be edited, given exceptions, created, and deleted in
place; every save commits in one registry transaction, the kernel re-walks
the subtree, and the generation bump — or the refusal — appears in the
header within a second. The backstop is compiled-in DROP, so everything in
the tree is a visible, deletable permissive statement.

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
  flow from the packet ring and shows how many frames that hid; its
  verdicts still appear, attributed like everyone else's.
- **Placement is stated.** Inbound frames are captured before the IP stack;
  outbound as handed to the driver. Verdicts come from the engine's seats,
  which stand elsewhere — the two views disagreeing is a diagnostic, not a
  bug to hide.

## Reaching it

On QEMU user-mode networking, forward the port:
`make boot NET='-nic user,hostfwd=tcp:127.0.0.1:8080-:8080,hostfwd=tcp:127.0.0.1:8081-:8081'`,
or `drive.py --hostfwd tcp:127.0.0.1:8081-:8081`, then open
`http://localhost:8081`.
