---
title: The Two Channels
description: Why the notification channel is a datagram socket and the control channel a stream, and how a caller reaches either.
---

The two channels differ in almost every respect, and the differences are
deliberate.

| | Control | Notification |
|---|---|---|
| Socket type | `SOCK_STREAM` | `SOCK_DGRAM` |
| Who connects | The client | Nobody; a service sends |
| Addressing | A fixed path | A path given to each service |
| Direction | Request and response | One-way |
| Framing | Newline-delimited JSON | `KEY=VALUE` lines |
| Identity | The peer's token, at connect | The sender's kernel-attested PID |
| Authorisation | An access check per command | Membership: is the sender this service? |
| Loss | None. A stream, or an error | Possible. A datagram may be dropped |
| Ordering | Guaranteed within a connection | Not guaranteed |

## Why the notification channel is a datagram socket

A service reporting on itself must not be able to block the manager, and
must not block itself. A stream socket gives both parties a queue that
fills, and a service writing into a full queue either blocks — hanging a
service on the manager's scheduling — or gets an error it has to handle
in the middle of doing something else.

A datagram socket has neither problem. A send either goes or is dropped,
and the manager can drain at whatever rate it manages. The cost is that
a notification can be lost, which is why nothing in §4.19 is a
transaction: every field is either idempotent or a statement of current
condition, and a service that needs a lost keepalive to have arrived
sends another one.

## Why the control channel is a stream socket

A command has an answer, and a client waiting for one needs to know it
did not arrive rather than assuming. It also needs framing: a request
can be large, and a response certainly can.

## Reaching either socket

Both sockets are protected by the Security Descriptor on the socket's
own inode, and a party that may not reach the socket is refused when it
connects or sends, before any content is exchanged.

The manager MUST NOT rely on POSIX mode bits for this. On a Peios system
access to a filesystem object is routed through its Security Descriptor,
mode bits are not consulted, and a `chmod` on either socket has no
effect whatever.

The manager MUST ensure that each socket, and each directory containing
one, carries a Security Descriptor that admits the parties intended to
use it. A socket created where nothing inheritable applies acquires no
descriptor, and an object with no descriptor is denied to every caller —
so a manager that leaves this to chance produces a socket nobody can
reach, including principals its own default policy grants access to.

> [!NOTE]
> The failure is quiet in both directions and neither direction
> announces itself. A socket in a permissive place is reachable by
> anything, and a socket in a bare one is reachable by nothing, and in
> both cases the manager binds successfully, reports itself ready, and
> serves no one it meant to.
