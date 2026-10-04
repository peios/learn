---
title: The Flow layer
description: The second rung — one judgment per local endpoint of a flow, cached on the conntrack entry as a sentence, re-judged when the policy or the clock makes it stale, and dumped for the viewer.
---

The Flow layer (`Rules\Flow`, the rung-2 design on PEI-598) is the same
rule atom, verbs and evaluation as the per-packet layers, applied to a
different unit: the **flow**, what conntrack tracks. It exists because
the per-packet evaluator has no early exit — collation and
side-effects-always mean every packet walks the whole forest, so an
`Established → PASS` rule saves nothing — and because flows carry facts
(a start time, relatedness, one day an owner) and effect units (a
connection, not a packet) that packets do not. The Packet layer becomes
the cheap filter in front; the decisions move here and run once per
connection. [*ntfe-flow.decisions-run-once-per-connection]

## One judgment per local endpoint

`peios_ntfe_flow_dispatch()` (`flow.c`) is called at the IP seats:
inbound, at `LOCAL_IN`, for every packet the Packet layer passed;
outbound, at `LOCAL_OUT`, for every packet, before any Packet judgment
— the Packet layer judges outbound traffic at egress, after it (§6.2). [*ntfe-flow.dispatch-after-packet-pass]
An untracked packet (`snap->flow == NULL`) has no flow to judge and is
accepted, `NF_ACCEPT`: inbound the Packet verdict stands, outbound the
Packet layer judges it next at egress. [*ntfe-flow.untracked-packet-keeps-packet-verdict] A
tracked packet reads its flow's **sentence**:

- a *current* sentence — the policy generation that wrote it is the
  active one, and its expiry (if any) has not passed — is applied
  without evaluation (`flow_cached`); [*ntfe-flow.current-sentence-applied-without-evaluation]
- otherwise the Flow forest is evaluated against the snapshot
  (`peios_ntfe_policy_eval(PEIOS_NTFE_LAYER_FLOW)`, counted in `judged`
  and `flow_judged`), the outcome is written as the new sentence, an
  event is emitted (with `REJUDGED` when a stale sentence was replaced,
  `flow_rejudged` or `flow_expired` saying why), and the verdict is
  applied. [*ntfe-flow.stale-sentence-evaluated-and-rewritten] A refusal goes out before the event, so the event can confess
  a degradation. [*ntfe-flow.refusal-sent-before-event]

No Flow forest at all (generation 0, or no `Flow` key) is permissive,
counted, and caches nothing. [*ntfe-flow.no-forest-permissive-uncached]

