---
title: The PNP viewer
type: concept
description: pnpd serves a live packet viewer on port 8081 of Experimental images — a web UI over a wire tap that sees every frame on every interface, both directions, from the machine's first packet.
related:
  - peios/networking/overview
  - peios/networking/the-net-command
---

Experimental editions run **pnpd**, the first piece of Peios Network Policy
(PNP): a wire tap with a web UI. Browse to port **8081** on a running machine
and you are looking at its network life, packet by packet — the DHCP handshake
it booted with, its neighbor discovery, every conversation it starts, live.

pnpd is development-phase tooling. It exists so the people building PNP (and
anyone curious) can *see* what the machine does on the wire before any policy
engine exists to govern it. Whether it survives into production editions, and
in what form, is a decision for when PNP ships.

## What it shows

Every frame on every interface, both directions, decoded in the browser:
Ethernet, ARP, IPv4/IPv6, TCP, UDP, ICMP, ICMPv6 (router and neighbor
discovery spelled out), DNS, DHCP and DHCPv6. Each packet expands into a
per-layer field view and a hex dump. Filter by protocol or free text; pause,
or follow the live tail.

An idle Peios machine is nearly silent, which makes the viewer a teaching
instrument: run one command in a console and watch its whole story — ARP,
resolution, handshake, teardown — appear as a handful of explainable lines.

## Honesty rules

The viewer never silently lies about the wire:

- **Drops are confessed.** If frames arrive faster than the tap can keep,
  the kernel's count of what was missed is shown in the header.
- **Its own traffic is counted, not vanished.** Serving the viewer generates
  packets; showing them would generate more, forever. pnpd excludes its own
  HTTP flow from the ring and shows how many frames that hid.
- **Placement is stated.** Inbound frames are captured before the IP stack
  touches them; outbound as handed to the driver — so outbound checksums may
  read as unfilled and offloaded frames as oversized. That is where the tap
  stands, not corruption.

## Reaching it

On QEMU user-mode networking, forward the port:
`make boot NET='-nic user,hostfwd=tcp:127.0.0.1:8080-:8080,hostfwd=tcp:127.0.0.1:8081-:8081'`,
or `drive.py --hostfwd tcp:127.0.0.1:8081-:8081`, then open
`http://localhost:8081`.
