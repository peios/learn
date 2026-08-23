---
title: What an Authority Must Not Trust
description: Nothing a client sends is trusted. Peer identity comes from the kernel, and every asserted field is a proposal to be constrained.
---

Nothing a client sends is trusted. This section states the rule once,
because every field in §2.7 is subject to it.

## Peer identity

An authority MUST establish the connected peer's identity from the
**connected socket**, by reading the peer's token from the kernel. It
MUST NOT take the peer's identity from any message body, because there
is no field in which a client could put it that the client could not
also lie in.

An authority MUST NOT use `SO_PEERCRED` for this purpose. It answers a
similar-looking question and is the wrong answer: it returns the
*projected* UID, which cannot distinguish an authenticated principal
from an unauthenticated process running under the same projection, and
carries none of the token's SIDs, groups, integrity level or privileges.

> [!NOTE]
> On Peios many principals project to the same identifier, so a
> projected UID frequently identifies nobody in particular. Two
> different principals can share one. The peer token is the only thing
> that answers "who is this?" exactly.

## Logon type

`LogonStart.logon_type` is a **proposal**, not an instruction.

Only the caller knows whether an inbound connection is an interactive
shell or a batch command, so the caller has to be the one to say. But an
authority MUST constrain the proposal against what that verified peer is
permitted to request. Otherwise anything that can reach the socket can
mint itself an interactive session, and the logon type — which access
control decisions depend on — becomes a value chosen by the least
trusted party in the exchange.

## Identifier

The identifier names the principal a logon is *for*. It is a claim about
who is being authenticated, and it is what the subsequent credential
exchange exists to test. An authority MUST NOT treat an identifier as
established until authentication has succeeded.

## Everything else

`tty` and `remote_host` are unverified context. An authority MAY record
them, MAY use them in policy, and MUST NOT treat them as established
facts. A client that lies about its remote host is not prevented from
doing so by this protocol.

## Access to the socket

Access to the logon socket MUST be controlled by a security descriptor.

It MUST NOT be controlled by process integrity level. PIP *can* gate a
socket, but using it here would require every future caller — a
graphical greeter, a web console, a remote access daemon — to be signed
at high trust merely to *collect a password*. Collecting a credential is
not a privileged act; deciding whether it is correct is, and that
decision happens on the other side of the socket.

Rate limiting is defence in depth. It is not the access control, and an
authority MUST NOT rely on it as such.
