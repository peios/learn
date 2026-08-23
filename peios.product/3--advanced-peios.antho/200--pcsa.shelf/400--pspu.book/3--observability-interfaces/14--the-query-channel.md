---
title: The Query Channel
description: The query socket — one query per connection, the identity captured at connect, and why no credentials cross it.
---

A collector MUST expose an `AF_UNIX` `SOCK_STREAM` socket for queries,
protected by a Security Descriptor as §3.3 requires.

One socket serves all three data types. The mode a query runs in —
events, logs or metrics — is determined by parsing the query string
(§3.18), never by the transport, so a client needs no connection setup,
no mode selection, and no separate endpoint per data type.

## One query per connection

A connection carries exactly one query. A client that wants two
concurrent queries opens two connections.

A collector MUST close the connection after the terminal message of a
non-streaming query (§3.16), and MUST treat a client disconnect as
cancellation of a streaming one.

> [!NOTE]
> This is the opposite of the identity-lookup channel in PGSS §2.14,
> which multiplexes tagged requests over one connection. The reason is
> the shape of the work rather than a difference in taste: a lookup is
> small, uniform and answered in one message, so correlating many on one
> connection saves real cost. A query may run for thirty seconds, may
> stream indefinitely, and may be cancelled — and every one of those is
> expressed by the connection itself, with no correlation identifier and
> no cancellation message to specify.

## Identity

A collector MUST establish the client's identity from the connected
socket, before executing anything, by obtaining the peer's token. This
is possible here and not on the ingestion channels, and it is the whole
reason the query channel is a stream (§3.3).

The token is captured **once**, at connection time, and is a snapshot. A
client whose privileges change while a query runs — and in particular
while a streaming query runs, which may be indefinitely — is evaluated
throughout against the token it connected with.

If a collector cannot obtain the peer token, it MUST refuse the query.
It MUST NOT execute a query for an unidentified caller, and MUST NOT
fall back to any other means of identifying one.

## No credentials cross this channel

There is no message with which a client offers a credential and none
with which a collector asks for one. Identity is established from the
connection and from nothing else.

## Concurrency

A collector MUST bound the number of queries it will execute at once,
and MUST reject a query beyond the bound with an error rather than
queueing it behind the others.

The streaming bound is the lower of the two and is enforced separately,
because a streaming query holds its resources for as long as its client
stays connected while an ordinary one holds them for at most a timeout
(§3.16).

> [!NOTE]
> §3.A gives the mainline value and adjustable range
> for this bound and every other in this chapter.

Both bounds are global. Neither is per-client, because a collector
cannot attribute connections to a caller beyond the token it has, and
one client MAY therefore occupy every slot. A collector MUST NOT allow
that to affect ingestion: queries and ingestion are separate channels
precisely so that exhausting one cannot exhaust the other (§3.3).
