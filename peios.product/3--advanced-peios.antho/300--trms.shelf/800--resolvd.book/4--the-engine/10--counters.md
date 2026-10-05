---
title: Counters
description: The seven counters status reports, exactly what moves each one, and what resets them.
---

The engine keeps seven counters, reported by `status` (§5.3). Each is an
unsigned 64-bit count.

## What each counter counts

| Counter | Goes up by one for |
|---|---|
| `queries` | Every `resolve`, `lookup` and `reverse` request that passes the access check, and every stub query accepted at the door — including those whose name does not parse [*engine-counters.queries] |
| `synthetic` | Every task answered by a synthetic name (§4.2), including `.local`'s `notfound`; an `any` lookup of `localhost` adds two [*engine-counters.synthetic] |
| `cache_hits` | Every candidate found live in the cache (§4.5), including a `notfound` hit that moves on to the next candidate [*engine-counters.cache-hits] |
| `upstream_sent` | Every transaction started, UDP or TCP, including TCP retries. It is counted before the socket is opened, so a transaction whose socket cannot be opened, connected or sent on (§4.7) counts here as well as in `upstream_failed`, though nothing reached the wire [*engine-counters.upstream-sent] |
| `upstream_answered` | Every matching reply (§4.8), whatever its response code, including a truncated one [*engine-counters.upstream-answered] |
| `upstream_failed` | Every failed transaction (§4.6): a timeout, a transport failure, or a reply with a response code other than `NOERROR` and `NXDOMAIN` [*engine-counters.upstream-failed] |
| `refused` | Every question refused at the in-flight ceiling (§4.6) [*engine-counters.refused] |

## What is not counted [*engine-counters.status-flush-and-netd-not-counted]

`status` and `flush` requests are not counted, and nothing on the netd
channel is.

Because a non-matching UDP datagram leaves its transaction to time out
(§4.8), it shows up as one `upstream_failed` and no `upstream_answered`.
A reply with `SERVFAIL` shows up in both. A transaction that could not
be sent shows up in `upstream_sent` and `upstream_failed`, and never in
`upstream_answered`.

## Resetting the counters [*engine-counters.reset-only-by-restart]

The counters start at zero when resolvd starts, and are reset only by a
restart. `flush` does not reset them.
