---
title: The Metric Channel
description: The metric ingestion socket, separate from the log socket, and why the collector is a sink rather than a scraper.
---

A collector MUST expose an `AF_UNIX` `SOCK_DGRAM` socket for metric
ingestion, protected by a Security Descriptor as §3.3 requires,
separate from the log socket.

Before its first send, a producer MUST enable `KACS_SO_PASS_TOKEN` on
its persistent sending socket. KACS then attaches the producer's
effective token to every datagram as `KACS_SCM_TOKEN`. A collector MUST
receive with ancillary space for that token and MUST discard the whole
datagram when the token is absent or the data or control message was
truncated.

For every valid record, the collector resolves the metric name's
publication policy and runs KACS AccessCheck for `EVENTD_PUBLISH`
against the conveyed token. A denied record is discarded silently.
Records with other authorized names in the same datagram remain valid.
An implementation MAY cache a verdict by stable token identity, token
modification identity, metric name and policy generation.

The channel works exactly as the log channel does, for the reasons given
there: a declared datagram ceiling, truncated datagrams discarded whole,
a receive queue of at most four times the ceiling, no backpressure, no
notification, and no way for a producer to discover the ceiling (§3.6).

> [!NOTE]
> §3.A gives the mainline value and adjustable range
> for this bound and every other in this chapter.

## A sink, not a collector of its own

The collector is **pushed** to. It MUST NOT scrape an endpoint, read a
kernel interface, or poll anything to obtain metrics; every sample it
holds arrived on this socket because a producer sent it.

What gathers the measurements is a separate concern and a separate
program. A collection agent that reads system counters and submits them
is an ordinary producer here, with no privileged position and no
interface of its own.

> [!NOTE]
> The push direction follows from the loss model rather than from taste.
> A pulling collector must reach every producer on a schedule, which
> makes it responsible for their availability and makes a slow producer
> the collector's problem. Pushing keeps each producer responsible for
> its own submissions and keeps a slow or dead producer invisible to
> everything except the gap it leaves.

## Batching

Batching matters more here than it does for logs. It amortizes both the
datagram and conveyed-token costs. A collection sweep
produces many samples at once — every CPU core, every disk, every
interface — and they share a moment, so a producer SHOULD submit a sweep
as one batched datagram rather than as one datagram per sample.

The rules are the log rules: one map or an array of maps, per-record
validation, and the encoded datagram bounded by the ceiling (§3.8,
§3.12).
