---
title: The event stream
description: The verdict ring behind /dev/peios-pnp — what each evaluation records, how a reader drains it, the status and counters ioctls, and the engine's confessions.
---

Every real evaluation — a published forest judged the traversal, or a
fail-closed drop — appends one `struct peios_pnp_event` to a bounded
ring. Permissive traversals emit nothing: there is no decision to
attribute, and the status tells that story instead. A packet answered by
its flow's cached sentence emits nothing either: there was no
evaluation, and `flow_cached` counts it. The layouts are in §6.A; this
page is what they mean.

## One event

An event is the decision and enough of the snapshot to find the packet
it was about: sequence number, `CLOCK_REALTIME` nanoseconds, the seat
and layer, the verdict and — when it was a reject — its kind, flags
(`BACKSTOP`, `FAIL_CLOSED`, `REJECT_DEGRADED`, `REJUDGED` for a Flow
evaluation that replaced a stale sentence), direction, address family,
protocol, flow state, interface index, ports, ethertype, both addresses,
the stack-view length, the effect counts the evaluation yielded packed
eight bits each (tags, counts, reports, prompts, saturating), and the
attributing rule's path — the winning rule, or `backstop`, or
`fail-closed` — truncated to 96 bytes.

The path is relative to the layer key: `no-inbound/ssh`, not
`Machine\System\Network\Rules\Packet\no-inbound\ssh`.

## The ring and its reader

The ring holds 4096 events under a spinlock (`irqsave`: emission happens
in softirq). A full ring overwrites the **oldest** event and counts the
loss in `events_dropped` — the honesty rule: a slow reader loses data
and is told so, in the status and by the gap in sequence numbers.

`/dev/peios-pnp` is a misc device, mode 0600, with a single-reader gate
(`open()` returns `-EBUSY` to a second opener). `read()` returns whole
records only, up to 64 per call, and blocks on an empty ring unless
`O_NONBLOCK`; `poll()` raises `POLLIN` when events wait. A reader that
reconnects resumes from whatever the ring still holds, and catches the
gap from the sequence numbers.

The viewer daemon reads it with a small wrinkle worth knowing about: its
own HTTP responses to a viewer are judged traffic too, so every event it
sends produces another event — a feedback loop. pnpd hides events about
its own TCP port from what it serves and counts them (`own_verdicts_hidden`),
which is the same treatment the wire tap gives its own frames.

## Status

`PEIOS_PNP_IOC_STATUS` fills `struct peios_pnp_status`: the ABI version
(check it before trusting the rest — the ABI is experimental and
versioned, currently 3), the generation, whether any layer is enforcing,
the ring's confessed drops, and the engine counters. The counters are
plain 64-bit atomics rather than per-CPU — legibility over throughput
while the engine is young, to be revisited with a compiled evaluator.

| Group | Counters |
|---|---|
| Seats | `seen_ingress`, `seen_egress`, `seen_local_in`, `seen_local_out`, `deferred` (ingress traversals left for the IP seat), `fallback_judged` (ingress traversals the Packet layer judged there) |
| Evaluation | `judged`, `permissive`, `parse_errors`, `fail_closed` |
| Verdicts | `verdict_pass`, `verdict_drop`, `verdict_reject`, `reject_degraded` |
| Effects yielded | `fx_tags`, `fx_counts`, `fx_reports`, `fx_prompts` |
| Ingestion | `last_ingest_error`, `last_ingest_t_ns`, `reporting_level` |
| The stores | `tag_writes`, `tag_untracked`, `tag_refused`, `count_writes`, `count_key_absent`, `count_refused`, `reports_emitted`, `counter_cells` |
| The Flow layer | `flow_judged` (evaluations, sentences written), `flow_cached` (packets answered by a current sentence), `flow_rejudged` (stale by generation), `flow_expired` (stale by time edge), `flow_uncached` (flows with no extension to hold a sentence, evaluated per packet) |
| Refusals | `refusals_emitted` (answers built and sent), `refusals_bypassed` (own refusals waved through a seat), `teardowns_emitted` (far-end resets for refused established TCP flows) |

Two invariants a reader can check: `judged` equals the number of
evaluations against a live forest at any layer (Flow evaluations
included, so `judged − flow_judged` is the per-packet count), and
`permissive` counts layer evaluations that found no forest — at
generation 0, every one.

`PEIOS_PNP_IOC_COUNTERS` is the counter dump described in §6.6: the
caller supplies a buffer of `struct peios_pnp_counter_rec`, the kernel
fills as many as fit and reports both how many it wrote and how many
cells exist, so a short buffer is visible. `PEIOS_PNP_IOC_FLOWS` is the
flows dump described in §6.8, with the same short-buffer contract over
`struct peios_pnp_flow_rec`.

## Confessions, collected

Everything PNP declines to do is counted somewhere in the status, and
the viewer shows every one of them. A reader should never have to infer
a refusal from a missing effect:

- a `REJECT` it could not send → `reject_degraded`, and the event's flag;
- an evaluation it could not finish → `fail_closed`, and an event;
- a frame it could not describe → `parse_errors`;
- a tag it could not write → `tag_untracked` or `tag_refused`;
- a count it could not land → `count_key_absent` or `count_refused`;
- a sentence it could not keep → `flow_uncached`;
- a packet it did not judge because a sentence answered → `flow_cached`;
- a refusal it did not judge because it was its own → `refusals_bypassed`;
- a generation it could not accept → `last_ingest_error`, and the log;
- an event it could not keep → `events_dropped`.
