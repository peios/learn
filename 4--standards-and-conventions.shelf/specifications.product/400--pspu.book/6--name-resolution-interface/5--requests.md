---
title: Requests
description: The five requests on the native channel — resolve, lookup, reverse, status, flush — their fields, their replies, and the right each needs.
---

Each request is a map whose `query` key names it. Field types are the
MessagePack types named; an address is a string in its usual textual
form; a name is a string in presentation form, with or without a
trailing dot. [*nri-requests.field-encodings]

## `resolve` — `RESOLVER_QUERY`

One question.

| Key | Type | Meaning |
|---|---|---|
| `name` | string | The name |
| `type` | uint | The record type number (`1` A, `28` AAAA, `12` PTR, …) [*nri-requests.resolve-type-is-record-type-number] |
| `no_cache` | bool | Bypass the cache for this question; default `false` [*nri-requests.resolve-no-cache-bypasses-cache] |

Reply `kind: answer`:

| Key | Type | Meaning |
|---|---|---|
| `outcome` | string | `found`, `notfound`, `unavailable` (§6.6) |
| `records` | array of map | Each: `name` (string), `type` (uint), `ttl` (uint), `data` (bin, uncompressed wire rdata), `text` (string, presentation form) [*nri-requests.answer-records-shape] |
| `source` | string | `synthetic`, `hosts`, `cache`, `dns`, `local` [*nri-requests.answer-source-values] |
| `server` | string or nil | The upstream that answered, for `dns`; for `cache`, the upstream whose answer was cached; nil otherwise [*nri-requests.answer-server-for-dns] |
| `interface` | string or nil | The interface whose scope answered [*nri-requests.answer-interface] |
| `validation` | string | §6.6 |
| `rcode` | uint | The DNS response code, for `dns`; for `cache`, the code of the response that was cached; `0` otherwise [*nri-requests.answer-rcode-for-dns] |

`records` is the answer section only. [*nri-requests.records-are-answer-section-only] When the name was expanded
(§6.7) the records are at the expanded name, and `name` on each record
says so. [*nri-requests.expanded-records-carry-expanded-name]

## `lookup` — `RESOLVER_QUERY`

The addresses of a name: what `getaddrinfo` asks. The resolver asks for
`A` and/or `AAAA`, applies search expansion, follows the CNAME chain and
returns what it ends at. [*nri-requests.lookup-follows-cname-chain]

| Key | Type | Meaning |
|---|---|---|
| `name` | string | The name |
| `family` | string | `any` (default), `inet`, `inet6` [*nri-requests.lookup-family-default-any] |

Reply `kind: addresses`:

| Key | Type | Meaning |
|---|---|---|
| `outcome` | string | `found` when at least one family answered; `unavailable` when none did and one could not; else `notfound` [*nri-requests.lookup-outcome-rule] |
| `canonical` | string | The name the addresses belong to after expansion and CNAME chasing; the name asked, when neither applied [*nri-requests.lookup-canonical-name] |
| `addresses` | array of map | Each: `address` (string), `ttl` (uint) [*nri-requests.lookup-addresses-shape] |
| `source` | string | As for `resolve` |
| `validation` | string | §6.6 |

## `reverse` — `RESOLVER_QUERY`

| Key | Type | Meaning |
|---|---|---|
| `address` | string | An IPv4 or IPv6 address |

Equivalent to `resolve` of the address's reverse-mapping name with type
`PTR`; the reply is `kind: answer`. [*nri-requests.reverse-is-ptr-resolve]

## `status` — `RESOLVER_QUERY`

No fields. Reply `kind: status`:

| Key | Type | Meaning |
|---|---|---|
| `hostname` | string | The machine's name as the resolver knows it [*nri-requests.status-hostname] |
| `netd` | bool | Whether the network manager channel is connected [*nri-requests.status-netd-connected] |
| `scopes` | array of map | Each: `interface`, `servers` (array of string), `domains` (array of string), `default_route` (bool), `exclusive` (bool), `metric` (uint), `subnets` (array of string: the interface's addresses, each as `address/prefix`, which name the subnets routing step 3 matches against), `demoted` (array of string) [*nri-requests.status-scopes] |
| `fallback_servers` | array of string | The registry's server list [*nri-requests.status-fallback-servers] |
| `cache_entries` | uint | [*nri-requests.status-cache-entries] |
| `counters` | map | `queries`, `synthetic`, `cache_hits`, `upstream_sent`, `upstream_answered`, `upstream_failed`, `refused`, each uint [*nri-requests.status-counters] |

## `flush` — `RESOLVER_CONTROL`

No fields. Drops every cached answer. Reply `ok: true` with no `kind`. [*nri-requests.flush-drops-every-cached-answer]

## Unknown requests

A resolver MUST answer a `query` it does not know with an error reply. [*nri-requests.unknown-query-answered-with-error]
A client MUST treat an error reply as "not answered", never as
`notfound`. [*nri-requests.client-treats-error-as-not-answered]
