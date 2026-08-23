---
title: The Identity Channel
description: /run/ident.sock — its path, access control, framing, multiplexing and bounds, and why it carries no descriptors.
---

## Socket

An authority MUST listen on a `SOCK_STREAM` Unix domain socket at:

```
/run/ident.sock
```

The path is normative, for the same reason `/run/logon.sock` is: a name
resolver linked into every process on the system cannot be asked to find
it by configuration.

An authority MUST listen on both sockets. Offering one without the other
is not conformance — a system whose principals cannot be named is as
broken as one whose principals cannot sign in.

## Access control

The socket MUST carry a security descriptor granting connect access to
every principal that runs ordinary programs.

This is the opposite posture to `/run/logon.sock`, and deliberately so.
A descriptor that withheld connect access would not protect anything: it
would make `ls -l` print numbers for the principals it excluded, while a
principal who *can* connect learns the same names either way.
Restriction, where an authority wants it, belongs on individual fields
(§2.16) — not on reaching the socket at all.

## Framing

Messages use the header, magic, version, size limit and body
extensibility rules of §2.6 without modification. The message types
served here are disjoint from those of the logon socket (§2.A).

A message of one socket's range arriving on the other MUST be refused.
An authority MUST NOT serve a `Lookup` received on `/run/logon.sock`,
and MUST NOT serve a `LogonStart` received on `/run/ident.sock`.

> [!NOTE]
> Sharing the magic is what makes that a clean refusal rather than a
> parse failure. A peer connected to the wrong socket gets "this message
> is not served here" from byte six, instead of discovering the mistake
> several fields into a structure it has misread.

## Multiplexing

A connection carries any number of requests. A client MAY have more than
one outstanding at a time, and an authority MAY answer them in any
order.

Every request carries a `tag`, a `u32` chosen by the client, and its
reply carries the same value. The tag is **in the message body**, not
the header, so that the header of §2.6 is unchanged.

A client MUST NOT reuse a tag while a request bearing it is outstanding.
An authority MUST echo the tag it received and MUST NOT interpret it
otherwise.

A client MUST NOT assume replies arrive in request order. An authority
that answers strictly in order is conformant; a client that depends on
it is not.

> [!NOTE]
> The contrast with §2.5 is deliberate rather than inconsistent. A logon
> connection exists for one logon and is discarded, so multiplexing
> would buy nothing and a correlation identifier would only add
> something to forge. A lookup connection is opened by a name resolver
> that may issue thousands of requests, and the identifier costs four
> bytes.

## Concurrency and bounds

An authority MUST serve connections concurrently, and MUST NOT let a
slow answer on one connection delay answers on another.

An authority MUST bound the number of connections it will accept and the
number of requests it will hold outstanding per connection, and SHOULD
refuse further requests on a connection that exceeds the second rather
than closing it.

An authority MUST NOT wait indefinitely for a source. A request that
cannot be answered within the authority's own bound MUST be answered
`Unavailable` (§2.18). The bound is on the request, not on each source
consulted: an authority that walks several sources in turn MUST NOT let
the total exceed what it would have allowed one.

## No descriptor passing

Nothing is transferred over this channel by descriptor. An authority
MUST ignore ancillary data received here.

## Peer identity

An authority that restricts any field (§2.16) MUST establish peer
identity from the connected socket's peer token, as §2.4 requires, and
MUST NOT take it from a message body.

An authority that restricts no field MAY skip establishing peer
identity, since it would make no decision with it.
