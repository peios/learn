---
title: Desired state
description: What a joined interface should carry — link, MTU, addresses, routes and their metric — computed from its profile and what its network has offered; and what DOWN and IGNORE desire.
---

On every reconcile netd computes, for each interface, what it should look
like. That **desired state** is a link state, an MTU, a set of addresses
and a set of routes. It is derived from the interface's verdict, its
profile, and its clients' current state, and from nothing else: netd keeps
no record of what it applied.

## By verdict [*desired.by-verdict]

- Loopback, or an `IGNORE`d interface: there is no desired state, and
  netd plans nothing for the interface.
- `DOWN`: the link down, with no addresses and no routes.
- `JOIN`: the link up, and everything below.

## The metric [*desired.metric]

Every route netd adds for an interface carries the interface's metric:
the profile's `Route.Metric` when it is set, otherwise 600 for a
`wireless` interface and 100 for anything else.

## The MTU [*desired.mtu]

The profile's `Mtu.Value` when set. Otherwise, with `Mtu.Offered`, the
lease's MTU (DHCP option 26), else the routers' advertised MTU (§6.1).
Otherwise no MTU is desired and the link's MTU is left as it is.

## IPv4 addresses [*desired.ipv4-addresses]

In this order:

1. every IPv4 entry of `Address.Static`, at its prefix;
2. the lease's address at the lease's prefix (§5.3), when a lease is
   held, with the lease's broadcast address (option 28) when it gave one;
3. the link-local address (§5.5) at prefix 16, only when the client has
   fallen back to one **and** no lease is held **and** the profile has no
   static address of either family.

## IPv4 routes [*desired.ipv4-routes]

- **The default route** goes via `Route.Gateway`'s IPv4 entry when it is
  set. Otherwise, with `Route.Offered`, it goes via the lease's gateway:
  the first router of option 3, or, when the lease carried classless
  routes, the gateway of the classless `0.0.0.0/0` route. With neither,
  there is no IPv4 default route.
- **Classless static routes** (option 121) with a prefix above zero are
  added, each via its gateway, only with `Route.Offered`.

`Route.Gateway` is used as written; netd does not check that the gateway
is on a subnet the interface has. A gateway the kernel cannot reach makes
the route's add fail on every reconcile, logged each time (§11).

## IPv6 addresses [*desired.ipv6-addresses]

1. every IPv6 entry of `Address.Static`, at its prefix, preferred, with
   a prefix route;
2. every address router discovery currently wants (§6.2): stable-privacy
   and temporary addresses, each deprecated or not, each with or without
   a prefix route according to the prefix's on-link flag.

## IPv6 default route [*desired.ipv6-default-route]

Via `Route.Gateway`'s IPv6 entry when it is set. Otherwise, with
`Route.Offered`, via the default router router discovery has chosen
(§6.1). With neither, there is no IPv6 default route.

## Not desired

netd never desires the kernel's own IPv6 link-local address, the
kernel's prefix routes, or any route without netd's protocol mark. Those
are outside what reconciliation compares (§4.3).
