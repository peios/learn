---
title: Scope Routing
description: How resolvd picks the one scope a candidate goes to — which scopes take part at all, each step of the order as implemented, and how ties are broken.
---

PSPU §6.7 gives the routing order. resolvd applies it to each candidate
separately, when the candidate is first asked, and the candidate's
retries stay with the scope it chose.

## Which scopes take part [*engine-routing.only-routable-scopes-take-part]

Only **routable scopes** (§1.3) take part: those that are up — at level
`link` or better (PSPU §6.2) — and have at least one server. An up scope
with no servers is skipped at every step: it is never chosen, it never
wins a tie, and its flags have no effect on routing. The same set
decides which search domains apply (§4.3).

## The steps

1. **Exclusive.** The routable scopes that are exclusive and at level
   `addressed` or better. The one with the lowest metric takes the
   candidate; among equal metrics, the first in snapshot order. [*engine-routing.step-exclusive]
2. **Search domain.** Among the routable scopes, every search domain the
   candidate equals or ends with, compared label by label and
   case-insensitively. The scope holding the matching domain with the
   most labels takes the candidate. [*engine-routing.step-search-domain]
3. **Reverse subnet.** When the candidate is a reverse-mapping name
   (§4.2), the routable scopes that hold an address of the same family
   whose prefix contains the named address; a prefix length beyond the
   family's width counts as the full width. The lowest metric wins, then
   the earliest. [*engine-routing.step-reverse-subnet]
4. **Default route.** The routable scopes with `default_route` set. The
   lowest metric wins, then the earliest. [*engine-routing.step-default-route]
5. **Lowest metric.** Otherwise, the routable scope with the lowest
   metric, then the earliest. This step is reached whenever no routable
   scope claims the default route — including when the only claimant
   has no servers. [*engine-routing.step-lowest-metric]
6. **Fallback.** When there are no routable scopes at all, the fallback
   scope, provided `FallbackServers` names at least one server. Its
   scope key is `fallback`. [*engine-routing.step-fallback]

When none of the steps yields a scope, the candidate is `unavailable`
without a query (§4.1).

### An exclusive scope that does not qualify [*engine-routing.exclusive-without-servers-or-address-not-exclusive]

An exclusive scope at level `link`, or one with no servers, is not
exclusive for routing, and routing continues with step 2. The first
takes part in the later steps as an ordinary scope; the second, not
being routable, in none of them.

### Ties between search domains [*engine-routing.search-domain-tie-break]

Between matching domains with the same number of labels, the one in the
scope with the lower metric wins. With equal metrics too, the first
match found wins: the earlier scope in snapshot order, and within one
scope the earlier domain.

## Consequences

### Step 1 takes every candidate [*engine-routing.exclusive-takes-every-candidate]

Step 1 is absolute while it applies: with an exclusive scope chosen,
every candidate goes to it, whatever its name, and step 2 never runs.

### Search domains beat the subnet rule [*engine-routing.search-domain-beats-subnet]

Step 2 runs before steps 3 and 4, so a scope whose search domain is
`in-addr.arpa` or `10.in-addr.arpa` takes reverse names ahead of the
subnet rule.

### Fallback servers are a last resort [*engine-routing.fallback-unused-while-any-interface-has-a-server]

Fallback servers are used only while no scope is routable. As soon as
one scope at `link` or better has a server, the fallback scope takes
nothing. Answers cached through it are then not consulted, and stay in
the cache until they are flushed, overwritten or evicted (§4.5).

### A candidate asks only its own scope's servers [*engine-routing.candidate-asks-only-its-scope]

Every attempt for a candidate, and the TCP retry after a truncated
reply, goes to a server of the one scope the candidate was routed to.
When those attempts fail, the candidate is `unavailable` (§4.6); the
servers of other scopes, and the fallback servers, are not asked for
it.

### Demotion does not affect routing [*engine-routing.demotion-does-not-affect-routing]

Routing reads only the current scope list. Which servers are demoted
has no effect on which scope a candidate goes to: a scope whose every
server is demoted still takes the candidates routing gives it.
