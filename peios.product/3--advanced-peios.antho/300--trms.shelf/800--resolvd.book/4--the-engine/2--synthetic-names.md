---
title: Synthetic Names
description: The names resolvd answers before any network — localhost, the static names, the machine's own name, .local, and their reverses — in the order it checks them and for which record types.
---

PSPU §6.7 lists the names a resolver answers before any network.
resolvd checks them in a fixed order, on the name as asked and before
any search expansion, and the first match answers the task.

## The order

1. **`localhost`, or any name under it.** `127.0.0.1` for `A`, `::1`
   for `AAAA`, both for `ANY`. Source `synthetic`. [*engine-synthetic.localhost]
2. **A static name.** An exact, case-insensitive match against the
   `Hosts\` values (§2.3). The name's addresses of the asked family —
   IPv4 for `A`, IPv6 for `AAAA`, both for `ANY`. Source `hosts`. [*engine-synthetic.static-name]
3. **The machine's hostname.** An exact, case-insensitive match against
   the hostname (§3.3). The machine's own addresses: every address of
   every scope at level `addressed` or better, excluding loopback
   addresses, in snapshot order. When there are none, `127.0.0.1` and
   `::1`. Source `synthetic`. [*engine-synthetic.hostname]
4. **`.local`.** The name `local` or any name under it is `notfound`.
   Source `synthetic`. No query is sent. [*engine-synthetic.local-is-notfound]
5. **A reverse-mapping name, for `PTR` or `ANY` only.** See below.

A name that matches none of these goes on to search expansion and the
network.

Because the order is fixed, a static name beats the hostname and
`.local`: a `Hosts\` value named `printer.local` is answered with its
addresses, and one named after the machine overrides the machine's own
addresses. [*engine-synthetic.check-order]

### Record types

For the three address-bearing kinds, the answer is `found` whatever type
was asked; a type other than `A`, `AAAA` or `ANY`, or a family the name
has no address in, gives `found` with no records. `localhost` asked for
`MX` is an empty `found`, not a `notfound`, and is not forwarded. [*engine-synthetic.other-types-are-empty-found]

### The machine's own addresses

They are taken from every scope at `addressed` or better, whether or not
the scope has servers, and include link-local addresses. [*engine-synthetic.own-addresses-from-every-addressed-scope] Repeated
addresses are removed only when they are adjacent in that list, so an
address on two interfaces that are not consecutive in the snapshot
appears twice. [*engine-synthetic.only-adjacent-duplicates-removed]

## Reverse names

A reverse-mapping name is one under `in-addr.arpa` with exactly four
labels, each a decimal octet, before the suffix, or one under
`ip6.arpa` with exactly 32 labels, each a single hexadecimal digit. [*engine-synthetic.reverse-name-forms]
Asked for `PTR` or `ANY`, such a name is answered synthetically when
its address is:

| Address | Answer | Source |
|---|---|---|
| A loopback address — anything in `127.0.0.0/8`, or `::1` | `PTR localhost` | `synthetic` [*engine-synthetic.reverse-loopback] |
| Listed under a static name | `PTR` that name | `hosts` [*engine-synthetic.reverse-static-name] |
| One of the machine's own addresses, when there is a hostname | `PTR` the hostname | `synthetic` [*engine-synthetic.reverse-own-address] |

The rows are tried in that order. When several static names list the
same address, the name returned is whichever of them the static-name
table yields first; that choice is not stable across configuration
reloads or restarts. [*engine-synthetic.shared-static-address-reverse-unstable]

A reverse name asked for any other type, and a reverse name whose
address matches none of the rows, goes to the network. [*engine-synthetic.other-reverse-questions-go-to-network]

## Properties of every synthetic answer

Every synthetic record has TTL 0. [*engine-synthetic.ttl-zero] Synthetic answers are never cached,
and the `no_cache` flag has no effect on them. [*engine-synthetic.never-cached] Each one adds one to the
`synthetic` counter (§4.10).

Only the name as asked is checked. An expanded candidate is never
compared with the synthetic names, so with a static name `printer.lan`
and the search domain `lan`, a question for `printer` is expanded and
sent to the network as `printer.lan`. [*engine-synthetic.expanded-candidates-not-checked]
