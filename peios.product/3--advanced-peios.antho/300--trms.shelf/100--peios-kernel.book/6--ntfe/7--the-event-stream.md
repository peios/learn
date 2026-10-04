---
title: The event stream
description: The verdict ring behind /dev/peios-ntfe — what each evaluation records, how a reader drains it, the status and counters ioctls, and the engine's confessions.
---

Every real evaluation — a published forest judged the traversal, or a
fail-closed drop — appends one `struct peios_ntfe_event` to a bounded
ring. [*ntfe-stream.each-evaluation-appends-one-event] Permissive traversals emit nothing: there is no decision to
attribute, and the status tells that story instead. [*ntfe-stream.permissive-emits-no-event] A packet answered by
its flow's cached sentence emits nothing either: there was no
evaluation, and `flow_cached` counts it. [*ntfe-stream.cached-sentence-emits-no-event] The layouts are in §6.A; this
page is what they mean.

## One event

An event is the decision and enough of the snapshot to find the packet
it was about: sequence number, `CLOCK_REALTIME` nanoseconds, the seat
and layer, the verdict and — when it was a reject — its kind, flags
(`BACKSTOP`, `FAIL_CLOSED`, `REJECT_DEGRADED`, `REJUDGED` for a Flow
evaluation that replaced a stale sentence, `IDENTITY_UNRESOLVED` for
one whose endpoint could not be attributed), [*ntfe-stream.event-flags] direction, address family,
protocol, flow state, interface index, ports, ethertype, both addresses,
the stack-view length, the effect counts the evaluation yielded packed
eight bits each (tags, counts, reports, prompts, saturating), [*ntfe-stream.event-effect-counts-packed-saturating] and the
attributing rule's path — the winning rule, or `backstop`, or
`fail-closed` — truncated to 96 bytes. [*ntfe-stream.event-attributed-path-truncated-96] A `Flow` event also carries both
endpoints' identities as the judgment read them (§6.9): the kind, the
process GUID, pid and comm, the user SID and the service SID — binary
SIDs, so the viewer, not the kernel, turns them into names. [*ntfe-stream.flow-event-carries-endpoint-identities]

The path is relative to the layer key: `no-inbound/ssh`, not
`Machine\System\Network\Rules\Packet\no-inbound\ssh`. [*ntfe-stream.path-relative-to-layer-key]

## The ring and its reader

The ring holds 4096 events under a spinlock (`irqsave`: emission happens
in softirq). [*ntfe-stream.ring-4096-events-irqsave-lock] A full ring overwrites the **oldest** event and counts the
loss in `events_dropped` — the honesty rule: a slow reader loses data
and is told so, in the status and by the gap in sequence numbers. [*ntfe-stream.full-ring-overwrites-oldest]

`/dev/peios-ntfe` is a misc device, mode 0600. [*ntfe-stream.device-misc-mode-0600] Any number of files may
be open on it, because the status and dump ioctls are asked by tools
while a viewer holds the stream, [*ntfe-stream.device-many-openers] but the ring has one drain: the first
file to `read()` claims it until it closes, and another file's `read()`
returns `-EBUSY` meanwhile. [*ntfe-stream.first-reader-claims-ring-others-ebusy] `read()` returns whole
records only, up to 64 per call, [*ntfe-stream.read-whole-records-up-to-64] and blocks on an empty ring unless
`O_NONBLOCK`; [*ntfe-stream.read-blocks-unless-nonblock] `poll()` raises `POLLIN` when events wait. [*ntfe-stream.poll-pollin-when-events-wait] A reader that
reconnects resumes from whatever the ring still holds, and catches the
gap from the sequence numbers. [*ntfe-stream.reconnect-resumes-from-ring]

The viewer daemon reads it with a small wrinkle worth knowing about: its
own HTTP responses to a viewer are judged traffic too, so every event it
sends produces another event — a feedback loop. pnpd hides events about
its own TCP port from what it serves and counts them (`own_verdicts_hidden`),
which is the same treatment the wire tap gives its own frames. [*ntfe-stream.viewer-hides-own-port-events]

## Status

`PEIOS_NTFE_IOC_STATUS` fills `struct peios_ntfe_status`: the ABI version
(check it before trusting the rest — the ABI is experimental and
versioned, currently 5), [*ntfe-stream.status-abi-version-5] the generation, whether any layer is enforcing,
the ring's confessed drops, and the engine counters. [*ntfe-stream.status-ioctl-contents] The counters are
plain 64-bit atomics rather than per-CPU — legibility over throughput
while the engine is young, to be revisited with a compiled evaluator. [*ntfe-stream.counters-plain-64bit-atomics]

