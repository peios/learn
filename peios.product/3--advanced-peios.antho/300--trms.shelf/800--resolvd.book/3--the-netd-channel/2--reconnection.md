---
title: Reconnection and Backoff
description: When resolvd tries to reach netd again, the exact backoff sequence, what it logs, and what it keeps answering with while netd is away.
---

Failure and reconnection are covered by PSPU §6.9. resolvd's backoff
starts at 0.5 seconds and doubles to a ceiling of 10 seconds.

## The sequence

The first attempt is made during startup, before readiness (§2.2). Each
failed attempt schedules the next one the current backoff later, then
doubles the backoff up to 10 seconds. Measured from a first attempt that
fails, attempts are made at: [*netd-reconnect.backoff-sequence]

| Attempt | Time after the first |
|---|---|
| 2 | 0.5 s |
| 3 | 1.5 s |
| 4 | 3.5 s |
| 5 | 7.5 s |
| 6 | 15.5 s |
| 7 and later | every 10 s |

The first failure is logged as `netd not reachable (<error>); retrying`.
Later failures are not logged until a connection has succeeded. [*netd-reconnect.first-failure-logged-once]

A successful connection resets the backoff to 0.5 seconds. [*netd-reconnect.success-resets-backoff]

## After a loss

When an established channel is dropped (§3.1), the next attempt is due
0.5 seconds later and the backoff is reset to 0.5 seconds. If that
attempt fails, the following ones come 0.5, 1, 2, 4, 8 and then every
10 seconds after it. [*netd-reconnect.sequence-after-loss] The `netd not reachable` warning is not logged for
failures that follow a loss; the `lost the netd channel; reconnecting`
line that preceded them is the record. [*netd-reconnect.no-unreachable-warning-after-loss]

A netd that accepts the connection and then answers the subscription
with an error is a connection that succeeds and is then lost, so the
backoff never grows: resolvd reconnects about every half second, logging
two warnings each time (§9.4). [*netd-reconnect.refusal-reconnects-every-half-second]

## While disconnected

Losing netd changes nothing in the engine. The scopes from the last
snapshot, the hostname taken from it, and every cached answer stay in
use until the next snapshot replaces them; questions are answered
exactly as before, and the servers in those scopes are still asked. [*netd-reconnect.state-kept-while-disconnected]
`status` reports `netd` as `false` (§5.3).

When resolvd has never received a snapshot it has no scopes. It answers
synthetic and static names, uses the fallback servers if any are
configured, and answers everything else `unavailable` (§4.4). [*netd-reconnect.no-snapshot-yet-behaviour]
