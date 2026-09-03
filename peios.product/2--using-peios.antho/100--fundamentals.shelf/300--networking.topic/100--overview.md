---
title: Networking
type: concept
description: How a Peios machine gets onto a network — PNP's interface layer says which interfaces join and which profile they stand in, and netd reconciles links, addresses, routes and DHCP to it; nothing else configures the network.
related:
  - peios/networking/configuring-profiles
  - peios/networking/network-policy
  - peios/networking/name-resolution
  - peios/networking/the-net-command
  - peios/registry-concepts/overview
  - peios/services-and-jobs/overview
  - peios/registry-administration/regman
---

A Peios machine's network is described in the registry and made real by one service, **netd**. There is no `ifconfig` step, no interface file, no daemon-specific configuration format: what the network should be is written under `Machine\System\Network`, in the vocabulary of [Peios Network Policy](~peios/networking/network-policy), and netd keeps the kernel matching it.

This page explains the model. [Configuring profiles](~peios/networking/configuring-profiles) covers writing the configuration; [The net command](~peios/networking/the-net-command) covers looking at the result.

## The registry is the truth

netd is a **reconciler**. It reads the desired state — the interface layer's rules and the profiles from the registry, plus whatever leases its DHCP clients currently hold — compares it with what the kernel reports over rtnetlink, and applies the difference. It does this on start, whenever the kernel reports a change (a cable plugged in, an interface appearing), whenever the registry changes, and whenever a DHCP lease arrives or expires.

Two consequences follow, and both are deliberate:

- **A manual change to a joined interface is reverted.** Adding an address by hand lasts until the next reconcile. The way to change the network is to change the registry.
- **Restarting netd changes nothing visible.** It re-derives the same desired state, finds the kernel already matches, and does nothing. Interfaces do not flap.

netd owns what it configured and nothing else. Addresses on a joined interface are all netd's; routes are netd's only when they carry its routing-protocol tag, so a route another program adds for itself is left alone.

## Rules say which, profiles say how

An **interface** is a place a network can be attached: an Ethernet socket, a radio, later a tunnel. It exists from the moment the hardware is found, cable or no cable. Plugging in gives it a link, and then there is a **network** on the other side, which makes an **offer**: an address for you, a way out, name servers, sometimes a name for you. The offer is claims; nothing checks them.

For each interface the machine decides one thing — join the network found there, or do not, and if joining, what to take from the offer — and that decision is written in two places:

