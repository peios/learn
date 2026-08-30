---
title: Three Channels
description: Two datagram sockets carrying data inward and one stream socket carrying it out — why the split, and how each is protected.
---

A collector listens on three `AF_UNIX` sockets. Two carry data inward,
one carries it out.

| Channel | Socket type | Direction | Section |
|---|---|---|---|
| Log ingestion | `SOCK_DGRAM` | producer to collector | §3.6 |
| Metric ingestion | `SOCK_DGRAM` | producer to collector | §3.9 |
| Query | `SOCK_STREAM` | request and response | §3.14 |

The pathnames are configuration and this chapter does not fix them. A
collector MUST serve each interface on a distinct socket; it MUST NOT
multiplex two of them onto one.

## Why ingestion is datagram

Each submission is an independent message. A datagram either arrives
whole or does not arrive, so there is no framing to get wrong, no
length prefix to parse, no partial read to reassemble, and no connection
state to keep for a producer that submits one line an hour. The record
boundary is the datagram boundary.

The property that matters more is that a datagram socket **cannot exert
backpressure**. When the receive queue is full the kernel discards the
datagram and the sender proceeds. That is the behaviour §3.4 requires,
and choosing a stream socket would make it unachievable: a full stream
buffer blocks the writer, which is precisely the outcome this design
forbids.

## Why the query channel is a stream

A query result is arbitrarily large, is delivered in several messages,
and must not be silently truncated — the opposite requirements. It also
needs a caller identity, and a peer token can be obtained from a
connected stream socket. Both push the same way.

## Separation

The three channels are separated for the same two reasons.

The first is **admission**. Each listening socket has its own receive
queue. Log volume is orders of magnitude above query volume on any
normal system, and a burst of either must not delay the other. Three
sockets means three populations of caller that cannot starve one
another, whatever load any of them is under.

The second is **access control**. The service manager alone writes the
log channel, while service processes write the metric channel under
their own conveyed identities; the set that may read either is
different again. Those want different Security Descriptors, and a
descriptor is a property of a socket.

The separation is **not** for isolation. One collector serves all three,
so a defect or a hang in any of them reaches the others regardless, and
this chapter does not pretend otherwise.

## Protecting the channels

A collector MUST protect each socket with a Security Descriptor.

The log socket descriptor MUST deny `FILE_WRITE_DATA` to the Service
logon group before allowing SYSTEM. The service manager runs as SYSTEM
without the Service group; every service it launches, including a
SYSTEM service, carries that group. The ordered deny therefore makes
the service manager the log broker without making every SYSTEM service
one (§3.6).

The metric socket descriptor is coarse admission only. Every metric
datagram also carries a KACS sender token and every metric name is
authorized for `EVENTD_PUBLISH` (§3.9).

A collector MUST NOT rely on the socket's POSIX mode bits for this. On
Peios an access decision is routed through the object's Security
Descriptor, not through mode bits, so a mode set on a socket pathname
does not restrict anything; and an inode created without a descriptor is
denied to every caller, so a collector that binds a socket into a
directory carrying no inheritable ACEs produces a socket nothing can
reach. A collector MUST establish the descriptor on each socket before
it begins accepting on it.
