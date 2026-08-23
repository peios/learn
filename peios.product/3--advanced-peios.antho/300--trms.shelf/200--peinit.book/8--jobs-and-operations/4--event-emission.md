---
title: Event Emission
description: The structured event peinit emits at every job and operation transition, plus its own audit and graph records.
---

peinit emits a structured event at every job and operation lifecycle
transition, and for its own audit records. All of them go into the KMES
kernel ring buffer through `kmes_emit` and `kmes_emit_batch`, encoded as
msgpack per the KMES event-record format (Peios Kernel TRM §2).

**There is no event socket.** Structured events are not sent to eventd
over any connection. eventd consumes them from the ring buffer, which is
why they survive eventd being down, being restarted, or not existing
yet. The only thing peinit sends eventd over a socket is service output
(§11.4), which is a different path with different guarantees.

## Job events

**`job.created`** — the job object exists. Carries the job identifier,
service name, type, image path, identity and operation identifier.

**`job.started`** — exec succeeded. Carries the job identifier, PID and
cgroup path.

**`job.ended`** — the process exited or was killed. Carries the job
identifier, final state, exit code or signal, duration and failure
cause.

The event type is the dotted string; the fields form the msgpack
payload. The payloads are supersets of the summaries above — `job.ended`
in particular carries the whole record.

## Operation events

Every operation event carries: `operation_id`, `type`, `service`,
`source`, `caller` — null for a lifecycle-generated operation — and
`state` after the transition.

| Event | Adds |
|---|---|
| `operation.requested` | — |
| `operation.started` | — |
| `operation.completed` | `duration_ns`, `result` |
| `operation.failed` | `duration_ns`, `failure_reason` |
| `operation.cancelled` | `reason` |
| `operation.merged` | `merged_into` |
| `operation.aborted` | `duration_ns`, `reason` |

`duration_ns` is measured from **creation**, not from the start of
execution — the same reasoning as the operation timeout. What a caller
waited is what matters, and queue time is part of it.

The same field appears under three names across the two surfaces:
`failure_reason` on `operation.failed`, `reason` on
`operation.cancelled` and `operation.aborted`, and `error` in the
control interface's operation view (PSPU §4).

## Ordering

When one runtime step produces several lifecycle events, peinit emits
them in causal order before committing the retained state for that step.
For a terminal pre-start graph dispatch, the terminal event for the
operation whose outcome satisfied or failed the graph input precedes the
events for the operations that dispatch releases, which preserve graph
dispatch order.

Every operation in a graph context is requested when the context is
built rather than when its turn comes, so what a release emits is
`operation.started`.

## Audit and graph events

peinit's own audit records go through the same path: `access.denied` for
a refused control command, with the caller's SID, the target, the
requested right by name and the access bits requested and granted;
`on_failure.loop_suppressed` when the fallback chain guard trips;
`graph.validation_error` and `graph.validation_warning` for validation
findings; `notify.rejected` for an unauthenticated notification;
`fd_store.rejected` for a refused descriptor; `notify.status`,
`notify.errno` and `notify.exit_status` for the three event-emitting
notification fields; `cgroup.leaked` the first time a sub-cgroup is found
still populated after its post-kill deadline (§5.7); and
`graph.operation_terminal` for a graph member's terminal outcome.

Audit records are events rather than logs, and that distinction is the
point: the ring buffer persists from the moment PKM loads, so an access
denial during Phase 1 is captured before the registry exists, let alone
eventd.
