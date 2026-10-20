---
title: Query Framing
description: Length-prefixed MessagePack in both directions, the inbound request ceiling, and the outbound response target.
---

Every message in either direction is a length-prefixed MessagePack
value:

| Offset | Size | Field | Value |
|---|---|---|---|
| 0 | 4 | `length` | Length of the payload in bytes |
| 4 | `length` | `payload` | The request or response body |

`length` is little-endian, as PSPU §1.2 requires of every integer field
in this document. It counts the payload only; the four bytes of the
prefix are not included.

There is no magic value and no version field. The channel is a Unix
socket at a configured path, so there is no possibility of reaching the
wrong service by accident in the way a shared header guards against
(PSPU §2.7), and versioning is handled as §3.29 describes.

## The two size controls

A collector declares two independent sizes. The **query request
ceiling** is a hard inbound limit. The **query response target** is a
soft outbound batching target. They are separate because an untrusted
client must not be able to force an arbitrarily large allocation merely
by declaring a request length, while a record the collector has already
accepted must remain possible to return.

> [!NOTE]
> §3.A gives the mainline value and adjustable range
> for both sizes and every other bound in this chapter.

**Inbound.** A collector MUST refuse a request whose `length` exceeds
the request ceiling. It MUST do so without reading the payload — the
point of checking the prefix is to avoid allocating for a request that
a malicious or broken client has declared too large — and it MUST send
an error response (§3.16) before closing the connection. A collector
MUST NOT close on an oversized request silently: a bare close is
indistinguishable from a crash, and leaves a client unable to tell that
shortening its query is the remedy.

**Outbound.** A collector SHOULD chunk result records so an ordinary
response does not exceed the response target (§3.16). The target is not
a ceiling: when one complete record would exceed it, the collector MUST
send that record alone in one response rather than split, truncate,
skip, or reject it.

## Every stored record must remain returnable

A collector MUST NOT store a record whose encoded result representation
cannot fit in the protocol's `u32` payload length. This structural
framing bound is the only outbound ceiling.

A single result record is never split across messages (§3.16). A
collector MUST therefore ensure that its accepted record encodings have
a bounded result expansion that fits one frame. It MAY establish that
statically from the protocol's record limits; it need not flatten or
encode each record on the ingestion path merely to check response size.
An implementation MAY encode a large response incrementally after
writing its known length; it need not allocate another buffer as large
as the record.

The ingestion ceilings (§3.6, §3.9) remain independent configuration.
Raising one does not require raising the response target: it merely
makes a single-record response above that target more likely. The
structural `u32` requirement is a property of the wire encodings, not a
configurable coupling between those values.

## Requests

A request is a MessagePack map:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `query` | string | yes | The query string (§3.18). |

A collector MUST send an error response and close the connection if the
payload is not valid MessagePack, is not a map, omits `query`, gives
`query` a non-string value, or contains a duplicate top-level key. It
MUST ignore unrecognised fields that are not duplicates (§3.29).

Unlike the ingestion channels, nothing here is silent. A query client is
identified (§3.14), is one of a bounded number, and is asking a
question, so telling it what went wrong is neither an amplification
vector nor an information leak — with the one exception §3.28 sets out.
