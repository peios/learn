---
title: Counters
description: The seven counters status reports, exactly what moves each one, and what resets them.
---

The engine keeps seven counters, reported by `status` (§5.3). Each is an
unsigned 64-bit count from zero at startup.

| Counter | Goes up by one for |
|---|---|
| `queries` | Every `resolve`, `lookup` and `reverse` request, and every stub query — including those whose name does not parse [*engine-counters.queries] |
| `synthetic` | Every task answered by a synthetic name (§4.2), including `.local`'s `notfound`; an `any` lookup of `localhost` adds two [*engine-counters.synthetic] |
| `cache_hits` | Every candidate found live in the cache (§4.5), including a `notfound` hit that moves on to the next candidate [*engine-counters.cache-hits] |
| `upstream_sent` | Every transaction sent, UDP or TCP, including TCP retries [*engine-counters.upstream-sent] |
| `upstream_answered` | Every matching reply (§4.8), whatever its response code, including a truncated one [*engine-counters.upstream-answered] |
| `upstream_failed` | Every failed transaction (§4.6): a timeout, a transport failure, or a reply with a response code other than `NOERROR` and `NXDOMAIN` [*engine-counters.upstream-failed] |
| `refused` | Every question refused at the in-flight ceiling (§4.6) [*engine-counters.refused] |

`status` and `flush` requests are not counted, and nothing on the netd
channel is. [*engine-counters.status-flush-and-netd-not-counted]

Because a non-matching UDP datagram leaves its transaction to time out
(§4.8), it shows up as one `upstream_failed` and no `upstream_answered`.
A reply with `SERVFAIL` shows up in both.

The counters are reset only by a restart. `flush` does not reset them. [*engine-counters.reset-only-by-restart]