| Group | Counters |
|---|---|
| Seats | `seen_ingress`, `seen_egress`, `seen_local_in`, `seen_local_out`, `deferred` (ingress traversals left for the IP seat), `fallback_judged` (ingress traversals the Packet layer judged there) [*ntfe-stream.counters-seats] |
| Evaluation | `judged`, `permissive`, `parse_errors`, `fail_closed` [*ntfe-stream.counters-evaluation] |
| Verdicts | `verdict_pass`, `verdict_drop`, `verdict_reject`, `reject_degraded` [*ntfe-stream.counters-verdicts] |
| Effects yielded | `fx_tags`, `fx_counts`, `fx_reports`, `fx_prompts` [*ntfe-stream.counters-effects-yielded] |
| Ingestion | `last_ingest_error`, `last_ingest_t_ns`, `reporting_level`, `changes_noted` and `changes_walked` (§6.5, in force), `contexts` (interfaces in the network context table) [*ntfe-stream.counters-ingestion] |
| The stores | `tag_writes`, `tag_untracked`, `tag_refused`, `count_writes`, `count_key_absent`, `count_refused`, `reports_emitted`, `counter_cells` [*ntfe-stream.counters-stores] |
| The Flow layer | `flow_judged` (evaluations, sentences written), `flow_cached` (packets answered by a current sentence), `flow_rejudged` (stale by generation), `flow_expired` (stale by time edge), `flow_uncached` (flows with no extension to hold a sentence, evaluated per packet) [*ntfe-stream.counters-flow-layer] |
| Refusals | `refusals_emitted` (answers built and sent), `refusals_bypassed` (own refusals waved through a seat), `teardowns_emitted` (far-end resets for refused established TCP flows) [*ntfe-stream.counters-refusals] |
| The identity facts | `identity_unresolved` (endpoints that could not be attributed at resolution: a socket with no KACS state, an inet socket nobody stamped, a loopback sender the inbound seat could not see) [*ntfe-stream.counters-identity] |

Two invariants a reader can check: `judged` equals the number of
evaluations against a live forest at any layer (Flow evaluations
included, so `judged − flow_judged` is the per-packet count), [*ntfe-stream.judged-counts-live-forest-evaluations] and
`permissive` counts layer evaluations that found no forest — at
generation 0, every one. [*ntfe-stream.permissive-counts-forestless-evaluations]

`PEIOS_NTFE_IOC_COUNTERS` is the counter dump described in §6.6: the
caller supplies a buffer of `struct peios_ntfe_counter_rec`, the kernel
fills as many as fit and reports both how many it wrote and how many
cells exist, so a short buffer is visible. [*ntfe-stream.counters-ioctl-short-buffer-visible] `PEIOS_NTFE_IOC_FLOWS` is the
flows dump described in §6.8, with the same short-buffer contract over
`struct peios_ntfe_flow_rec`. [*ntfe-stream.flows-ioctl-short-buffer-visible]

## Confessions, collected

Everything NTFE declines to do is counted somewhere in the status, and
the viewer shows every one of them. [*ntfe-stream.every-refusal-counted] A reader should never have to infer
a refusal from a missing effect:

- a `REJECT` it could not send → `reject_degraded`, and the event's flag; [*ntfe-stream.confess-reject-degraded]
- an evaluation it could not finish → `fail_closed`, and an event; [*ntfe-stream.confess-fail-closed]
- a frame it could not describe → `parse_errors`; [*ntfe-stream.confess-parse-errors]
- a tag it could not write → `tag_untracked` or `tag_refused`; [*ntfe-stream.confess-tag-not-written]
- a count it could not land → `count_key_absent` or `count_refused`; [*ntfe-stream.confess-count-not-landed]
- a sentence it could not keep → `flow_uncached`; [*ntfe-stream.confess-flow-uncached]
- an endpoint it could not attribute → `identity_unresolved`, and the
  event's flag; [*ntfe-stream.confess-identity-unresolved]
- a packet it did not judge because a sentence answered → `flow_cached`; [*ntfe-stream.confess-flow-cached]
- a refusal it did not judge because it was its own → `refusals_bypassed`; [*ntfe-stream.confess-refusals-bypassed]
- a generation it could not accept → `last_ingest_error`, and the log; [*ntfe-stream.confess-ingest-error]
- an event it could not keep → `events_dropped`. [*ntfe-stream.confess-events-dropped]
