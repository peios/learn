---
title: The Channel
description: The PSI socket, its access control, why connections are long-lived, and what happens when one fails.
---

## Socket

An authority that federates over PSI MUST listen on a `SOCK_STREAM` Unix
domain socket.

Unlike PGSS Logon's path, this one is **not normative**. PSI is not a
conformance requirement (§2.1), and an authority that offers it may put
it where it likes provided its sources are told. Mainline's is
`/run/psi.sock`.

## Access control

The socket SHOULD carry a security descriptor. It is **DoS protection
and nothing more**, and an implementation MUST be written as though it
were absent.

The reason is that the socket cannot be the boundary. What establishes a
source's identity is the peer's token (§2.9), which is checked on every
connection. A descriptor that kept casual traffic away would be a
convenience; a descriptor *relied upon* would be a second, weaker access
control that someone will eventually assume is doing the work.

An authority MUST therefore bound the number of unregistered connections
it will hold open, and the time it will wait for a registration,
independently of any descriptor.

> [!NOTE]
> An unauthorised peer is refused at the identity check, which is cheap,
> and the connection cap bounds what it can occupy in the meantime. That
> is the whole of what the descriptor's absence costs.

## Long-lived connections

A source's connection persists for the life of the source and carries
every logon routed to it.

An authority MUST bound the number of registered sources and the number
of concurrent conversations per source. A source MUST bound the
conversations it will track, and MUST NOT depend on the authority's
bookkeeping to do it — a source that trusted the authority's limit would
be trusting a bound it cannot verify.

## Failure

A framing error is **fatal to the connection**, not to a conversation.
Once a message has failed to parse there is no way to know where the
next one starts, so both parties MUST tear the connection down rather
than attempt resynchronisation.

A failed write is likewise fatal. A partial write desynchronises the
stream just as a bad frame does, and treating it as a per-conversation
error would leave a corrupt connection in use.

Ordinary semantic failures — an unknown principal, a bad credential, a
refused logon — are **not** connection failures. They are `Refusal`
messages (§2.13) and the connection continues.
