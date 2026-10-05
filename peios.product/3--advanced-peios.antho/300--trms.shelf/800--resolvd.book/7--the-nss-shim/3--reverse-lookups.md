---
title: Reverse Lookups
description: How the shim answers an address — loopback in-process, everything else through a reverse — and which records become h_name and h_aliases.
---

## Loopback

An address in `127.0.0.0/8`, or `::1`, is answered inside the calling
process without contacting resolvd: `h_name` is `localhost`, with no
aliases and TTL 0. [*nss-reverse.loopback-answered-in-process]

## Everything else

Any other address is sent as a `reverse` (§4.9). A `found` reply with no
records is `NOTFOUND` (§7.1). [*nss-reverse.found-without-records-is-notfound] Otherwise the reply's `PTR` records are
taken in order, each record's `text` with any trailing dot removed: [*nss-reverse.hostent-layout]

| Field | Content |
|---|---|
| `h_name` | The first `PTR` record's name |
| `h_aliases` | The remaining `PTR` records' names |
| `h_addrtype` | The `af` asked for |
| `h_length` | 4 or 16 |
| `h_addr_list` | The address asked about, alone |

A reply whose records include no `PTR` record — only `CNAME`s, for
instance — is `NOTFOUND` with `HOST_NOT_FOUND`. [*nss-reverse.no-ptr-record-is-notfound]

When `ttlp` is given it receives the least TTL among all the reply's
records, `PTR` or not. [*nss-reverse.ttl-least-of-all-records]
