---
title: The Resolution Model
description: Scopes, the routing order that sends every question to exactly one of them, search expansion without leaks, synthetic answers, the scoped cache and server health.
---

This is the function behind every door.

## Scopes

Every interface with a link contributes a **scope**: servers in the
order to try them, search domains, the interface's addresses, whether it
claims unmatched names (`default_route`), whether it is exclusive, and
its metric. Scopes arrive from the network manager (§6.9); the resolver
holds them and nothing else about the network. The **fallback scope** is
`Machine\System\Network\Dns FallbackServers` and `ExtraSearchDomains`. [*nri-resolution.fallback-scope-from-registry]

## Routing

A question goes to **exactly one** scope. A resolver MUST NOT send a
question to several scopes' servers and take the first answer — parallel
fan-out is the mechanism of the classic VPN name leak, and it also lets
a hostile network win a race for a name it has no claim to. [*nri-resolution.exactly-one-scope-no-fan-out]

The order:

1. **An exclusive scope**, if any interface at `addressed` or better is
   exclusive: it takes every question. [*nri-resolution.route-exclusive-takes-every-question] Several exclusive scopes: the
   lowest metric. [*nri-resolution.route-several-exclusive-lowest-metric] While an exclusive interface is up no other
   interface's servers are consulted for anything. [*nri-resolution.exclusive-excludes-every-other-server]
2. **The longest matching search domain.** The scope with the longest
   domain the name ends with; ties by metric. [*nri-resolution.route-longest-search-domain]
3. **The subnet**, for a reverse-mapping name: the scope whose interface
   has an address in the same subnet as the address named. [*nri-resolution.route-reverse-by-subnet]
4. **The default-route claimant** with the lowest metric. [*nri-resolution.route-default-route-claimant]
5. **The lowest-metric scope with servers**, when no interface claims
   the default route. [*nri-resolution.route-lowest-metric-with-servers]
6. **The fallback scope**, only when no interface contributes servers. [*nri-resolution.route-fallback-only-without-interface-servers]

When none of these yields a scope with servers, the question is
`unavailable` without a query. [*nri-resolution.no-scope-is-unavailable-without-query]

This is DNS routing only. Which interface a *packet* leaves by is the
network manager's and the firewall's.

## Search expansion

A **single-label** name is never sent upstream as it is. [*nri-resolution.single-label-never-sent-bare] It is expanded
with the applicable search domains, in order, and each candidate is
asked in turn until one is not `notfound`. [*nri-resolution.candidates-asked-in-turn] The applicable domains are
the exclusive scope's when one is up; otherwise every up scope's, in
metric order, followed by the fallback scope's. [*nri-resolution.applicable-search-domains] With no applicable
domain the name is `notfound` without a query. [*nri-resolution.no-domain-is-notfound-without-query]

A **multi-label** name is never expanded. There is no `ndots` setting:
the rule is fixed at one, because every other value is a leak of local
names to the public tree or of public names to the local one. [*nri-resolution.multi-label-never-expanded]

An answer at an expanded name reports the expanded name (`resolved`
records on the native channel; a `CNAME` from the bare name at the
stub door, §6.8).

## Synthetic answers

Before any network, a resolver MUST answer: [*nri-resolution.synthetic-before-network]

- `localhost` and any name under it: `127.0.0.1` and `::1`; [*nri-resolution.synthetic-localhost]
- the machine's hostname: every unicast address of every interface at
  `addressed` or better, or loopback when there are none; [*nri-resolution.synthetic-hostname]
- every name under `Machine\System\Network\Dns\Hosts`, exactly and
  case-insensitively: its addresses. [*nri-resolution.synthetic-static-names] A static name wins over DNS; [*nri-resolution.static-name-wins-over-dns]
- the reverse of loopback (`localhost`), of a static name's address
  (the name), and of the machine's own addresses (the hostname); [*nri-resolution.synthetic-reverses]
- any name under `.local`: `notfound`. [*nri-resolution.local-is-notfound] mDNS is a separate transport
  (RFC 6762) and a `.local` question MUST NOT reach a DNS server. [*nri-resolution.local-never-reaches-dns]
  LLMNR MUST NOT be spoken. [*nri-resolution.no-llmnr]

A synthetic answer has `source` `synthetic` (or `hosts`) and TTL `0`. [*nri-resolution.synthetic-source-and-ttl-zero]

## The cache

The cache is keyed by `(name, type, scope)`, the name folded to lower
case. [*nri-resolution.cache-keyed-by-name-type-scope] The scope is part of the key because the same name may have
different answers on different interfaces (split horizon), and because
when an interface's servers change or the interface goes away, every
answer learned through it MUST be discarded: what a VPN's servers said
dies with the VPN. [*nri-resolution.cache-discarded-with-scope]

Positive answers live for their least TTL, capped (§6.B). [*nri-resolution.positive-ttl-least-capped] Negative
answers — `notfound`, and `found` with no records — live for the lesser
of the authority section's SOA record TTL and its MINIMUM field (RFC 2308
§5), capped lower. [*nri-resolution.negative-ttl-soa-minimum-capped] `unavailable`
is never cached. A hit reports TTLs reduced by the time spent in cache. [*nri-resolution.cache-hit-ttl-reduced]

## Upstream behaviour

A resolver MUST send each query from a fresh source port, [*nri-resolution.fresh-source-port] MUST use a
random message identifier, [*nri-resolution.random-message-id] and MUST randomise the case of the question
name and require the reply to echo it exactly (0x20 encoding). Both the
identifier and the case bits MUST come from a cryptographically secure
generator: a predictable one hands a spoofer back the entropy these
measures exist to add. [*nri-resolution.case-randomised-and-echo-required] A reply
whose identifier, question or case pattern does not match MUST be
ignored, not treated as a failure. [*nri-resolution.mismatched-reply-ignored]

Queries are UDP with EDNS0 advertising the buffer size in §6.B; [*nri-resolution.udp-with-edns0] a
truncated reply is retried over TCP to the same server. [*nri-resolution.truncated-retried-over-tcp-same-server] A server that
does not answer within the per-server timeout, or answers `SERVFAIL`,
`REFUSED` or a format error, is **demoted** — tried after its peers —
for the demotion period; [*nri-resolution.failing-server-demoted] the question moves to the next server. [*nri-resolution.question-moves-to-next-server] After
the attempt limit the question is `unavailable`. [*nri-resolution.attempt-limit-unavailable] Servers within a scope
are tried in the scope's order, healthy ones first; never in parallel. [*nri-resolution.servers-in-order-healthy-first]