What the Flow forest judges is the **flow view**, not the packet's
snapshot: a Flow fact is one identical for every packet of the flow, so
`ntfe_flow_view()` builds it from the flow. [*ntfe-flow.judges-flow-view-not-packet] A reply-direction packet's
addresses and ports are swapped back to the original tuple (and its
ICMP type replaced by the tuple's); [*ntfe-flow.reply-view-uses-original-tuple] the direction is the originator's,
recorded at the first judgment along with the interface, the VLAN, the
peer's MAC and the endpoints' identities (§6.9), so a re-judgment on a
reply sees exactly the facts the first judgment saw. [*ntfe-flow.rejudgment-sees-first-judgment-facts] (Found live before the fix: an inbound viewer flow
re-judged on its reply packet as `out`, and matched `outbound-ok`.) A
loopback flow's view takes the slot's direction. [*ntfe-flow.loopback-view-takes-slot-direction] The refusal, when the
verdict is one, answers the packet in hand; [*ntfe-flow.refusal-answers-packet-in-hand] the event describes the flow
as judged. [*ntfe-flow.event-describes-flow-as-judged]

A normal flow has one local endpoint and one sentence, slot 0, written
at the originator's seat on the first packet; the reply direction, and
every later packet, reads it. [*ntfe-flow.normal-flow-one-sentence-slot-0] `Direction` in the judgment is the
originator's side. [*ntfe-flow.direction-is-originator-side] A **loopback** flow has two local endpoints and two
sentences: the outbound one (slot 0) at `LOCAL_OUT` and the inbound one
(slot 1) at `LOCAL_IN`, both on the same first packet, [*ntfe-flow.loopback-two-sentences-same-first-packet] and every packet
of it answers to the *stricter* of the two (DROP > REJECT(Refused) >
REJECT(Prohibited) > PASS). [*ntfe-flow.loopback-stricter-sentence-applies] The comparison is made before any
refusal is sent: a `REJECT` overruled by the other end's `DROP` sends
nothing, and one overruled by the other end's stricter `REJECT` sends
that one's kind. [*ntfe-flow.loopback-stricter-decided-before-refusal] Loopback-ness is the seat's device
(`IFF_LOOPBACK`, `snap->loopback`); [*ntfe-flow.loopback-by-seat-device] a stale other-endpoint sentence is
not applied — it is that seat's to refresh when it next sees the flow. [*ntfe-flow.stale-other-slot-not-applied]

## The sentence

`struct peios_ntfe_sentence` lives in NTFE's conntrack extension
(`include/linux/peios_ntfe.h`), two per flow: the generation that judged
(0 = empty), `expires_at` (epoch seconds, 0 = never), the FNV-1a-64 hash
of the attributing rule's whole path (the outcome's `attributed_hash`:
the event's `attributed` text is cut short, the hash never is; the same
identity the tag and counter stores use for names, so the viewer
resolves it against the policy), the verdict and the reject kind. [*ntfe-flow.sentence-fields] Alongside: `start_secs`, stamped when
conntrack created the entry (`peios_ntfe_ct_ext_add()`) — the `Start.*`
facts — [*ntfe-flow.start-secs-stamped-at-ct-creation] and, from the first judgment, the interface, the direction and
whether the flow is loopback, for the dump. [*ntfe-flow.extension-records-first-judgment-facts]

Writes take the flow's lock (`ct->lock`, `_bh`), zero the generation
first, write the fields, and publish the generation last with a release
store. [*ntfe-flow.sentence-write-publishes-generation-last] Reads are lock-free on the hook path: an acquire load of the
generation, the fields, then a re-check of the generation — a torn
sentence (a writer in between) reads as absent and the flow is simply
evaluated. [*ntfe-flow.torn-sentence-reads-absent] Two packets of a new flow racing on two CPUs may both
evaluate; the second sentence write wins (both judged the identities
the first resolution recorded, §6.9), and the effects ran twice — the only
place NTFE tolerates that, because the alternative is a lock on the fast
path for a race that needs a flow's first two packets to arrive
concurrently. [*ntfe-flow.first-packet-race-second-write-wins]

The cache holds the verdict only. [*ntfe-flow.cache-holds-verdict-only] Effects run at every evaluation of the
flow and never per packet. [*ntfe-flow.effects-per-evaluation-not-per-packet] `DROP` and `REJECT` sentences persist for the
life of a flow conntrack has confirmed: a cached `REJECT` refuses every
subsequent packet of it. [*ntfe-flow.drop-reject-sentences-persist] A `DROP` or `REJECT` on a flow's first packet
at a seat that stands before confirmation — `LOCAL_IN` for an inbound
flow, `LOCAL_OUT` for an outbound one — leaves nothing to persist:
nothing kills the entry, but its packet is dropped before conntrack
confirms it (the refusal is filed as the entry's reply, which confirms
nothing), so the unconfirmed entry dies with the packet, sentence and
all. A retransmitted SYN is then a fresh flow, judged again — effects
included — and refused again. [*ntfe-flow.new-flow-drop-reject-kills-entry] So the cached refusal answers only on a
confirmed flow: one re-judged mid-life, or a loopback flow's inbound
end, judged at `LOCAL_IN` after `POST_ROUTING` confirmed the entry. A
`Refused` reset to a confirmed TCP flow also moves it to conntrack's
`CLOSE` state (`nf_ct_set_closing()`), whose short timeout ends it. [*ntfe-flow.refused-tcp-flow-set-closing] A flow whose extension could not be allocated has nowhere to hold
a sentence and is evaluated on every packet (`flow_uncached`). [*ntfe-flow.no-extension-evaluated-per-packet]

