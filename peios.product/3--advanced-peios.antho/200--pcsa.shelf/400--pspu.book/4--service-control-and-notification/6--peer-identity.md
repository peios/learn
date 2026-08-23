---
title: Peer Identity
description: The manager establishes every client's identity from the kernel, at connect, and a client can never assert who it is.
---

The manager MUST establish the identity of every client from the kernel.
There is no credential exchange in this protocol, and a client MUST NOT
be able to assert who it is.

## Obtaining the identity

On accepting a connection, the manager MUST obtain the peer's token from
the kernel. On Peios this is `kacs_open_peer_token`, which returns a
token descriptor for the peer.

The token obtained is the peer **thread's effective token at the moment
of the call**. A client that is impersonating another principal is
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
> Capturing once is what makes the identity meaningful. A per-command
> capture would evaluate each command against whatever the peer happened
> to be at the moment the manager got round to reading it, which is a
> race a client could steer.

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
