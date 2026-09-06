---
title: The eventd Handoff
description: Switching from buffering to forwarding when eventd reaches Active — the record format, lossy delivery, and what happens when eventd goes away.
---

When eventd reaches Active, peinit switches from buffering to
forwarding. [*eventd.forwarding-begins-when-eventd-reaches-active]

1. Start sending to eventd's log datagram socket, at the path from
   `Machine\System\eventd\LogSocketPath`.
   [*eventd.the-socket-path-comes-from-the-registry]
2. Replay the pre-eventd buffer, oldest first, preserving each line's
   timestamp and metadata. [*eventd.the-buffer-is-replayed-oldest-first]
   The replay is best-effort: these are
   datagrams on a loss-tolerant socket, so some may be dropped, and
   peinit does not block waiting to deliver them.
3. Switch to real-time forwarding — new output sent as it arrives.
   [*eventd.new-output-is-forwarded-as-it-arrives]
4. Clear the buffer.

From there peinit is a relay: read from the pipes, tag each line,
forward. Audit events continue to flow as KMES events, entirely
separately.

## Broker authentication [*eventd.the-log-socket-denies-the-service-group-before-allowing-system]

eventd's log socket denies `FILE_WRITE_DATA` to the Service logon group
before allowing SYSTEM. peinit's bootstrap token is SYSTEM without that
group; every phase-2 service token carries it, including a token whose
user is SYSTEM. peinit is therefore the only service-output broker.
[*eventd.peinit-is-the-only-service-output-broker]

peinit does not attach a KACS token per log datagram. The socket
descriptor authenticates the broker once at send admission, and peinit
derives each `origin` from the pipe it is draining. Avoiding ancillary
token fds also preserves mixed-origin batching and the hot-path reuse
described below.

## Datagram framing and the record [*eventd.a-datagram-holds-a-msgpack-array-of-records]

peinit sends a msgpack array of one or more records in each datagram.
It takes the largest ordered prefix that fits
the PSPU portable ceiling of 262144 encoded bytes.
[*eventd.a-batch-is-the-largest-prefix-fitting-the-portable-ceiling] It
deliberately does
not read eventd's larger local ceiling: fixing the producer boundary
avoids registry work and means an eventd configuration change cannot
invalidate peinit's batches. A successful datagram advances the replay
buffer by the whole array, while a failed datagram advances it by
nothing. [*eventd.a-failed-datagram-advances-the-replay-by-nothing]

Each record is a msgpack map [*eventd.the-record-fields]:

| Key | Type | Content |
|---|---|---|
| `origin` | string | The service name, or the hook identifier. |
| `is_error` | bool | True for stderr. |
| `message` | string | The line. |
| `timestamp` | uint | Nanoseconds, wall clock. |
| `job_id` | bin | The job's 16-byte GUID. Omitted when absent. |

The map has four or five entries depending on whether a job identifier
applies. [*eventd.the-job-id-is-omitted-when-there-is-none]

## Lossy delivery [*eventd.the-log-socket-is-a-non-blocking-datagram-socket]

eventd's log socket is a non-blocking Unix datagram socket. If eventd
cannot drain it fast enough its `SO_RCVBUF` fills and the kernel drops
further datagrams silently — log ingestion deliberately exerts no
backpressure on senders.

peinit therefore keeps no unbounded outbound write buffer. It sends
bounded arrays of records and accepts that some datagrams may be
dropped. It never blocks on a send, and never lets pending records grow
without bound. [*eventd.peinit-never-blocks-on-a-send]

peinit creates one non-blocking datagram socket when forwarding begins,
connects it to eventd, and reuses both that socket and its encoding
allocation. It does not create a socket or allocate a fresh output
buffer per record. [*eventd.one-socket-is-created-and-reused] When
eventd becomes inactive, the connection is
discarded so the next Active transition connects to the newly bound
socket. [*eventd.the-connection-is-discarded-when-eventd-goes-inactive]

A **drop** and a **transport failure** are handled differently, and the
difference is what keeps the lossy design working.

A drop is `EAGAIN`, `EWOULDBLOCK` or `ENOBUFS` — the receive buffer is
full and the datagram did not fit. That is the designed outcome under
load, so the connection stands and forwarding continues.
[*eventd.a-drop-leaves-the-connection-standing] Live records in
the dropped datagram are gone; peinit counts them and sends the next
batch. Replaying the pre-eventd buffer is the one case where waiting
beats dropping — those records are already held and the buffer is
bounded, so the flush stops and the next turn tries again.
[*eventd.a-drop-during-replay-waits-rather-than-loses]

A transport failure is anything else: the socket path gone, the peer
refusing. peinit clears the connection, keeps the unsent records in the
pre-eventd buffer in order, and the end of the turn re-establishes
forwarding by replaying them.
[*eventd.a-transport-failure-rebuffers-and-replays]

Treating a drop as a transport failure made peinit oscillate between
forwarding and buffering under exactly the load the lossy socket exists
to absorb, and replay records eventd may already have held — so the
busier eventd got, the more work peinit made for it.

## When eventd goes away [*eventd.an-eventd-exit-re-enables-the-buffer]

peinit supervises eventd like any other service, so it sees the exit
directly. It re-enables the pre-eventd buffer, and when eventd restarts
and reaches Active the handoff repeats.
[*eventd.the-handoff-repeats-when-eventd-comes-back]

There is a log gap between eventd crashing and restarting, bounded by
the buffer size. [*eventd.the-gap-is-bounded-by-the-buffer-size] Events
are unaffected: they land in the KMES ring
buffer regardless of eventd's state, and eventd resumes consuming from
the last persisted sequence when it comes back.
