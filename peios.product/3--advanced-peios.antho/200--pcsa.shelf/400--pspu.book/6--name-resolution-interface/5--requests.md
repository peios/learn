---
title: Requests
description: The five requests on the native channel — resolve, lookup, reverse, status, flush — their fields, their replies, and the right each needs.
---

Each request is a map whose `query` key names it. Field types are the
MessagePack types named; an address is a string in its usual textual
form; a name is a string in presentation form, with or without a
trailing dot.

## `resolve` — `RESOLVER_QUERY`

One question.

| Key | Type | Meaning |
|---|---|---|
| `name` | string | The name |
| `type` | uint | The record type number (`1` A, `28` AAAA, `12` PTR, …) |
| `no_cache` | bool | Bypass the cache for this question; default `false` |

Reply `kind: answer`:

| Key | Type | Meaning |
|---|---|---|
| `outcome` | string | `found`, `notfound`, `unavailable` (§6.6) |
| `records` | array of map | Each: `name` (string), `type` (uint), `ttl` (uint), `data` (bin, uncompressed wire rdata), `text` (string, presentation form) |
| `source` | string | `synthetic`, `hosts`, `cache`, `dns`, `local` |
| `server` | string or nil | The upstream that answered, for `dns` |
| `interface` | string or nil | The interface whose scope answered |
| `validation` | string | §6.6 |
| `rcode` | uint | The DNS response code, for `dns`; `0` otherwise |

`records` is the answer section only. When the name was expanded
(§6.7) the records are at the expanded name, and `name` on each record
says so.

## `lookup` — `RESOLVER_QUERY`

The addresses of a name: what `getaddrinfo` asks. The resolver asks for
`A` and/or `AAAA`, applies search expansion, follows the CNAME chain and
returns what it ends at.

| Key | Type | Meaning |
|---|---|---|
| `name` | string | The name |
| `family` | string | `any` (default), `inet`, `inet6` |

Reply `kind: addresses`:

| Key | Type | Meaning |
|---|---|---|
| `outcome` | string | `found` when at least one family answered; `unavailable` when none did and one could not; else `notfound` |
| `canonical` | string | The name the addresses belong to after expansion and CNAME chasing; the name asked, when neither applied |
| `addresses` | array of map | Each: `address` (string), `ttl` (uint) |
| `source` | string | As for `resolve` |
| `validation` | string | §6.6 |

## `reverse` — `RESOLVER_QUERY`

| Key | Type | Meaning |
|---|---|---|
| `address` | string | An IPv4 or IPv6 address |

Equivalent to `resolve` of the address's reverse-mapping name with type
`PTR`; the reply is `kind: answer`.

## `status` — `RESOLVER_QUERY`

No fields. Reply `kind: status`:

| Key | Type | Meaning |
|---|---|---|
| `hostname` | string | The machine's name as the resolver knows it |
| `netd` | bool | Whether the network manager channel is connected |
| `scopes` | array of map | Each: `interface`, `servers` (array of string), `domains` (array of string), `default_route` (bool), `exclusive` (bool), `metric` (uint), `subnets` (array of string), `demoted` (array of string) |
| `fallback_servers` | array of string | The registry's server list |
| `cache_entries` | uint | |
| `counters` | map | `queries`, `synthetic`, `cache_hits`, `upstream_sent`, `upstream_answered`, `upstream_failed`, `refused`, each uint |

## `flush` — `RESOLVER_CONTROL`

No fields. Drops every cached answer. Reply `ok: true` with no `kind`.

## Unknown requests

A resolver MUST answer a `query` it does not know with an error reply.
A client MUST treat an error reply as "not answered", never as
`notfound`.
