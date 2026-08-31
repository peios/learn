---
title: Conformance
description: Every requirement of this chapter collected by role — collector, producer and client — plus what is deliberately not required.
---

A conforming implementation of any role MUST satisfy every requirement
in this chapter. This section collects the obligations that are not tied
to one message.

## A collector

**Serve three separate channels.** Two `SOCK_DGRAM` for ingestion, one
`SOCK_STREAM` for queries, each on its own socket, each protected by a
Security Descriptor established before it accepts anything (§3.3).

**Never exert backpressure.** No producer stalls because of a collector,
under any load, in any failure state (§3.4).

**Never react to input.** No event, no log entry, no client-observable
counter, in response to a malformed, unwanted or excessive submission
(§3.4).

**Authenticate ingestion.** Admit only the service-manager broker on
the log socket; require a complete KACS token on every metric datagram
and authorize every metric name for `EVENTD_PUBLISH` (§3.3, §3.6,
§3.9).

**Validate at the stated scope.** Datagram, record, or field — as §3.8
and §3.12 set out, and no more broadly. In particular a malformed record
MUST NOT cost the valid records batched with it, and a malformed
optional field MUST NOT cost a log record.

**Store what you were given.** A log message byte-for-byte, an event
payload unmodified, a timestamp uncorrected, a histogram's boundaries in
the order sent (§3.8, §3.10, §3.5).

**Preserve gaps.** No interpolation, no backfill, no synthesised sample
(§3.13).

**Identify every query client** from the connection, before executing
anything, and refuse the query if you cannot (§3.14).

**Order totally and deterministically.** Every result, for a fixed set
of stored records, in one order — so that `SKIP` and `TAKE` mean
something (§3.21).

**Use query-language semantics, not your storage engine's**, for every
comparison, ordering, grouping and equality test the language defines
(§3.20, §3.21).

**Enforce access before you compute**, per concrete identifier, failing
closed, and silently (§3.28).

**Bound everything a client can consume**: concurrent queries, streaming
queries, message size, query time, distinct-stream values, cross-type
lookback (§3.14, §3.15, §3.16, §3.26, §3.27).

**Behave identically across your configured ranges** (§3.29).

## A producer

**Send well-formed records** and accept that malformed ones vanish
without notice (§3.8, §3.12).

**Stay within the 262144-byte portable datagram ceiling**, batched or
not. Do not add discovery or depend on a collector's larger local
setting (§3.6).

**Choose a stable, conforming metric name.** It must match the identifier
grammar, name the producer distinguishably and use dots for hierarchy,
because publication and read rules are written against it and queries
select on it (§3.10).

**Convey metric identity.** Enable `KACS_SO_PASS_TOKEN` before sending
metrics and retain the sending socket so the captured-token and
authorization caches remain effective (§3.9).

**Timestamp at production**, not at submission (§3.7).

**Bound your label cardinality**, and keep histogram boundaries fixed
for the life of a metric (§3.10, §3.13).

**Never assume delivery.** No acknowledgement exists, none is coming,
and a record that mattered should have been an event (§3.4).

**Never change a metric's type.** Doing so ends the series silently and
permanently (§3.10).

## A client

**Tolerate unknown keys** in result records, and unknown statuses as
errors (§3.29).

**Discard partial results.** An error before `"end"` or `"watch"` means
every `"ok"` message for that query is void (§3.16).

**Assume nothing about completeness.** Results are silently filtered by
access, counts count only what you may see, and an absent field is
indistinguishable from a denied one (§3.28).

**Interpret provenance narrowly.** A log origin is broker-attested and a
metric name is publisher-authorized; neither proves the message, value
or labels are truthful (§3.28).

**Do not parse error strings** (§3.16).

**Open one connection per query** (§3.14).

## What this chapter does not require of a collector

A conforming collector need not accelerate anything, pre-compute
anything, shard anything, or retain anything for any particular period.
It need not honour `INDEX` beyond accepting it (§3.23). Its storage,
indexing, retention and query planning are entirely its own, and every
requirement above is stated about the answer rather than about how the
answer is reached.