## Staleness

A sentence is stale when its generation is not the current one (a
policy published, or a network context published — §6.5 — both advance
the one counter) or
`t_secs >= expires_at`. [*ntfe-flow.stale-by-generation-or-expiry] Both are checked lazily, on the flow's next
packet — an idle flow past a policy change is killed when it next
speaks, or conntrack times it out; there are no timers and no walk of
the table at publication. [*ntfe-flow.staleness-checked-lazily] Grandfathering was rejected: the registry must
not lie about what is enforced, and a `REJECT` rule must be able to
reject something already running. A refused packet of an
established TCP flow tears down both ends at once (§6.2): the end that
sent it is refused with the kind's story, and the packet, turned into a
reset, is sent on to the other end. [*ntfe-flow.refused-established-tcp-teardown-both-ends] Before the teardown existed, a
killed viewer stream froze at the local end while the silent host peer
waited for its own next packet to meet the cached `REJECT` sentence —
correct under the lazy law, and half a kill.

The expiry is the evaluation's `expires_at` (§6.4): the earliest moment
any live-time condition the judgment *consulted* would flip. [*ntfe-flow.expiry-earliest-consulted-flip] A forest
with no time conditions never expires a sentence; [*ntfe-flow.no-time-conditions-never-expires] `Start.*` conditions
never contribute, which is the point of them. [*ntfe-flow.start-conditions-never-contribute-expiry]

## The flows dump

`PEIOS_NTFE_IOC_FLOWS` walks conntrack's table the way `ctnetlink` does —
`local_bh_disable()`, each bucket under its `nf_conntrack_locks` lock,
original-direction entries of `init_net` that are neither expired nor
dying [*ntfe-flow.dump-walks-live-original-entries] — and fills `struct peios_ntfe_flow_rec` per flow: conntrack's id,
family, protocol, the original tuple (ports, or ICMP id and type/code),
`seen_reply`/`assured`/`related`, the remaining lifetime, packet and
byte counts (NTFE turns conntrack accounting on at init — the
`net.netfilter.nf_conntrack_acct` sysctl, `init_net.ct.sysctl_acct` —
since it is conntrack's consumer now), [*ntfe-flow.init-enables-conntrack-acct] and the extension: start time, first-judgment interface
and direction, loopback, both sentences, both ends' identities, and up
to eight tags by hash with the flow's total tag count. [*ntfe-flow.dump-record-contents]
Records are batched in kernel memory (32 to a batch) and copied to user
between passes over the buckets, never under a lock; a bucket holding
more flows than the batch has room for is walked again under its lock
from where the batch filled, rather than losing the rest. [*ntfe-flow.dump-copies-out-between-buckets] The walk counts every live flow it saw so
a short buffer is visible, and is best-effort against a table that
changes under it. [*ntfe-flow.dump-counts-every-live-flow]

## What was decided against

- **Backstop inheritance** (the flow's verdict as the Packet layer's
  compiled-in default): unnecessary once Packet is the filter in front
  and passes tracked traffic by shipped configuration.
- **Two layers, Inbound and Outbound**: direction-blind rules are common
  and shadowing gives the direction-specific exceptions; the posture is
  a visible root rule; per-seat direction pruning is a future evaluator
  optimisation, invisible to authors.
- **Effects on first judgment only**: a kill by `REJECT, REPORT(n)` must
  report; the `COUNT` noise is per generation, not per packet.
- **Identity in the sentence.** The sentence caches the verdict; the
  identities the judgment read are recorded beside it (§6.9), not
  re-derived per packet.
