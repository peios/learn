---
title: The Notification Channel
description: The datagram socket a service reports on itself over — how it is addressed, how delivery works, and the bounds on it.
---

A service reports on itself over a Unix `SOCK_DGRAM` socket the manager
binds and holds for the lifetime of the system.

## Addressing

The manager MUST make the socket's path available to each service it
starts, in the `NOTIFY_SOCKET` environment variable, set in the service
process's environment before exec.

The path is not part of this contract, and a service MUST NOT hardcode
one. The manager MAY bind one socket for all services or one per
service; a service cannot tell and MUST NOT depend on either.

The manager MUST set `NOTIFY_SOCKET` unconditionally, for every service
it starts, whatever readiness protocol that service uses. A service uses
this channel for keepalives, status, timeout extension and the
descriptor store as well as for readiness, and a manager that set the
variable only for services expected to signal readiness would make the
rest unreachable.

The manager MUST NOT allow `NOTIFY_SOCKET` to be overridden by any
configurable environment layer. A service that could override it would
silently disable its own supervision.

## Direction and delivery

The channel is one-way. The manager does not reply, and a service MUST
NOT wait for one.

Delivery is not guaranteed. A datagram MAY be dropped, by the kernel
under load or by the manager. Every field in §4.19 is therefore either
idempotent or a statement of a current condition, and a service that
needs an effect to have taken hold sends the field again rather than
waiting for an acknowledgement that does not exist.

The manager MUST NOT let this channel exert backpressure on a service.
A service MUST NOT be able to block by sending, and the manager MUST NOT
require a service to slow down.

## Bounds

The manager MUST accept a datagram of at least the size in §4.A, and
MUST accept at least the number of file descriptors in §4.A in one
datagram's control message.

The manager MUST detect a datagram that exceeded either bound and MUST
reject the whole datagram (§4.17). It MUST NOT process a truncated
datagram: a truncation can leave a tail that parses as a complete,
valid line, which would apply a field the sender did not send.

A service MUST NOT send a datagram exceeding either bound.