- **A rule in the interface layer**, `Rules\Interface`, says *which* interfaces. It is an ordinary PNP rule: conditions over facts about the interface (`Interface.Kind`, `Interface.Path`, the stable `Interface.Id`) and, once a network has been identified on it, about the network (`Network.Name`, `Network.Trust`). Its verdict is `JOIN(profile)`, `IGNORE` (never touch it) or `DOWN` (keep it dark). Exceptions are subkeys, the most specific rule speaks, priority collates, and an interface no rule speaks for meets the backstop, `IGNORE`, and is left exactly as the kernel left it.
- **A profile** under `Profiles\` says *how* to stand there: `Address.Offered`, `Dns.Servers`, `Route.Gateway`, and so on. Nothing the network offers is taken unless a bundle's `Offered` says so, so a profile's trust posture is visible by counting its Offereds. A subkey is a derived profile that inherits everything above it and overrides only what it names.

Nothing is "activated". A rule that matches two interfaces puts both in its profile; the same profile serves any number of interfaces; and the same radio can stand in a different profile at home, in the office and in a cafe, because the rule can condition on the network. A default profile and a rule shipped with the image put every wired interface on whatever it is plugged into, at a priority anything you write outranks.

## The inventory and the networks

netd writes what it finds under `Machine\System\Network\Interfaces\<id>\Status`: the kernel name, kind, MAC, bus path, driver, and its verdict — which rule spoke, which profile it stands in, and its readiness. The **interface id** is derived from the bus path and MAC, so the same card in the same slot keeps the same key across boots however the kernel names it. Only netd may write a `Status` key; a hand edit is refused rather than silently reverted.

Every network the machine has stood on gets a record under `Networks\<id>`, identified for now by the DHCP server that answered and the subnet it handed out (or the advertising router and its prefix). Two values on it are yours: `Name`, a label, and `Trust`, your word on it. Those are the `Network.*` facts rules condition on. What the network showed is under its own `Status`.

Nothing transient is stored in the registry — not leases, not link state, not what a network offered. `net status` shows those.

## Addresses

A profile gets its addresses three ways, and they combine:

- **Offered**, with `Address.Offered`: netd runs its own DHCPv4 client once the interface has carrier, and solicits IPv6 routers and acts on their advertisements itself — the kernel's own RA handling is switched off everywhere, so there is exactly one place deciding what an advertisement means. Each advertised prefix yields a **stable-privacy address** (RFC 7217): a keyed digest of the prefix and the interface's identity, so the same machine on the same network keeps its address across boots without ever deriving it from the MAC. When a router asks for it (the M or O flag), netd also asks over stateless DHCPv6 for DNS servers and search domains. `Address.Temporary` adds daily-rotating addresses (RFC 8981) beside the stable one. `Address.Families` limits the bundle to one family.
- **Static** addresses in `Address.Static`, CIDR form, either family. The way out is a separate claim: `Route.Offered` takes the network's, `Route.Gateway` pins your own.
- **Link-local** (169.254/16), with `Address.LinkLocal`: self-assigned when DHCP discovery goes unanswered, so two machines on a cable with no server can still talk. Discovery continues, and the link-local address is dropped when a lease arrives.

When a lease expires and cannot be renewed the address is dropped by default: the server may have given it to someone else, and an address conflict is worse than no address. A profile can say `Address.OnExpiry = Keep` instead. IPv6 lifetimes behave as the RFCs say: an address past its preferred lifetime is kept for standing connections but chosen for nothing new, and one past its valid lifetime is removed — with the two-hour floor that stops a spoofed advertisement from killing an address outright.

The address a network last leased is remembered on its record as `RequestedAddress`, and asked for first next time. You may write it yourself as a soft reservation.

## Readiness is a level, not a boolean

"The network is up" means different things to different services. netd reports each joined interface at one of four **levels** — `absent`, `link` (up with carrier), `addressed` (has an address), `routed` (has a default route) — and the machine's readiness is the highest among them. Both are written to the registry as `Readiness`, on `Machine\System\Network` and on each interface's `Status`, for services and scripts to watch; `net wait routed` blocks until there is a default route. A service that needs the network says so in its definition, `Requires = ["network:routed"]`: `network` is the role netd fills, so the dependency names PNP's vocabulary rather than the daemon, and peinit holds the start until the level is published.

## What netd does not do

- **Names.** netd never answers a DNS query. It tells resolvd, live, what each interface contributes — servers, search domains, addresses — and resolvd routes every name to one interface's servers. Nothing is written to `/etc/resolv.conf` or `/etc/hosts`; see [name resolution](~peios/networking/name-resolution).
- **Firewalling.** The packet layers of PNP are the kernel's; netd reads only the interface layer. Joining needs netd's own DHCP and router-discovery traffic to pass them, and the shipped baseline permits it with visible, deletable rules.
- **Port ownership.** Who may bind a port is a kernel decision under `Machine\System\Network\TcpIp\PortReservations`.
- **WiFi association.** A wireless supplicant brings the link up; netd treats the result like any other interface. Wireless networks are not yet identified by name.

## Where to start

- [Configuring profiles](~peios/networking/configuring-profiles) — write a profile and a rule, static or offered, and see it take effect.
- [Network policy](~peios/networking/network-policy) — the model behind rules, and the [reference](~peios/networking/network-policy-reference) with every fact, verdict and profile value.
- [The net command](~peios/networking/the-net-command) — status, readiness, renewals.
- `regman Machine\System\Network` on a Peios machine documents every key netd reads and writes.
