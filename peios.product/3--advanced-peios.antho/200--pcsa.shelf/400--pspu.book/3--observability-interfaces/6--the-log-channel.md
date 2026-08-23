---
title: The Log Channel
description: The log ingestion socket — its datagram ceiling, the receive queue as the only buffer, and what reachability a producer may assume.
---

A collector MUST expose an `AF_UNIX` `SOCK_DGRAM` socket for log
ingestion, protected by a Security Descriptor as §3.3 requires.

## The datagram ceiling

A collector declares a maximum accepted datagram size, the **log
datagram ceiling**. A collector MUST receive log datagrams into a buffer
of at least that size, and MUST discard a datagram the kernel reports as
truncated rather than storing the prefix that fitted.

A producer MUST NOT send a log datagram larger than the ceiling. One
that does is discarded whole, taking every record in it, and the
producer is not told (§3.4).

> [!NOTE]
> §3.A gives the mainline value and adjustable range
> for this bound and every other in this chapter.

**There is no mechanism by which a producer can learn the ceiling.** A
datagram channel has no reply, so a producer either knows the value out
of band or assumes the mainline default. A collector that lowers the
ceiling below the mainline value MUST expect producers to keep sending
at the old one, and silently losing what they send. Raising it is safe;
lowering it is a change to the contract with every producer on the
system.

## The receive queue is the buffer

A collector MAY enlarge the socket receive queue, to at most four times
the datagram ceiling. It MUST NOT buffer beyond it.

That queue is the only cushion between a producer and the collector's
storage. While a collector is committing a batch it is not draining the
socket, and datagrams arriving in that window occupy the queue; when the
queue fills, they are discarded. This is the designed degradation
(§3.4), not a failure to be tuned away — a larger buffer moves the
threshold without changing what happens at it, and an unbounded one
converts data loss into memory exhaustion.

## Reachability

Every process that produces output is a log producer, including
processes that have not been written with a collector in mind.

The mainline arrangement is that the service manager holds each
service's standard output and standard error at fork and forwards what
it reads (peinit TRM). It is **not** a privileged producer: it uses this
socket, this record format and these rules like anything else, and its
role is to bridge programs that write to a file descriptor into an
interface that expects datagrams.

A producer that wants control over its own metadata MAY write to the
socket directly instead, with no registration, negotiation or setup of
any kind. Direct submission and forwarded submission are the same
interface; nothing distinguishes them on the wire, and a collector MUST
NOT treat them differently.
