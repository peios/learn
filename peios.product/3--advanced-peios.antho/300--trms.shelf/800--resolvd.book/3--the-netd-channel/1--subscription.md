---
title: Subscription
description: How resolvd subscribes to netd's DNS snapshots, reads the stream, and what ends the subscription.
---

The channel is the `subscribe` request of PSPU §6.9, on netd's control
socket. This chapter describes resolvd's end of it; what netd puts in a
snapshot and when it sends one is described in the netd TRM.

## Connecting

When a connection attempt is due (§3.2), resolvd:

1. connects to `/run/netd/control.sock`;
2. sets a two-second write timeout and writes the `subscribe` request in
   netd's framing — a four-byte little-endian length and a MessagePack
   map;
3. switches the socket to nonblocking mode. [*netd-subscribe.connect-and-send-subscribe]

A failure at any step is a failed attempt. [*netd-subscribe.any-step-failure-is-failed-attempt] On success resolvd logs
`subscribed to netd`, discards anything buffered from an earlier
connection, and resets its backoff (§3.2). [*netd-subscribe.success-logged-and-backoff-reset] The first snapshot arrives as
an ordinary read on the channel.

resolvd writes nothing more on the channel. [*netd-subscribe.writes-only-the-request] The request needs netd's
`NETWORK_QUERY` right for resolvd's account; whether that is granted is
netd's decision.

## Reading the stream

When the channel is readable, resolvd reads everything available and
then takes every complete frame from what it holds, in order:

| Frame | What resolvd does |
|---|---|
| A `snapshot` reply | Applies it (§3.3). Several in one read are applied one after another, so the last wins. [*netd-subscribe.snapshots-applied-in-order] |
| An error reply | Logs `netd refused the subscription: <message>` and drops the channel. [*netd-subscribe.error-reply-drops-channel] |
| Any other well-formed reply | Ignores it. [*netd-subscribe.other-replies-ignored] |
| A payload that does not decode | Logs `netd sent something unreadable: <error>` and drops the channel. [*netd-subscribe.undecodable-payload-drops-channel] |
| A length above 65 536 bytes | Drops the channel without reading further. [*netd-subscribe.oversized-frame-drops-channel] |

A partial frame stays buffered until the rest arrives. [*netd-subscribe.partial-frame-buffered] End of file, or
any read error other than `EINTR` or `EAGAIN`, drops the channel. [*netd-subscribe.eof-or-read-error-drops-channel]

Dropping the channel closes the socket, discards the buffer, logs
`lost the netd channel; reconnecting`, and schedules a reconnection
(§3.2). [*netd-subscribe.drop-logged-and-reconnect-scheduled] Snapshots already taken from the same read are applied before
the channel is dropped.
