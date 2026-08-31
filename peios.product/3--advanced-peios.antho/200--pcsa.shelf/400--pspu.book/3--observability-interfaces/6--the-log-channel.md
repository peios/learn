---
title: The Log Channel
description: The log ingestion socket — its datagram ceiling, the receive queue as the only buffer, and what reachability a producer may assume.
---

A collector MUST expose an `AF_UNIX` `SOCK_DGRAM` socket for log
ingestion, protected by a Security Descriptor as §3.3 requires.

## The datagram ceiling

A collector declares a maximum accepted datagram size, the **log
datagram ceiling**. The portable ceiling is **262144 bytes**. Every
collector MUST accept a whole datagram up to that size, and every
portable producer MUST bound its encoded datagrams to that size without
discovering collector configuration. A collector MAY accept more, but a
producer MUST NOT depend on that when implementing this interface.

A collector MUST receive log datagrams into a buffer of at least its
declared ceiling, and MUST discard a datagram the kernel reports as
truncated rather than storing the prefix that fitted.

A producer MUST NOT send a log datagram larger than the ceiling. One
that does is discarded whole, taking every record in it, and the
producer is not told (§3.4).

> [!NOTE]
> §3.A gives the mainline value and upward-adjustable range
> for this bound and every other in this chapter.

No capability exchange is needed. The 262144-byte floor is part of the
wire contract rather than a tunable assumption shared out of band.
Raising a collector's ceiling is a local extension; lowering it below
the portable ceiling is non-conforming.

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
