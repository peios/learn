---
title: The Write Path
description: There is no per-record access control on the way in — what stands in its place, and what that leaves open for an operator.
---

There is no per-record access control on the way in. This article
records what stands in its place and what that leaves open.

## Events

Emission is KMES's business. `kmes_emit` and `kmes_emit_batch` require
SeAuditPrivilege, and eventd is not in the path — it consumes what KMES
delivers and applies no admission control of its own (§2.2).

The identity stamps on an event are the kernel's, captured from kernel
state at the moment of the write, and an emitting process cannot set,
influence or suppress them. That is what makes an event's `process_guid`
evidence in a way that a log's `origin` is not.

## Logs and metrics

The Security Descriptor on each ingestion socket is the entirety of the
write-path control (PSPU §3.3). There is nothing per record: no token is
obtained, no identity is checked, and no field is verified.

The socket descriptor is therefore doing all the work, and it is worth
being precise about what it does and does not do on Peios. An access
decision is routed through the object's Security Descriptor, not through
POSIX mode bits, so setting a mode on a socket pathname restricts
nothing — and an inode created without a descriptor is denied to every
caller, so binding a socket into a directory carrying no inheritable
ACEs produces a socket that nothing, including the service manager, can
reach. eventd establishes the descriptor on each socket before it begins
receiving on it.

## Origin and name are claims

`origin` in a log record and `name` in a metric record are self-reported
(PSPU §3.7, §3.10). Any process that can reach an ingestion socket can
write under any origin or metric name it likes, including one belonging
to another program.

The consequences are the obvious ones. A compromised service can inject
log lines attributed to another service, manufacturing a plausible
operational narrative. It can bury a real incident under noise
attributed elsewhere. It can create metric series under a name a
dashboard trusts.

Read-path descriptors limit who can *see* data written under a given
identifier; they do nothing about who wrote it. eventd never presents a
stored `origin` or metric `name` as evidence of provenance.

> [!NOTE]
> Closing this needs a primitive eventd does not have: a way to obtain
> the peer's token for a **datagram**, as `kacs_open_peer_token` does for
> a stream connection. With one, an ingestion socket could carry a
> descriptor governing which origins a sender may write, checked per
> datagram — which is the shape the read path already has. Until it
> exists, confining which processes can reach the socket at all is the
> only available control, and it is coarse: it is a decision about
> processes, where the thing worth controlling is names.

## What this means for an operator

The interim posture is that the ingestion sockets are a trust boundary
that only separates "can reach eventd" from "cannot" — and on a system
where every service logs, nearly everything is on the inside.

Two things follow. Data whose provenance must be trustworthy belongs in
an event, where the kernel stamps the identity, rather than in a log
where the producer asserts it. And read-path descriptors on the origins
and metric names that matter are worth writing even so: they prevent an
unauthorized reader from *querying* data written under a spoofed
identifier, which is a smaller property than authenticity but not
nothing.
