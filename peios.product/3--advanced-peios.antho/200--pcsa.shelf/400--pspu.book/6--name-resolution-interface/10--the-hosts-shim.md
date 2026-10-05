---
title: The Hosts Shim
description: What libnss_peios_net.so.2 must do — one request per libc call, localhost on its own, no files and no DNS — and how outcomes map to NSS statuses.
---

The shim is the NSS module glibc's `hosts` database reaches, and on
Peios the only one it can reach: glibc is patched so that `hosts`, like
the identity databases, is not configurable and names `peios_net`
whatever `nsswitch.conf` says. [*nri-shim.hosts-database-fixed-to-peios-net] There is no `files` source behind it and
no `/etc/hosts` for one to read.

## Obligations

A shim MUST:

1. Forward every question to the native channel (§6.4) as `lookup` or
   `reverse`, one connection per libc call, and render the reply. [*nri-shim.one-connection-per-call] It
   MUST NOT hold a connection across calls. [*nri-shim.no-connection-across-calls]
2. Answer `localhost`, and any name under it, and the reverse of a
   loopback address, itself — with no socket. [*nri-shim.answers-localhost-itself] It is the one name a
   machine can never be without, and the only one the shim knows.
3. Answer `NSS_STATUS_UNAVAIL` for everything else when the resolver
   cannot be reached. [*nri-shim.unreachable-resolver-is-unavail] There is nothing behind it.
4. Report an over-full caller buffer as `NSS_STATUS_TRYAGAIN` with
   `ERANGE`, so glibc retries with a larger one. [*nri-shim.over-full-buffer-is-tryagain-erange]

A shim MUST NOT read `/etc/hosts`, `/etc/resolv.conf` or any file; [*nri-shim.reads-no-file]
MUST NOT speak DNS itself; [*nri-shim.speaks-no-dns] and MUST NOT cache. [*nri-shim.does-not-cache] Each would be a second
policy path the resolver cannot see.

## Status mapping

| Resolver outcome | NSS status | `h_errno` |
|---|---|---|
| `found`, with addresses of the asked family | `SUCCESS` | — [*nri-shim.found-is-success] |
| `found`, none of that family | `NOTFOUND` | `NO_DATA` [*nri-shim.found-without-family-is-no-data] |
| `notfound` | `NOTFOUND` | `HOST_NOT_FOUND` [*nri-shim.notfound-is-host-not-found] |
| `unavailable` | `TRYAGAIN` (`EAGAIN`) | `TRY_AGAIN` [*nri-shim.unavailable-is-tryagain] |
| Resolver unreachable, or an error reply | `UNAVAIL` | `NO_RECOVERY` [*nri-shim.unreachable-or-error-is-no-recovery] |

The `unavailable` row is the one that matters: a shim MUST NOT render it
as `NOTFOUND`. A caller that retries gets its answer when the network
comes back; a caller told "no such host" may remember that.

> [!NOTE]
> glibc's `getaddrinfo` reports a module's `UNAVAIL` to its caller as
> `EAI_NONAME`, the same code as a name that does not exist, so through
> that interface an unreachable resolver still looks like an absent
> name. That mapping is glibc's; the shim reports `UNAVAIL` faithfully,
> and the native channel and `resolv` keep the distinction.

`h_name` is the reply's `canonical` name. [*nri-shim.h-name-is-canonical] TTLs are reported through
`ttlp` where glibc offers it, as the least TTL among the addresses. [*nri-shim.ttl-is-least-address-ttl]

## Entry points

`_nss_peios_net_gethostbyname4_r`, `gethostbyname3_r`,
`gethostbyname2_r`, `gethostbyname_r`, `gethostbyaddr2_r`,
`gethostbyaddr_r`. [*nri-shim.entry-points] The module's SONAME is `libnss_peios_net.so.2` and
it is installed in glibc's configured library directory; [*nri-shim.soname-and-location] it links
against libc and the wire codec and nothing else, since it is loaded
into every process that resolves a host. [*nri-shim.links-libc-and-codec-only]
