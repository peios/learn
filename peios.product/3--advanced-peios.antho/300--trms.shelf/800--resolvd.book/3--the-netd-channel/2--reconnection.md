---
title: Reconnection and Backoff
description: When resolvd tries to reach netd again, the exact backoff sequence, what it logs, and what it keeps answering with while netd is away.
---

Failure and reconnection are covered by PSPU §6.9. resolvd's backoff
starts at 0.5 seconds and doubles to a ceiling of 10 seconds.

## The backoff sequence [*netd-reconnect.backoff-sequence]

The first attempt is made during startup, before readiness (§2.2). Each
failed attempt schedules the next one the current backoff later, then
doubles the backoff up to 10 seconds. Measured from a first attempt that
fails, attempts are made at:

| Attempt | Time after the first |
|---|---|
| 2 | 0.5 s |
| 3 | 1.5 s |
| 4 | 3.5 s |
| 5 | 7.5 s |
| 6 | 15.5 s |
| 7 and later | every 10 s |

## The unreachable warning [*netd-reconnect.first-failure-logged-once]

A failed attempt made before any connection has succeeded is logged as
`netd not reachable (<error>); retrying` when it is the first failure,
and not logged otherwise. Together with the rule after a loss (below),
the warning is written at most once in the life of the process: for the
first failure, when that failure comes before the first successful
connection. A resolvd whose first attempt succeeds never writes it.

## A successful connection resets the backoff [*netd-reconnect.success-resets-backoff]

A successful connection resets the backoff to 0.5 seconds.

## After a loss

When an established channel is dropped (§3.1):

- the next attempt is due 0.5 seconds later and the backoff is reset to
  0.5 seconds; if that attempt fails, the following ones come 0.5, 1, 2,
  4, 8 and then every 10 seconds after it; [*netd-reconnect.sequence-after-loss]
- the `netd not reachable` warning is not logged for the failures that
  follow, however many there are; the `lost the netd channel;
  reconnecting` line that preceded them is the record. [*netd-reconnect.no-unreachable-warning-after-loss]

### A refused subscription loops every half second [*netd-reconnect.refusal-reconnects-every-half-second]

A netd that accepts the connection and then answers the subscription
with an error is a connection that succeeds and is then lost, so the
backoff never grows: resolvd reconnects about every half second, logging
`subscribed to netd` at info level and then two warnings each time
(§9.4).

## Disconnected from netd [*netd-reconnect.state-kept-while-disconnected]

Losing netd changes nothing in the engine. The scopes from the last
snapshot, the hostname taken from it, and every cached answer stay in
use until the next snapshot replaces them; questions are answered
exactly as before, and the servers in those scopes are still asked.
`status` reports `netd` as `false` (§5.3).

## Before the first snapshot [*netd-reconnect.no-snapshot-yet-behaviour]

When resolvd has never received a snapshot it has no scopes. It answers
synthetic and static names, uses the fallback servers if any are
configured, and answers everything else `unavailable` (§4.4).
