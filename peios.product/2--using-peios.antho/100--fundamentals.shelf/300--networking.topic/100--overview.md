---
title: Networking
type: concept
description: How a Peios machine gets onto a network — netd reconciles links, addresses, routes and DHCP to what the registry says; nothing else configures the network.
related:
  - peios/networking/configuring-profiles
  - peios/networking/name-resolution
  - peios/networking/the-net-command
  - peios/registry-concepts/overview
  - peios/services-and-jobs/overview
  - peios/registry-administration/regman
---

A Peios machine's network is described in the registry and made real by one service, **netd**. There is no `ifconfig` step, no interface file, no daemon-specific configuration format: what the network should be is written under `Machine\System\Network`, and netd keeps the kernel matching it.

This page explains the model. [Configuring profiles](~peios/networking/configuring-profiles) covers writing the configuration; [The net command](~peios/networking/the-net-command) covers looking at the result.

## The registry is the truth

netd is a **reconciler**. It reads the desired state — profiles from the registry, plus whatever leases its DHCP clients currently hold — compares it with what the kernel reports over rtnetlink, and applies the difference. It does this on start, whenever the kernel reports a change (a cable plugged in, an interface appearing), whenever the registry changes, and whenever a DHCP lease arrives or expires.

Two consequences follow, and both are deliberate:

- **A manual change to a managed interface is reverted.** Adding an address by hand lasts until the next reconcile. The way to change the network is to change the registry.
- **Restarting netd changes nothing visible.** It re-derives the same desired state, finds the kernel already matches, and does nothing. Interfaces do not flap.

netd owns what it configured and nothing else. Addresses on a managed interface are all netd's; routes are netd's only when they carry its routing-protocol tag, so a route another program adds for itself is left alone.

## Profiles match interfaces

Configuration is not written per interface, because interface names are not stable across kernels and an image is built before its hardware is known. Instead a **profile** is a *match rule* with the configuration to apply to whatever it matches: by name, MAC address, bus path, driver or type, with one `*` wildcard allowed. netd evaluates every profile against every interface, highest priority first, and the first whose match keys all hold wins.

Nothing is "activated". A profile that matches two interfaces configures both; an interface no profile matches is left alone. A default profile shipped with the image claims every Ethernet interface for DHCP, at a priority low enough that anything you write outranks it.

## The inventory

netd writes what it finds under `Machine\System\Network\Interfaces\<ifid>`: the kernel name, MAC, bus path, driver, type, and which profile won. The **interface id** is derived from the bus path and MAC, so the same card in the same slot keeps the same key across boots however the kernel names it. One value there is yours: `Enabled`, which takes an interface down and keeps it down regardless of its profile.

Nothing transient is stored in the registry — not leases, not link state, not learned DNS servers. `net status` shows those.

## Addresses

A profile gets its addresses three ways, and they combine:

- **DHCPv4**, on by default. netd runs its own client on each interface once it has carrier. The lease's address, gateway, classless routes, DNS servers and MTU are applied; the address is remembered on disk so the next boot asks for the same one first.
- **IPv6 autoconfiguration**, on by default. netd solicits routers and acts on their advertisements itself — the kernel's own RA handling is switched off everywhere, so there is exactly one place deciding what an advertisement means. Each advertised prefix yields a **stable-privacy address** (RFC 7217): a keyed digest of the prefix and the interface's identity, so the same machine on the same network keeps its address across boots without ever deriving it from the MAC. When a router asks for it (the M or O flag), netd also asks over stateless DHCPv6 for DNS servers and search domains. A profile can additionally enable **temporary addresses** (RFC 8981) that rotate daily.
- **Static** addresses in CIDR form, either family, with optional gateways that override DHCP's and the routers'.
- **Link-local** (169.254/16), self-assigned when DHCP discovery goes unanswered, so two machines on a cable with no server can still talk. Discovery continues, and the link-local address is dropped when a lease arrives.

When a lease expires and cannot be renewed the address is dropped by default: the server may have given it to someone else, and an address conflict is worse than no address. A profile can choose to keep it instead. IPv6 lifetimes behave as the RFCs say: an address past its preferred lifetime is kept for standing connections but chosen for nothing new, and one past its valid lifetime is removed — with the two-hour floor that stops a spoofed advertisement from killing an address outright.

## Readiness is a level, not a boolean

"The network is up" means different things to different services. netd reports each interface at one of four **levels** — `absent`, `link` (up with carrier), `addressed` (has an address), `routed` (has a default route) — and the machine's level is the highest among its managed interfaces. `net wait routed` blocks until there is a default route; a service definition will be able to declare which level it needs.

## What netd does not do

- **Names.** netd never answers a DNS query. It tells resolvd, live, what each interface contributes — servers, search domains, addresses — and resolvd routes every name to one interface's servers. Nothing is written to `/etc/resolv.conf` or `/etc/hosts`; see [name resolution](~peios/networking/name-resolution).
- **Firewalling.** Traffic policy is a separate component.
- **Port ownership.** Who may bind a port is a kernel decision under `Machine\System\Network\TcpIp\PortReservations`.
- **WiFi association.** A wireless supplicant brings the link up; netd treats the result like any other interface.

## Where to start

- [Configuring profiles](~peios/networking/configuring-profiles) — write a profile, static or DHCP, and see it take effect.
- [The net command](~peios/networking/the-net-command) — status, levels, renewals.
- `regman Machine\System\Network` on a Peios machine documents every key netd reads.
