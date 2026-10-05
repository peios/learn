---
title: Reconciliation
description: How netd diffs an interface's desired state against the kernel's and applies the difference — what counts as netd's, the order of operations, how each is phrased to rtnetlink, and which failures are benign.
---

## What netd owns [*reconcile.ownership]

On an interface with a desired state:

- **Every IPv4 address**, including a 169.254 address, and **every IPv6
  address except a link-local one** is netd's. An address netd does not
  desire is removed, whoever added it.
  [*reconcile.foreign-address-removed]
- **A route is netd's only if it carries routing protocol 200**
  (`RTPROT_NETD`). netd stamps it on every route it adds, and removes no
  route without it. [*reconcile.foreign-route-kept]
- **The kernel's IPv6 link-local addresses** (`fe80::/10`) are never
  compared, added or removed. Every up interface has one, and neighbour
  discovery needs it.

Only routes in the main table, of unicast type and with an output
interface, are read from the kernel at all.

## The plan [*reconcile.plan-order]

For each interface with a desired state, netd plans these operations, in
this order:

1. **Link up**, if it is desired up and is down.
2. **MTU**, if one is desired, differs from the link's, and is at least
   68.
3. **Address deletions**: every address netd owns whose address and
   prefix length together match no desired address.
4. **Address additions**: every desired address the kernel does not hold
   with the same flags.
5. **Route deletions**: every protocol-200 route on the interface that is
   not desired.
6. **Route additions**: every desired route the kernel does not hold.
7. **Link down**, if it is desired down and is up — last, after its
   addresses and routes have gone.

Addresses compare by address and prefix length, plus the two flags netd
sets: deprecated and no-prefix-route. A tentative flag (duplicate address
detection still running) is erased before comparing. A change of flags
alone is therefore an addition of the same address, which replaces it
(below), never a delete and re-add that would reset standing connections.
[*reconcile.flag-change-is-a-replace]

Routes compare on everything: destination, prefix length, gateway, metric
and protocol. A change of metric or gateway is a deletion and an
addition.

An interface whose desired state the kernel already matches gets an empty
plan, and nothing is sent. [*reconcile.converged-plan-is-empty]

## Applying [*reconcile.apply]

Operations are applied one at a time, each as an rtnetlink request with
an acknowledgement:

| Operation | Request |
|---|---|
| link up or down | `RTM_SETLINK` changing only `IFF_UP` |
| MTU | `RTM_SETLINK` with `IFLA_MTU` |
| address add | `RTM_NEWADDR` with `NLM_F_CREATE` and `NLM_F_REPLACE` |
| address delete | `RTM_DELADDR` |
| route add | `RTM_NEWROUTE` with `NLM_F_CREATE` and `NLM_F_EXCL`, main table, protocol 200 |
| route delete | `RTM_DELROUTE` |

How addresses are phrased:

- An **IPv4** address carries `IFA_LOCAL` and `IFA_ADDRESS` set to
  itself, link scope for 169.254/16 and universe scope otherwise. Below
  a /31 it also carries a broadcast address: the lease's if it gave one,
  otherwise the subnet's all-ones address.
- An **IPv6** address carries universe scope and, when its prefix is not
  on-link, `IFA_F_NOPREFIXROUTE`. Its lifetimes are netd's to manage, so
  the kernel is told a valid lifetime of forever and a preferred lifetime
  of forever, or of zero when the address is deprecated. Source address
  selection then stops choosing a deprecated address, and connections
  already using it keep it. [*reconcile.ipv6-lifetimes-forever-or-deprecated]

A route with a gateway has universe scope, and one without has link
scope. A route carries a metric only when it is above zero.

A failed operation is logged as `reconcile: <operation> failed: <error>`
and the rest of the plan carries on, so one bad route never stops an
address landing. `EEXIST` on an add and `ENOENT` or `ESRCH` on a delete
mean the kernel got there first, and are not logged.
[*reconcile.failure-carries-on]

After every interface's plan is applied, netd dumps the kernel's state
again, so readiness and the status reply describe what actually landed.
