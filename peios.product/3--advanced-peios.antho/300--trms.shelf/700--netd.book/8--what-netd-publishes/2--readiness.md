---
title: Readiness
description: The four readiness levels, how netd computes one for each interface and for the machine, and how the machine level reaches peinit and the registry.
---

"The network is up" means different things to different services, so
netd reports a level, not a flag. Levels are ordered:
`absent` < `link` < `addressed` < `routed`.

## An interface's level [*readiness.interface-level]

From the kernel's state after the last reconcile:

| Level | When |
|---|---|
| `absent` | the interface is not up, or has no carrier |
| `link` | up with carrier, and no usable address |
| `addressed` | a usable address, and no default route |
| `routed` | a usable address, and a default route on the interface |

A **usable** address is any IPv4 address other than a loopback one —
a 169.254 link-local address counts, because it is the outcome of address
acquisition — and any IPv6 address that is neither loopback nor
link-local. Every up interface has an IPv6 link-local address, so
counting one would make `addressed` mean nothing. Deprecated and
tentative addresses count. [*readiness.usable-address]

A **default route** is any route with prefix length 0, of either family,
in the main table, out of the interface. It need not be one of netd's.
[*readiness.any-default-route-counts]

## The machine's level [*readiness.machine-level]

The highest level among joined interfaces, or `absent` when none is
joined. An `IGNORE`d or `DOWN` interface contributes nothing, whatever
state it is in.

## Publishing it [*readiness.publish-on-change]

At every publish (§2.2) netd computes the machine level. When it differs
from the last one published — and at the first publish after startup,
which precedes `READY=1` — netd:

1. logs `machine readiness is <level>`;
2. sends `LEVEL=<level>` on the notify socket named by `NOTIFY_SOCKET`;
3. writes `Readiness` on `Machine\System\Network`.

A level is sent only on a change. The notify channel is lossy by design
and unacknowledged (PSPU §4.16), and a level is a statement of a current
condition, so a lost one is corrected by the next change.

Each joined interface's own level is written as `Status Readiness`
(§8.1).

## What peinit makes of it [*readiness.peinit-matches-the-published-level]

peinit records the level netd last sent against the `network` role netd
provides, and matches a dependent's level against it exactly (peinit TRM
§7.5). A service that `Requires = ["network:<level>"]` is held until the
level netd last published is that one: a higher level does not release
it.

netd publishes only the machine's current level, so a dependent is
released only while the machine sits at its level. When a DHCPv4 lease
carries a router and the profile takes it (`Route.Offered`, §4.2), the
lease's address and its default route are applied in the same pass, so
the level goes from `link` to `routed` without ever being `addressed`.
A `network:addressed` dependent is then held, through `link` and
`routed` alike, until the machine next sits at `addressed` with a
usable address and no default route: in practice, after the link-local
fallback (§5.5), or on a lease that gives no default route.

`net wait <level>` is not matched this way: it polls over the control
socket and succeeds when the machine level is at least the one named
(§10.1).
