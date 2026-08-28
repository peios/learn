---
title: Peer Identity
description: The manager establishes every client's identity from the kernel, captured once when the connection is accepted, and a client can never assert who it is.
---

The manager MUST establish the identity of every client from the kernel.
There is no credential exchange in this protocol, and a client MUST NOT
be able to assert who it is.

## Obtaining the identity

On accepting a connection, the manager MUST obtain the peer's token
through the kernel's peer-identity facility for connected local sockets
(the Peios Kernel TRM §3.5). The token is captured by the kernel when
the client connects; nothing in this protocol carries it, and a client
has no way to supply one.

The token reflects the identity the client was **acting under when it
connected**. A client that is impersonating another principal is
therefore captured as the principal it is impersonating, not as its own
service identity — which is the intended behaviour: access decisions
reflect the identity a client is actually acting under.

## When it is captured

The manager MUST capture the identity once, when the connection is
accepted, and MUST use that identity for every command on the
connection.

A client MUST NOT expect a change of identity mid-connection to affect
authorisation. A client that needs to act under a different identity
MUST open a new connection.

> [!NOTE]
> One identity per connection is what keeps a command sequence coherent.
> A job started under one identity cannot be steered by a later command
> issued under another on the same connection, every command on a
> connection is attributable to a single principal, and the manager
> never has to decide which of two identities an in-flight operation
> belongs to. The rule is a property of this protocol.

## Failure

If the manager cannot obtain the peer's identity, it MUST close the
connection without a response. There is no error code, because the
manager has no basis on which to decide whether this caller may be told
anything at all.

A client MUST treat an immediate close with no response as a refusal.
This is the same observable outcome as exceeding the connection limit
(§4.4), and a client cannot distinguish the two — deliberately, since
distinguishing them would tell an unauthenticated caller about the
manager's state.

## The identity is not a UID

The manager MUST NOT use the peer's UID or GID as an authorisation
input. Identity on a Peios system is a token, and the token is what the
kernel attests.
