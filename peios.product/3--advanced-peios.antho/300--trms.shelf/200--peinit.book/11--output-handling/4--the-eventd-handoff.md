---
title: The eventd Handoff
description: Switching from buffering to forwarding when eventd reaches Active — the record format, lossy delivery, and what happens when eventd goes away.
---

When eventd reaches Active, peinit switches from buffering to
forwarding.

1. Start sending to eventd's log datagram socket, at the path from
   `Machine\System\eventd\LogSocketPath`.
2. Replay the pre-eventd buffer, oldest first, preserving each line's
   timestamp and metadata. The replay is best-effort: these are
   datagrams on a loss-tolerant socket, so some may be dropped, and
   peinit does not block waiting to deliver them.
3. Switch to real-time forwarding — new output sent as it arrives.
4. Clear the buffer.

From there peinit is a relay: read from the pipes, tag each line,
forward. Audit events continue to flow as KMES events, entirely
separately.

## The record

Each record is a msgpack map:

| Key | Type | Content |
|---|---|---|
| `origin` | string | The service name, or the hook identifier. |
| `is_error` | bool | True for stderr. |
| `message` | string | The line. |
| `timestamp` | uint | Nanoseconds, wall clock. |
| `job_id` | bin | The job's 16-byte GUID. Omitted when absent. |

The map has four or five entries depending on whether a job identifier
applies.

## Lossy delivery

eventd's log socket is a non-blocking Unix datagram socket. If eventd
cannot drain it fast enough its `SO_RCVBUF` fills and the kernel drops
further datagrams silently — log ingestion deliberately exerts no
backpressure on senders.

peinit therefore keeps no outbound write buffer. It sends each record as
a datagram and accepts that some may be dropped. It never blocks on a
send, and never lets pending records grow without bound.

Each send opens a datagram socket, sends, and closes it. Records go one
at a time; there is no batching of several records into one datagram.

A send that fails — the receive buffer full — takes peinit out of
forwarding for the remainder of that turn: the failing record and the
rest of its batch go back into the pre-eventd buffer. The end of the
turn re-establishes forwarding by replaying them.

## When eventd goes away

peinit supervises eventd like any other service, so it sees the exit
directly. It re-enables the pre-eventd buffer, and when eventd restarts
and reaches Active the handoff repeats.

There is a log gap between eventd crashing and restarting, bounded by
the buffer size. Events are unaffected: they land in the KMES ring
buffer regardless of eventd's state, and eventd resumes consuming from
the last persisted sequence when it comes back.
