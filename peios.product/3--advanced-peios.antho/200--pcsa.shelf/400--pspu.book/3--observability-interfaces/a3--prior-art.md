---
title: Prior Art
description: The well-known counterparts these three interfaces were shaped against, and where they sit relative to them.
---

The three interfaces here are not novel, and each has a well-known
counterpart whose shape informed it. What follows compares the
*contracts* — this appendix is about wire shapes and the obligations
they place on either side. The eventd TRMP §1.4 compares the systems.

## Log ingestion

The closest relative is journald's native socket: a Unix datagram
socket, world-writable, accepting a self-describing record from any
local process, with no acknowledgement and no notification of loss. The
agreements are substantive — datagram rather than stream, self-asserted
identity, silent drop under pressure, a forwarder bridging programs that
only know standard output.

The differences are three. The record here is MessagePack rather than a
line-oriented key-value text format, because the collector already
carries a MessagePack decoder for event payloads and a second parser
would be a second thing to get wrong. Severity is a boolean rather than
a syslog priority, because a forwarder can distinguish two file
descriptors and inventing eight levels from two would be a guess
presented as data (§3.7). And a batch is a first-class datagram shape
rather than a stream of records, which is what lets a forwarder amortise
the syscall without giving up the datagram's all-or-nothing property.

Classic syslog over `/dev/log` is the older relative, and the departure
from it is the same one journald made: a record with named fields rather
than a formatted line that every consumer re-parses with a regular
expression.

## Metric ingestion

The shape is StatsD's: push, datagram, fire-and-forget, no registration,
sender-named series. It is the opposite of Prometheus's, where the
collector pulls from endpoints it has been configured to know about.

The choice follows from the loss model rather than from taste (§3.9). A
pulling collector must reach every producer on a schedule, which makes
it responsible for their availability; pushing keeps a slow or dead
producer invisible except for the gap it leaves.

What is taken from the Prometheus data model rather than from StatsD is
the *identity* of a series: a name plus a set of labels, with each
distinct label combination a distinct series, and the cardinality
warning that comes with it (§3.10). The histogram is Prometheus's
cumulative-bucket form, including the property that the top bucket is an
overflow whose contents are counted but not located.

Two things are deliberately absent. There is no text exposition format,
because nothing scrapes. And there is no summary type — a producer that
has already computed its own quantiles cannot submit them, because
quantiles do not aggregate and a stored one could not be combined with
another (§3.25).

## The query interface

The unusual choice here is having a query *language* at all.

journald exposes a cursor and a set of field matchers, and computation
belongs to the client. The Windows Event Log exposes XPath over an XML
representation. Prometheus exposes PromQL, a genuine language, but only
for metrics. This interface puts one language over all three data types,
with a shared clause vocabulary and per-type modes (§3.18).

The reason is access control. Filtering, grouping and aggregation must
happen on the side that knows what the caller may see, because a count
computed by a client is a count of what the client was given and a count
computed by the collector can be a count of what the client is entitled
to (§3.28). A cursor interface pushes the computation across the trust
boundary and takes the enforcement point with it.

The framing — a length-prefixed MessagePack request, a sequence of
chunked result messages, one terminal message — is unremarkable and
deliberately so. What it does not have is more interesting: no version
field (§3.29), no error codes (§3.16), no multiplexing (§3.14), and no
cursor. A query is one connection, and paging is `SKIP` and `TAKE` over
a total order (§3.21) rather than an opaque token the collector must
keep state for.

## Where these interfaces sit

| Concern | Where it is specified |
|---|---|
| Event emission and the ring-buffer transport | PSPK |
| Event types and payload schemas | the emitting subsystem's own documentation |
| Tokens, SIDs and Security Descriptors | PCDS, and the Peios Kernel TRM |
| Forwarding a service's output | the peinit TRM |
| Storage, indexing, retention, query planning | the collector's own design; for the mainline one, the eventd TRMP |
