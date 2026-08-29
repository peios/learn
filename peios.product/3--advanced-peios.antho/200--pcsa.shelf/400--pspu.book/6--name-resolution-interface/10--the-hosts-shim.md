---
title: The Hosts Shim
description: What libnss_peios_net.so.2 must do — one request per libc call, localhost on its own, no files and no DNS — and how outcomes map to NSS statuses.
---

The shim is the NSS module glibc's `hosts` database reaches, and on
Peios the only one it can reach: glibc is patched so that `hosts`, like
the identity databases, is not configurable and names `peios_net`
whatever `nsswitch.conf` says. There is no `files` source behind it and
no `/etc/hosts` for one to read.

## Obligations

A shim MUST:

1. Forward every question to the native channel (§6.4) as `lookup` or
   `reverse`, one connection per libc call, and render the reply. It
   MUST NOT hold a connection across calls.
2. Answer `localhost`, and any name under it, and the reverse of a
   loopback address, itself — with no socket. It is the one name a
   machine can never be without, and the only one the shim knows.
3. Answer `NSS_STATUS_UNAVAIL` for everything else when the resolver
   cannot be reached. There is nothing behind it.
4. Report an over-full caller buffer as `NSS_STATUS_TRYAGAIN` with
   `ERANGE`, so glibc retries with a larger one.

A shim MUST NOT read `/etc/hosts`, `/etc/resolv.conf` or any file;
MUST NOT speak DNS itself; and MUST NOT cache. Each would be a second
policy path the resolver cannot see.

## Status mapping

| Resolver outcome | NSS status | `h_errno` |
|---|---|---|
| `found`, with addresses of the asked family | `SUCCESS` | — |
| `found`, none of that family | `NOTFOUND` | `NO_DATA` |
| `notfound` | `NOTFOUND` | `HOST_NOT_FOUND` |
| `unavailable` | `TRYAGAIN` (`EAGAIN`) | `TRY_AGAIN` |
| Resolver unreachable, or an error reply | `UNAVAIL` | `NO_RECOVERY` |

The `unavailable` row is the one that matters: a shim MUST NOT render it
as `NOTFOUND`. A caller that retries gets its answer when the network
comes back; a caller told "no such host" may remember that.

`h_name` is the reply's `canonical` name. TTLs are reported through
`ttlp` where glibc offers it, as the least TTL among the addresses.

## Entry points

`_nss_peios_net_gethostbyname4_r`, `gethostbyname3_r`,
`gethostbyname2_r`, `gethostbyname_r`, `gethostbyaddr2_r`,
`gethostbyaddr_r`. The module's SONAME is `libnss_peios_net.so.2` and
it is installed in glibc's configured library directory; it links
against libc and the wire codec and nothing else, since it is loaded
into every process that resolves a host.
