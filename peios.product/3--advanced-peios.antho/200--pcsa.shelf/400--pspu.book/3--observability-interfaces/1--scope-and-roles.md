---
title: Scope and Roles
description: The three channels by which programs deposit logs and metrics with an observability service, and the roles at each end.
---

This chapter specifies the **observability interfaces**: the three
channels by which the programs on a Peios system deposit logs and
metrics with an observability service, and by which anything on the
system asks that service what it holds.

There are three interfaces and they are specified together because they
are one contract from the service's side and because two of the three
share their encoding, their validation posture and their loss model:

- the **Log Ingestion Interface**, on which a producer submits log
  records (§3.6 to §3.8)
- the **Metric Ingestion Interface**, on which a producer submits
  metric samples (§3.9 to §3.13)
- the **Query Interface**, on which a client asks for stored events,
  logs and metrics and receives records (§3.14 to §3.28)

Three roles participate.

The **collector** is the process that accepts ingestion on the two
datagram channels, serves the query channel, and holds the data in
between. There is one collector. It is the party being asked, on all
three interfaces — which is why the obligations in this chapter fall
mostly on it, and why the producer and client roles are so thin.

A **producer** is a process that submits metric samples. Its KACS token
is conveyed with every datagram, and the collector verifies that it may
publish each metric name (§3.9). Service output reaches the log channel
through the service manager instead: the service manager authenticates
the service origin by the pipe it owns, then acts as the sole log broker
(§3.6).

A **client** is a process that issues a query and reads the result. A
client's identity, unlike a producer's, is established by the collector
and determines what it may see (§3.28).

One program is commonly all three at once.

This chapter covers:

- the shape of the three channels and why two are datagram and one is
  a stream (§3.3)
- the loss model, which is the load-bearing decision of the whole
  ingestion design (§3.4)
- encoding, timestamps and the timestamp domain (§3.5)
- the log record, its fields, and exactly which malformations cost the
  record and which are merely ignored (§3.6 to §3.8)
- the metric data model, the three metric types, the sample record, and
  what makes two samples the same time series (§3.9 to §3.13)
- the query channel, its framing, and the four response messages
  (§3.14 to §3.17)
- the query language: its shape, its lexis, its operators, its ordering
  and grouping semantics, and the three modes (§3.18 to §3.25)
- cross-type filtering and streaming (§3.26, §3.27)
- what a client is and is not told about data it may not read (§3.28)
- how these interfaces may be extended (§3.29)
- the obligations binding on each role (§3.30)

This chapter does not cover:

- Event *emission*. Events reach a collector through KMES, not through
  any interface here; the consumer side of that is specified in PSPK,
  and emission is a kernel interface offered to privileged callers.
- Event type vocabulary and payload schemas, which belong to whichever
  subsystem emits the event.
- How a collector stores, indexes, retains or accelerates anything —
  its own design. The mainline collector's is described in the eventd
  TRMP.
- Which principals receive publication rights for individual metric
  names, and how those rights are administered.
- Administering a collector's contents.

The third of those is the point of the whole document. A collector is
handed records and asked questions; how it gets from one to the other is
exactly what different collectors exist to do differently.

## These interfaces are not a conformance requirement

A system that offers none of these is still Peios. Observability is not
in the definition of the platform, and a system that ships a different
collector, or none, conforms exactly as well.

They are specified because they are *public*. Every service has its
output brokered into logs, every collection agent is a metric producer,
and every dashboard, alerting tool and command-line viewer is a query
client. All three of those are third-party positions, and all three need
a contract that stays put.

> [!NOTE]
> The Query Interface reaches *events* as well as logs and metrics, even
> though events do not arrive over any interface here. That asymmetry is
> deliberate: PSPK's ring-buffer interface is the raw transport, requires
> SeSecurityPrivilege, and applies no per-record access control. The
> query interface is how everything else reads events, and it is the only
> way to read them after the ring buffer has moved on.
