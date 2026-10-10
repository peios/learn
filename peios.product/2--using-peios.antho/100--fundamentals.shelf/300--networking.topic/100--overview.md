---
title: Networking
type: guide
description: Check network status, configure an interface safely, verify addresses and routes, and choose the next connectivity, DNS or firewall check.
related:
  - peios/networking/configuring-profiles
  - peios/networking/network-policy
  - peios/networking/name-resolution
  - peios/networking/the-net-command
  - peios/registry-concepts/overview
  - peios/services-and-jobs/overview
  - peios/registry-administration/regman
---

Start with `net status` to see whether an interface has joined a network,
which profile it uses, and whether it has an address and a default route.
On the desktop, open **Network Manager** from the launcher by typing
`network`.

```sh
net status
resolv status
```

`net` reports interface configuration; `resolv` reports the name servers
actually in use. For a firewall change, an administrator also checks
`net policy`. A route, a DNS answer and permission to reach a service are
separate checks.

## Choose the next check

| What you see | Next step |
|---|---|
| No carrier, or readiness `absent` | Check the cable or link and the interface's verdict in `net status`. |
| `IGNORE`, `DOWN`, or no profile | Inspect `net rules` and [choose a profile safely](~peios/networking/configuring-profiles). |
| Carrier, but no address or only `169.254…` | Check the profile and DHCP warning; follow [connectivity troubleshooting](~peios/networking/diagnostic-tools#start-with-the-symptom). |
| An address, but no default route | Check `Route.Offered` or the pinned `Route.Gateway`, then read back the result. |
| An address works but a name does not | Use [name-resolution checks](~peios/networking/name-resolution#check-a-name-first). |
| A particular service is unreachable | Check its listener, port reservation and [firewall decision](~peios/networking/network-policy#check-and-change-policy-safely). |
| `policy REFUSED` | The last good interface configuration still applies. Fix the named rule or profile and check again. |

The [net command reference](~peios/networking/the-net-command) explains
its output and access rights. The [diagnostic tools](~peios/networking/diagnostic-tools)
guide covers probes available in Experimental.

## The registry is the truth

Network settings live under `Machine\System\Network`. Change them through
[Network Manager](~peios/networking/network-manager) or the
[profile and rule keys](~peios/networking/configuring-profiles). netd reads
those settings and applies them live; there is no interface configuration
file or reload command.

Do not add an address by hand to a joined interface: netd removes addresses
that its profile does not request. Routes added by another program are
left alone unless they carry netd's own routing-protocol tag. The kernel's
IPv6 link-local address is left alone too. The exact ownership and apply
order are in [Reconciliation](~peios/advanced-peios/netd/interfaces/reconciliation).

> [!WARNING]
> A live change can interrupt the connection you are using. Profile edits
> restart the affected interfaces' address clients. Do not use a daemon
> restart as a harmless reload: the netd manual documents leased addresses
> and routes being removed until DHCP answers, and advertised IPv6
> settings waiting for a new advertisement. Keep a local recovery path and
> follow [the change checklist](~peios/networking/configuring-profiles#before-you-change-anything).

The [netd loop](~peios/advanced-peios/netd/the-daemon/the-loop) and
[startup and restart](~peios/advanced-peios/netd/the-daemon/startup)
chapters describe how registry, kernel, lease and timer changes are
reconciled.

## Rules say which, profiles say how

A rule under `Rules\Interface` selects an interface and gives it one of
three outcomes:

- `JOIN(profile)` uses a profile under `Profiles\`.
- `IGNORE` leaves the interface as it is, including existing settings.
- `DOWN` keeps the interface administratively down.

A profile supplies settings such as `Address.Static`, `Route.Gateway` and
`Dns.Servers`. Each `Offered` value decides whether to accept that part
of the network's offer. An offer is a claim from the network, not proof
that it is trustworthy. A child profile inherits its parents' settings
and replaces only the values it names.

A profile can serve several interfaces at once; there is no separate
activation step. Rules can match stable interface identity or the network's
name and trust label. A shipped `wired` rule at priority 10 assigns all
wired interfaces to `default`, which accepts offered addresses, routes
and DNS and enables link-local fallback. A bare profile accepts none of
those offers. No matching rule means `IGNORE`.

See [Configuring profiles](~peios/networking/configuring-profiles) for
examples and [Network policy](~peios/networking/network-policy) for
exceptions, priorities and conflicts.

## The inventory and the networks

Use `net status` for the current link, address, lease and network. The
interface id remains stable for the same card in the same slot even if its
kernel name changes across boots.

The registry also keeps records under `Interfaces\<id>` and
`Networks\<id>`. netd's findings are in their protected `Status` subkeys;
hand edits there are refused. On a network record, you can set `Name` and
`Trust`. Rules for both profiles and the firewall use those labels, so
changing one can change connectivity.

Network identification currently uses the DHCP server and subnet, or an
advertising router and prefix. It does not prove a network's identity.
The [inventory](~peios/advanced-peios/netd/what-netd-publishes/the-inventory)
and [network records](~peios/advanced-peios/netd/networks/records) chapters
list the persisted fields; lease timers and current offered configuration
are live daemon state, not a lease to restore from the registry.

## Addresses

Choose these in a profile, then check the result in `net status`:

| Need | Setting and effect |
|---|---|
| Accept the network's address | `Address.Offered`: DHCPv4 and IPv6 router discovery, limited by `Address.Families`. IPv6 uses stable-privacy addresses; DHCPv6 supplies DNS information, not addresses. |
| Set an address yourself | `Address.Static`: CIDR addresses of either family. Set the gateway separately with `Route.Gateway`, or accept it with `Route.Offered`. |
| Reach another machine on a cable without DHCP | `Address.LinkLocal`: a `169.254/16` fallback while DHCP discovery continues; removed when a lease arrives. |
| Add rotating IPv6 addresses | `Address.Temporary`: daily-rotating addresses alongside the stable address. |

An expired DHCP lease is dropped by default. `Address.OnExpiry = Keep`
trades address-conflict risk for continuity. A network's `RequestedAddress`
is only the address to ask for first next time; the server can refuse it.

A deprecated IPv6 address remains for existing connections but is not
chosen for new ones; it is removed when its valid lifetime ends. Stable
address derivation, temporary-address rotation and the protective two-hour
lifetime rule are documented in [IPv6 addresses](~peios/advanced-peios/netd/ipv6/addresses).
See [DHCPv4](~peios/advanced-peios/netd/dhcpv4/the-client) for acquisition,
renewal and fallback details.

## Readiness is a level, not a boolean

| Level | What it tells you |
|---|---|
| `absent` | The joined interface is down or has no carrier. |
| `link` | It is up with carrier, but has no usable address. |
| `addressed` | It has a usable address, but no default route. A `169.254…` address counts. |
| `routed` | It has a usable address and a default route. This does not test Internet or DNS reachability. |

The machine reports the highest level among joined interfaces. Readiness
is also published on `Machine\System\Network` and each joined interface's
`Status` for scripts and services.

`net wait routed` waits for a default route. A service may declare
`Requires = ["network:routed"]`. These waits differ: `net wait` accepts
at least the requested level, while peinit matches the published service
level exactly. See [Readiness](~peios/advanced-peios/netd/what-netd-publishes/readiness)
before depending on `network:addressed`.

## What netd does not do

- **Answer DNS.** resolvd receives netd's live server and domain information;
  use [name resolution](~peios/networking/name-resolution) to configure and
  diagnose it. netd writes neither `/etc/resolv.conf` nor `/etc/hosts`.
- **Filter traffic.** The kernel enforces PNP's packet layers. DHCP and
  router-discovery traffic need the baseline's visible, deletable rules.
- **Grant port ownership.** [Port reservations](~peios/network-objects/port-reservations)
  decide who may bind a port; the firewall decides who may reach it.
- **Associate Wi-Fi.** A supplicant must bring up a wireless link before
  netd can configure it. Wi-Fi is unfinished: wireless is absent from the
  baseline, Network Manager shows it as **Not managed**, and wireless
  networks are not yet identified by name.

## Where to start

- [Configure a profile](~peios/networking/configuring-profiles), apply it
  through a matching rule, and read back the accepted settings.
- [Use Network Manager](~peios/networking/network-manager) for desktop
  configuration, change previews and its documented rollback flow.
- [Troubleshoot a symptom](~peios/networking/diagnostic-tools).
- Look up exact settings in `regman Machine\System\Network` or the
  [network policy reference](~peios/networking/network-policy-reference).
- Use the [netd technical reference manual](~peios/advanced-peios/netd/introduction/overview)
  for daemon algorithms, protocol exchanges, timers and limits.
