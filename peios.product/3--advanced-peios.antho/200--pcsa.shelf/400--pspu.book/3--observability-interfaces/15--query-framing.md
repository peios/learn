---
title: Query Framing
description: Length-prefixed MessagePack in both directions, the message ceiling, and the requirement that the ceiling admit every record.
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

## The message ceiling

A collector declares a maximum payload size, the **query message
ceiling**, which bounds messages in both directions.

> [!NOTE]
> §3.A gives the mainline value and adjustable range
> for this bound and every other in this chapter.

**Inbound.** A collector MUST refuse a request whose `length` exceeds
the ceiling. It MUST do so without reading the payload — the point of
checking the prefix is to avoid allocating for a request that a
malicious or broken client has declared too large — and it MUST send an
error response (§3.16) before closing the connection. A collector MUST
NOT close on an oversized request silently: a bare close is
indistinguishable from a crash, and leaves a client unable to tell that
shortening its query is the remedy.

**Outbound.** A collector MUST ensure every response payload it sends is
within the ceiling, chunking result records across messages as §3.16
describes.

## The ceiling must admit every record

A collector MUST NOT operate with a query message ceiling smaller than
the largest record it can store.

A single result record is never split across messages (§3.16), so a
record larger than the ceiling cannot be returned at all — and it cannot
be skipped either, because skipping it would silently misreport what the
store holds. It fails the query, and it fails every query whose range
covers it, for as long as retention keeps it. One oversized record
renders a span of history unreadable.

The two are related by configuration and nothing enforces the relation
automatically: the ingestion ceilings (§3.6, §3.9) bound the largest
record a producer can deposit, and the query message ceiling bounds the
largest that can be handed back. An administrator who raises one MUST
raise the other.

> [!NOTE]
> The mainline defaults do not satisfy this. The log and metric datagram
> ceilings are 262144 bytes and the query message ceiling is 65536, so a
> producer can deposit a log line four times larger than any response
> that could carry it.

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
