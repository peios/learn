---
title: Loss and Backpressure
description: The decision that shapes both ingestion channels — a producer is never stalled, so data may be lost — and what a collector must not do about it.
---

The single decision that shapes both ingestion interfaces is this:
**a producer is never slowed down, and never told that a record was
lost.**

## The obligation

A collector MUST NOT exert backpressure on a producer. A producer MUST
NOT stall, block, retry or otherwise change its behaviour because a
collector is slow, busy, or absent.

The consequence is accepted openly. When a collector cannot drain an
ingestion socket as fast as producers fill it, the kernel discards
datagrams. Neither party is notified. A collector MUST NOT report the
loss to the producer, because there is no reply message on a datagram
channel and adding one would reintroduce the coupling this rule exists
to prevent.

## Why loss is acceptable here

A lost log line is an inconvenience. A lost metric sample is a visible
gap in a chart. Neither is a failure of the system, and neither is worth
the cost of the alternative — which is either blocking the producer or
buffering without bound, and the second is only the first with a delay.

Events are the counter-example, and the reason the boundary between
events and logs matters. An event may be a security audit record whose
absence is itself the finding, so events do not travel on either
interface in this chapter: they travel through KMES, where loss is
detected, bounded and recorded. A program with data that must not be
lost emits an event; a program with output for a human to read writes a
log.

> [!NOTE]
> This is the practical test for producers deciding where output belongs.
> If you would want to know that a record went missing, it is not a log
> and not a metric.

## What a collector must not do about it

A collector MUST NOT emit an event, write a log entry, or perform any
other work proportional to the volume of malformed or unwanted input it
receives.

Ingestion input is unauthenticated and arrives from arbitrary local
processes (§3.3). A collector that reacted to bad input — by logging it,
by counting it in a way a client can observe, or by emitting a
diagnostic event — would hand every process on the system an
amplification primitive: a cheap malformed datagram producing an
expensive durable record. Silence is the defence.

The rule binds only on responses to *input*. A collector MAY record its
own internal conditions, and the mainline collector records several
(eventd TRMP §2.6).

## Ordering and duplication

A collector MUST NOT assume that datagrams arrive in the order they were
sent, and MUST NOT reorder or deduplicate the records inside one. A
producer MUST NOT assume that submitting two datagrams in order causes
them to be stored in that order; the timestamp field (§3.7, §3.11) is
the only ordering a producer controls.

Records are not deduplicated. A producer that submits the same record
twice has produced two records.
