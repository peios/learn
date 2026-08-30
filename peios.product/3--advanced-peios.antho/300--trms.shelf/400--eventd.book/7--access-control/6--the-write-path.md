---
title: The Write Path
description: Broker-attested log origins and KACS-authorized metric names, including the cache that keeps AccessCheck off the steady-state hot path.
---

The three write paths establish provenance differently because their
inputs come from different places.

## Events

Emission is KMES's business. `kmes_emit` and `kmes_emit_batch` require
SeAuditPrivilege, and eventd is not in the admission path — it consumes
what KMES delivers (§2.2).

The identity stamps on an event are the kernel's, captured from kernel
state at the write. An emitting process cannot set, influence or
suppress them. That is what makes an event's `process_guid` evidence.

## Logs use peinit as a broker

Service processes do not reach the log socket. eventd replaces the
inherited descriptor on `LogSocketPath` with this protected DACL before
its first receive:

```text
O:SYG:SYD:P(D;;0x2;;;SU)(A;;GA;;;SY)
```

`SU` is the Service logon group, S-1-5-6. Every phase-2 service token,
including a SYSTEM service token, carries it. peinit's bootstrap SYSTEM
token does not. The deny is evaluated before the SYSTEM allow, so a
service cannot write merely because its user SID is SYSTEM; peinit can.

peinit determines `origin` from the output pipe it is draining and may
batch records from several origins in one datagram. eventd therefore
does not request or check a KACS token for each log datagram. The socket
admission attests the broker and the broker attests the origin, without
token-fd churn or an AccessCheck on the log hot path.

A log origin proves which service context peinit associated with the
line. It does not prove that the line's message is truthful.

## Metrics carry the producer token

A metric producer enables `KACS_SO_PASS_TOKEN` once on its persistent
sending socket. KACS attaches the producer's effective identity to each
datagram as `KACS_SCM_TOKEN`. eventd uses `recvmsg` with room for exactly
one token and no ordinary file descriptors.

eventd discards the whole datagram before MessagePack parsing when:

- no token arrived
- the data was truncated
- the ancillary data was truncated
- querying the token or resolving policy failed

For a valid datagram, eventd resolves each record's metric name through
the ordinary hierarchical Metrics descriptor namespace (§7.2) and runs
AccessCheck against the conveyed token for `EVENTD_PUBLISH`. A denied
record is discarded; authorized sibling records in the same datagram
continue.

The wildcard Metrics descriptor grants `EVENTD_PUBLISH` to SYSTEM and
Administrators, not Authenticated Users. A package that owns a metric
prefix installs a more-specific descriptor granting its service SID
that right. Existing wildcard descriptors that exactly match eventd's
old read-only default are upgraded in place; administrator-modified
descriptors are never rewritten.

Authorization covers the metric name, not its labels or value. An
authorized producer can create arbitrarily many valid label sets under
that name (§5.3).

## The publication cache

A full AccessCheck is not performed per sample or per datagram. The
metric ingestion thread owns a bounded verdict cache keyed by:

```text
(token_id, modified_id, concrete metric name)
```

KACS reuses the captured token object while a persistent sender socket
keeps the same effective identity, so ordinary traffic repeatedly hits
the same entry. A hit performs no allocation and no AccessCheck.

`MetricAuthorizationCacheSize` bounds the total entry count. When full,
eventd clears the cache rather than maintaining an LRU list on the write
path. This makes churn expensive for the producer causing it without
adding pointer updates to every successful lookup.

The descriptor cache carries a generation. Any security-registry change
advances it and clears all local publication verdicts before they are
reused. The cache stores denials as well as grants, so repeatedly sending
an unauthorized name does not repeatedly invoke KACS.

## Rejected input

Missing identity, truncation, denied records and policy errors increment
in-memory diagnostic counters. Policy errors may produce rate-limited
standard-error text. None produces a durable event or log record: doing
work proportional to hostile input would create an amplification path
(PSPU §3.4).
