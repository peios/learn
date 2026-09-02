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
connection.

## One judgment per local endpoint

`peios_pnp_flow_dispatch()` (`flow.c`) is called at the IP seats for
every packet the Packet layer passed. An untracked packet (`snap->flow ==
NULL`) has no flow to judge: the Packet verdict stands, `NF_ACCEPT`. A
tracked packet reads its flow's **sentence**:

- a *current* sentence — the policy generation that wrote it is the
  active one, and its expiry (if any) has not passed — is applied
  without evaluation (`flow_cached`);
- otherwise the Flow forest is evaluated against the snapshot
  (`peios_pnp_policy_eval(PEIOS_PNP_LAYER_FLOW)`, counted in `judged`
  and `flow_judged`), the outcome is written as the new sentence, an
  event is emitted (with `REJUDGED` when a stale sentence was replaced,
  `flow_rejudged` or `flow_expired` saying why), and the verdict is
  applied. A refusal goes out before the event, so the event can confess
  a degradation.

No Flow forest at all (generation 0, or no `Flow` key) is permissive,
counted, and caches nothing.

What the Flow forest judges is the **flow view**, not the packet's
snapshot: a Flow fact is one identical for every packet of the flow, so
`pnp_flow_view()` builds it from the flow. A reply-direction packet's
addresses and ports are swapped back to the original tuple (and its
ICMP type replaced by the tuple's); the direction is the originator's,
recorded at the first judgment along with the interface, the VLAN and
the peer's MAC, so a re-judgment on a reply sees exactly the facts the
first judgment saw. (Found live before the fix: an inbound viewer flow
re-judged on its reply packet as `out`, and matched `outbound-ok`.) A
loopback flow's view takes the slot's direction. The refusal, when the
verdict is one, answers the packet in hand; the event describes the flow
as judged.

A normal flow has one local endpoint and one sentence, slot 0, written
at the originator's seat on the first packet; the reply direction, and
every later packet, reads it. `Direction` in the judgment is the
originator's side. A **loopback** flow has two local endpoints and two
sentences: the outbound one (slot 0) at `LOCAL_OUT` and the inbound one
(slot 1) at `LOCAL_IN`, both on the same first packet, and every packet
of it answers to the *stricter* of the two (DROP > REJECT(Refused) >
REJECT(Prohibited) > PASS). Loopback-ness is the seat's device
(`IFF_LOOPBACK`, `snap->loopback`); a stale other-endpoint sentence is
not applied — it is that seat's to refresh when it next sees the flow.

## The sentence

`struct peios_pnp_sentence` lives in PNP's conntrack extension
(`include/linux/peios_pnp.h`), two per flow: the generation that judged
(0 = empty), `expires_at` (epoch seconds, 0 = never), the FNV-1a-64 hash
of the attributing rule's path (the same identity the tag and counter
stores use for names, so the viewer resolves it against the policy), the
verdict and the reject kind. Alongside: `start_secs`, stamped when
conntrack created the entry (`peios_pnp_ct_ext_add()`) — the `Start.*`
facts — and, from the first judgment, the interface, the direction and
whether the flow is loopback, for the dump.

Writes take the flow's lock (`ct->lock`, `_bh`), zero the generation
first, write the fields, and publish the generation last with a release
store. Reads are lock-free on the hook path: an acquire load of the
generation, the fields, then a re-check of the generation — a torn
sentence (a writer in between) reads as absent and the flow is simply
evaluated. Two packets of a new flow racing on two CPUs may both
evaluate; the second write wins, and the effects ran twice — the only
place PNP tolerates that, because the alternative is a lock on the fast
path for a race that needs a flow's first two packets to arrive
concurrently.

The cache holds the verdict only. Effects run at every evaluation of the
flow and never per packet. `DROP` and `REJECT` sentences persist for the
flow's life (a cached `REJECT` refuses every subsequent packet, so a
retransmitted SYN gets its answer); a `DROP` or `REJECT` on a *new* flow
kills the unconfirmed entry, so the retransmit is a fresh flow, judged
again. A flow whose extension could not be allocated has nowhere to hold
a sentence and is evaluated on every packet (`flow_uncached`).

## Staleness

A sentence is stale when its generation is not the current one or
`t_secs >= expires_at`. Both are checked lazily, on the flow's next
packet — an idle flow past a policy change is killed when it next
speaks, or conntrack times it out; there are no timers and no walk of
the table at publication. Grandfathering was rejected: the registry must
not lie about what is enforced, and a `REJECT` rule must be able to
reject something already running (on TCP, that is an RST to both ends).

The expiry is the evaluation's `expires_at` (§6.4): the earliest moment
any live-time condition the judgment *consulted* would flip. A forest
with no time conditions never expires a sentence; `Start.*` conditions
never contribute, which is the point of them.

## The flows dump

`PEIOS_PNP_IOC_FLOWS` walks conntrack's table the way `ctnetlink` does —
`local_bh_disable()`, each bucket under its `nf_conntrack_locks` lock,
original-direction entries of `init_net` that are neither expired nor
dying — and fills `struct peios_pnp_flow_rec` per flow: conntrack's id,
family, protocol, the original tuple (ports, or ICMP id and type/code),
`seen_reply`/`assured`/`related`, the remaining lifetime, packet and
byte counts (PNP turns `sysctl_acct` on at init — it is conntrack's
consumer now), and the extension: start time, first-judgment interface
and direction, loopback, both sentences, and up to eight tags by hash.
Records are batched in kernel memory and copied to user between
buckets, never under a lock; the walk counts every live flow it saw so
a short buffer is visible, and is best-effort against a table that
changes under it.

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
- **Identity facts** (`Owner`, `Service`, the listener, the image): rung
  3, PEI-28.
