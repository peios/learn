---
title: Job Events
description: The three events peinit emits across a job's lifecycle, their payloads, and the ordering guarantee between them.
---

peinit emits a structured event at every job and operation lifecycle
transition. All of them go into the KMES ring buffer, encoded as msgpack
per the envelope in §1.2.

**There is no event socket.** Structured events are not sent to eventd
over any connection. eventd consumes them from the ring buffer, which is
why they survive eventd being down, restarted, or not yet existing. The
only thing peinit sends eventd over a socket is service output, which is
a different path with different guarantees.

## The three job events

| Event | Fires when | Carries |
|---|---|---|
| `job.created` | The job object exists. | Job identifier, service name, type, image path, identity, operation identifier. |
| `job.started` | `exec` succeeded. | Job identifier, PID, cgroup path. |
| `job.ended` | The process exited or was killed. | Job identifier, final state, exit code or signal, duration, failure cause. |

The event type is the dotted string; the fields form the msgpack
payload. The payloads are supersets of the summaries above — `job.ended`
in particular carries the whole record.

## Ordering

When one runtime step produces several lifecycle events, peinit emits
them in causal order **before** committing the retained state for that
step. A consumer sees the events in an order consistent with what
happened, not in whatever order the writes completed.
