---
title: Scope Routing
description: How resolvd picks the one scope a candidate goes to — which scopes take part at all, each step of the order as implemented, and how ties are broken.
---

PSPU §6.7 gives the routing order. resolvd applies it to each candidate
separately, when the candidate is first asked, and the candidate's
retries stay with the scope it chose.

## Which scopes take part

Only **up scopes** take part: those at level `link` or better with at
least one server. A scope with no servers is skipped at every step —
it is never chosen, it never wins a tie, and its flags have no effect on
routing. [*engine-routing.only-up-scopes-take-part] The same set decides which search domains apply (§4.3).

## The steps

1. **Exclusive.** The up scopes that are exclusive and at level
   `addressed` or better. The one with the lowest metric takes the
   candidate; among equal metrics, the first in snapshot order. [*engine-routing.step-exclusive] An
   exclusive scope at level `link`, or one with no servers, is not
   exclusive for routing, and routing continues with step 2: the first
   takes part in the later steps as an ordinary scope, the second in
   none of them. [*engine-routing.exclusive-without-servers-or-address-not-exclusive]
2. **Search domain.** Among the up scopes, every search domain the
   candidate equals or ends with, compared label by label and
   case-insensitively. The domain with the most labels wins; equal
   lengths go to the lower metric, then to the earlier scope. [*engine-routing.step-search-domain]
3. **Reverse subnet.** When the candidate is a reverse-mapping name
   (§4.2), the up scopes that hold an address of the same family whose
   prefix contains the named address. The lowest metric wins, then the
   earliest. [*engine-routing.step-reverse-subnet]
4. **Default route.** The up scopes with `default_route` set. The lowest
   metric wins, then the earliest. [*engine-routing.step-default-route]
5. **Lowest metric.** Otherwise, the up scope with the lowest metric,
   then the earliest. This step is reached whenever no *up* scope claims
   the default route — including when the only claimant has no servers. [*engine-routing.step-lowest-metric]
6. **Fallback.** When there are no up scopes at all, the fallback scope,
   provided `FallbackServers` names at least one server. Its scope key
   is `fallback`. [*engine-routing.step-fallback]

When none of the steps yields a scope, the candidate is `unavailable`
without a query (§4.1).

## Consequences

Step 1 is absolute while it applies: with an exclusive scope chosen,
every candidate goes to it, whatever its name, and step 2 never runs. [*engine-routing.exclusive-takes-every-candidate]
Step 2 runs before steps 3 and 4, so a scope whose search domain is
`in-addr.arpa` or `10.in-addr.arpa` takes reverse names ahead of the
subnet rule. [*engine-routing.search-domain-beats-subnet]

Fallback servers are used only while no interface offers a server. As
soon as one scope at `link` or better has a server, the fallback scope
takes nothing, [*engine-routing.fallback-unused-while-any-interface-has-a-server] and answers cached through it stay in the cache until
they expire or the fallback list changes.

Routing reads only the current scope list. It sends nothing to more
than one scope, [*engine-routing.never-more-than-one-scope] and nothing it does depends on which servers are
demoted. [*engine-routing.demotion-does-not-affect-routing]
