---
title: Message Reference
description: Every NRI request and reply by name, the rights and values, and the constants.
---

## Native channel requests

| `query` | Right | Reply `kind` | Defined in |
|---|---|---|---|
| `resolve` | `RESOLVER_QUERY` | `answer` | §6.5 |
| `lookup` | `RESOLVER_QUERY` | `addresses` | §6.5 |
| `reverse` | `RESOLVER_QUERY` | `answer` | §6.5 |
| `status` | `RESOLVER_QUERY` | `status` | §6.5 |
| `flush` | `RESOLVER_CONTROL` | (none) | §6.5 |

## Network manager channel

| `query` | Right | Reply `kind` | Defined in |
|---|---|---|---|
| `subscribe` | `NETWORK_QUERY` | `snapshot`, streamed | §6.9 |

## Rights

| Constant | Value | Defined in |
|---|---|---|
| `RESOLVER_QUERY` | `0x00000001` | §6.4 |
| `RESOLVER_CONTROL` | `0x00000002` | §6.4 |
| `RESOLVER_ALL_ACCESS` | `0x000F0003` | §6.4 |

## Enumerations

| Field | Values | Defined in |
|---|---|---|
| `outcome` | `found`, `notfound`, `unavailable` | §6.6 |
| `validation` | `unvalidated`, `secure`, `insecure`, `bogus` | §6.6 |
| `source` | `local`, `synthetic`, `hosts`, `cache`, `dns` | §6.2 |
| `family` | `any`, `inet`, `inet6` | §6.5 |
| `level` | `absent`, `link`, `addressed`, `routed` | §6.9 |

## Paths and addresses (Peios)

| Item | Value |
|---|---|
| Native socket | `/run/resolvd/resolv.sock` |
| Stub listener | `127.0.0.53:53`, UDP and TCP |
| Network manager socket | `/run/netd/control.sock` |
| Registry key | `Machine\System\Network\Resolver` |
| Shim | `libnss_peios_net.so.2` |
| Compat file | `/usr/etc/resolv.conf`, constant |
