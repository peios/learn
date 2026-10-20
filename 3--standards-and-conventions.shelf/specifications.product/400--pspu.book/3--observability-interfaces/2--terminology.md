---
title: Terminology
description: Terms this chapter borrows unchanged from PSPK's KMES event stream and from elsewhere in the corpus.
---

Terms defined in PSPK for the KMES event stream — event, header,
payload, stamp, sequence number, origin class — are used here with the
same meaning and are not redefined. Terms defined in PCDS — GUID, SID,
Security Descriptor, ACL, ACE — likewise.

The following terms are specific to this chapter.

**Collector**: the process that accepts log and metric ingestion and
serves queries. The role, not the program: the mainline collector is
eventd, and this chapter never requires that it be.

**Producer**: a process that submits log records or metric samples.

**Client**: a process that issues a query.

**Log record**: one line of output from a program, with the light
metadata of §3.7 attached. A log record is text; the collector does not
parse it.

**Metric sample**: one measurement of one quantity at one moment,
belonging to a time series (§3.13).

**Time series**: the sequence of samples sharing a name, a label set,
and — for histograms — a set of bucket boundaries. Identity is defined
in §3.13.

**Boot ID**: a GUID identifying one boot of the system. Every record a
collector stores carries one, so that records from different boots are
never interleaved and per-CPU event sequence numbers, which restart each
boot, remain unambiguous. It is assigned outside this interface and is
visible to a client only as a queryable field.

**Datagram**: one message on an ingestion channel, carrying either one
record or a batch of them (§3.7, §3.11).

**Effective query range**: the half-open interval a query examines,
`[SINCE, UNTIL)`, with the bounds resolved as §3.19 defines.

**Concrete identifier**: the event type, log origin or metric name that
a stored record actually carries — as distinct from the pattern a query
or a Security Descriptor uses to match one. Access control resolves
per concrete identifier (§3.28).
