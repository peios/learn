---
title: Forward Lookups
description: How the shim answers a host name — localhost in-process, everything else through a lookup — and how the reply is laid out as gaih_addrtuple and hostent.
---

## `localhost`

A name that, with trailing dots removed, is `localhost` or ends in
`.localhost`, compared case-insensitively, is answered inside the
calling process without contacting resolvd — whether resolvd is running
or not. The answer is `127.0.0.1` for IPv4, `::1` for IPv6, or both,
with canonical name `localhost` and TTL 0. [*nss-forward.localhost-answered-in-process]

## Everything else

Any other name is sent as a `lookup` (§4.9), with the family the entry
point asks for. The addresses in the reply are filtered to that family,
and an empty result is `NOTFOUND` (§7.1). [*nss-forward.addresses-filtered-to-family]

Addresses are returned in the order resolvd's reply lists them. [*nss-forward.reply-order-kept] resolvd
does not fix which family comes first (§4.9); glibc's own sorting of
`getaddrinfo` results is what callers normally see.

## `gethostbyname4_r`

The result is a linked list of `gaih_addrtuple`, one per address, in
reply order. Each tuple's `name` points at one copy of the canonical
name, its `family` is `AF_INET` or `AF_INET6`, and its `scopeid` is 0 —
an IPv6 link-local address is returned without the interface it belongs
to. [*nss-forward.gaih-addrtuple-layout] The pointer glibc passes is overwritten with the head of the list.
When `ttlp` is given it receives the least TTL among the addresses. [*nss-forward.gethostbyname4-ttl-least]

## `gethostbyname3_r`, `2_r` and `_r`

The result is a `hostent`: [*nss-forward.hostent-layout]

| Field | Content |
|---|---|
| `h_name` | The reply's `canonical` name |
| `h_aliases` | Empty |
| `h_addrtype` | The `af` asked for |
| `h_length` | 4 or 16 |
| `h_addr_list` | Every address, in reply order |

When `ttlp` is given it receives the least TTL among the addresses, and
when `canonp` is given it is pointed at `h_name`. [*nss-forward.gethostbyname3-ttl-and-canon]
