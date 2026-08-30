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

## The service-manager broker

Every service produces output, including programs that know nothing
about the collector, but service processes do not write this socket.
The service manager holds each service's standard output and standard
error at fork, determines the origin from the pipe it read, and forwards
the resulting records (peinit TRM).

The log socket MUST implement the deny-Service, allow-SYSTEM descriptor
in §3.3. A collector MUST accept log origins from this broker without a
per-record KACS token or AccessCheck. A service can choose the bytes it
writes to its pipe but cannot choose another service's origin.

Direct log submission is not part of this interface. A program that
wants structured, authenticated observability data emits an event or a
metric; it does not bypass the service manager to assert a log origin.
