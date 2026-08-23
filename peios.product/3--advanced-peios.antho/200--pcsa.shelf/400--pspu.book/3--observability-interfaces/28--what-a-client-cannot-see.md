---
title: What a Client Cannot See
description: Read access is enforced on every query against the token captured at connect — the unit of access, and why filtering is silent.
---

A collector MUST enforce read access on every query, against the token
captured when the client connected (§3.14).

How it does so is its own design, and the mechanism the mainline
collector uses is described in the eventd TRMP. What this chapter fixes
is the part a client can observe: **which results it gets, and what it
is told about the ones it does not.**

## The unit of access is the concrete identifier

Access is resolved per **concrete identifier** — the event type, log
origin or metric name a stored record actually carries (§3.2) — and not
per query, per store, or per pattern the query happened to write.

A collector MUST resolve each identifier that a query's data could touch
independently. A broad selector authorizes nothing by itself: `EVENTS`
with no pattern, `EVENTS kacs.*`, `LOGS` with no `FROM`, and
`METRIC cpu.*` are all resolved identifier by identifier, and a client
permitted to read one matching identifier and not another sees only the
first.

Identifiers are matched to rules by dot-delimited prefix, most specific
first, falling back to a wildcard default: for `kacs.access_denied`, a
rule for `kacs.access_denied`, then one for `kacs`, then the default.

A collector MUST fail closed. If no rule resolves — including because
the default is missing — access is denied.

## Filtering is silent

**Records and fields removed by access control are removed without
comment.** A collector MUST NOT indicate in a response that anything was
withheld, and a client MUST NOT assume a result set is complete.

The consequences are precise and a client needs all of them:

- A record whose identifier the client may not read is **absent**, not
  redacted.
- A field the client may not read is **absent from the record**, and is
  indistinguishable from a field the record never carried (§3.17).
- `COUNT`, `COUNT BY`, `TOP N BY`, `DISTINCT` and every aggregation
  reflect **only** authorized records. A count is a count of what the
  client may see.
- A cross-type condition referencing data the client may not read
  evaluates as though **no matching data exists** (§3.26). It does not
  fail the query.
- `TAKE` and `SKIP` page over the authorized records only.

## Access control runs before everything

A collector MUST remove unauthorized records from the logical row set
**before** predicates, transforms, grouping, aggregation, sorting,
pagination and projection (§3.18).

This is not tidiness. Counting, ordering or paginating over records a
client may not read leaks them through the count, through the ordering,
and through the gaps in pagination — a client could establish how many
records of a type it cannot read exist, and roughly when, without ever
seeing one.

A collector MAY reach the result however it likes: pushing the
authorization down into its storage engine, or reading candidates and
discarding them before aggregating. What it MUST NOT do is produce a
different answer from the one filtering-first produces.

## Denied fields do not fail the query

When a query references a field in a predicate, a grouping, a sort or an
aggregation, and some matching identifier does not grant that field, the
records under that identifier contribute nothing — exactly as if their
identifier had been denied outright.

A collector MUST NOT reject the query.

> [!NOTE]
> Rejecting would be the more informative behaviour and that is precisely
> the objection to it. A rejection tells the client that an identifier
> exists, matches its query, and carries a field it may not read — three
> facts about data it was not permitted to see, delivered by the
> mechanism meant to withhold them. A client could enumerate restricted
> event types by watching which queries are refused. Silence costs the
> client a result that is narrower than it looks; rejection costs the
> system the property the whole model rests on.

Authorization for a field is resolved from the field **as written**,
against each concrete identifier, and does not depend on whether any
record of that identifier actually carries it. Payload fields vary
between records of the same type, so a rule that turned on presence
would be undecidable before the scan it was meant to authorize.

## What is not a field

Derived aggregate outputs — `count`, `sum`, `avg`, `min`, `max` — are
**not** source fields, have no access identity of their own, and are
visible whenever the client is authorized for the records and the source
fields they were computed from.

Values internal to preserving query semantics — row identifiers, series
identifiers, ordering tiebreakers, series type checks — are likewise not
query-language fields (§3.21). A metric result's `value` **is** a source
field, because it is a raw sample or a scalar derived from raw samples.

## Errors say nothing

A collector MUST NOT include a value the client is not authorized to
read in any error message (§3.16), including in errors raised by
internal consistency checks.

## Streaming

Access decisions made for the initial result set are reused during the
watch phase, but a collector MUST resolve any **new** concrete
identifier that appears in a streamed batch and check it before using
the record or its distinct value — a new event type or a new log origin
appearing mid-stream has never been authorized.

If a rule changes during a streaming query, a collector MUST re-check
subsequent batches against the new rule.

The **token** does not change. It was captured at connection (§3.14), so
a client whose group memberships change mid-stream continues to be
evaluated against what it connected with, and a client whose access is
revoked keeps receiving records until it disconnects.

## The write path is not access-controlled

Nothing on either ingestion channel is authorized per record (§3.4).
Access control here is a read-path mechanism only, and the Security
Descriptor on each ingestion socket is the whole of the write-path
control (§3.3).

The consequence is that **`origin` and metric `name` are self-asserted**
(§3.7, §3.10). Any process that can reach an ingestion socket may write
under any origin or metric name it likes, including one belonging to
another program — which permits fabricating a plausible operational
record, or burying a real one under noise attributed elsewhere.

Read-path rules limit who can *see* data written under a given
identifier; they do nothing about who wrote it. A collector MUST NOT
present a stored `origin` or metric `name` as evidence of provenance,
and a client MUST NOT treat one as authenticated.

> [!NOTE]
> Closing this needs something the interface cannot supply on its own: a
> way to obtain the peer's token for a datagram, as a collector obtains
> one for a stream connection (§3.14). Until that exists, a producer's
> claim about itself is unverifiable, and confining the set of processes
> that can reach the socket at all is the only available control.
