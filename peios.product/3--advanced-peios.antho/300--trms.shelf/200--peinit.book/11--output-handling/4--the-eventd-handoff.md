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

## Broker authentication

eventd's log socket denies `FILE_WRITE_DATA` to the Service logon group
before allowing SYSTEM. peinit's bootstrap token is SYSTEM without that
group; every phase-2 service token carries it, including a token whose
user is SYSTEM. peinit is therefore the only service-output broker.

peinit does not attach a KACS token per log datagram. The socket
descriptor authenticates the broker once at send admission, and peinit
derives each `origin` from the pipe it is draining. Avoiding ancillary
token fds also preserves mixed-origin batching and the hot-path reuse
described below.

## Datagram framing and the record

peinit sends a msgpack array of one or more records in each datagram.
It takes the largest ordered prefix that fits
the PSPU portable ceiling of 262144 encoded bytes. It deliberately does
not read eventd's larger local ceiling: fixing the producer boundary
avoids registry work and means an eventd configuration change cannot
invalidate peinit's batches. A successful datagram advances the replay
buffer by the whole array, while a failed datagram advances it by
nothing.

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

peinit therefore keeps no unbounded outbound write buffer. It sends
bounded arrays of records and accepts that some datagrams may be
dropped. It never blocks on a send, and never lets pending records grow
without bound.

peinit creates one non-blocking datagram socket when forwarding begins,
connects it to eventd, and reuses both that socket and its encoding
allocation. It does not create a socket or allocate a fresh output
buffer per record. When eventd becomes inactive, the connection is
discarded so the next Active transition connects to the newly bound
socket.

A **drop** and a **transport failure** are handled differently, and the
difference is what keeps the lossy design working.

A drop is `EAGAIN`, `EWOULDBLOCK` or `ENOBUFS` — the receive buffer is
full and the datagram did not fit. That is the designed outcome under
load, so the connection stands and forwarding continues. Live records in
the dropped datagram are gone; peinit counts them and sends the next
batch. Replaying the pre-eventd buffer is the one case where waiting
beats dropping — those records are already held and the buffer is
bounded, so the flush stops and the next turn tries again.

A transport failure is anything else: the socket path gone, the peer
refusing. peinit clears the connection, keeps the unsent records in the
pre-eventd buffer in order, and the end of the turn re-establishes
forwarding by replaying them.

Treating a drop as a transport failure made peinit oscillate between
forwarding and buffering under exactly the load the lossy socket exists
to absorb, and replay records eventd may already have held — so the
busier eventd got, the more work peinit made for it.

## When eventd goes away

peinit supervises eventd like any other service, so it sees the exit
directly. It re-enables the pre-eventd buffer, and when eventd restarts
and reaches Active the handoff repeats.

There is a log gap between eventd crashing and restarting, bounded by
the buffer size. Events are unaffected: they land in the KMES ring
buffer regardless of eventd's state, and eventd resumes consuming from
the last persisted sequence when it comes back.
