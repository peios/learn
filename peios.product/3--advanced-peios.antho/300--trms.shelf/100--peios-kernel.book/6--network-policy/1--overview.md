---
title: Overview
description: PNP is the Peios packet engine — where it stands in the kernel, what it replaced, how its C glue and Rust core divide the work, and the terms this chapter uses.
---

PNP — Peios Network Policy — is the kernel's packet filter. It stands at
the netfilter seats, judges every traversal against a policy it reads
from the LCS registry itself, and applies the result: a verdict on the
packet, side effects on the flow and machine, and an event for whoever
is watching. No userspace process is in the enforcement path; the
viewer daemon (pnpd) observes and authors, it never decides.

## What it replaced

Peios ships a clean slate below PNP. The netfilter **hook framework**
and **conntrack** (built in, with events, zones and timeouts; helpers
off) are kept, as are `nf_defrag` and the `nf_reject` machinery PNP uses
to phrase refusals. Everything that was a policy *frontend* is
configured out: nf_tables, the xtables family (`iptables`, `ip6tables`,
`ebtables`, `arptables`), ipset, NFQUEUE, NFLOG, the flow table offload,
bridge netfilter, the netfilter BPF link and IPVS. `NF_NAT` is built but
dormant. The kernel config gate (`kernel/verify-kernel-config.sh`)
asserts both halves so a merge cannot quietly bring a frontend back.

One consequence is worth knowing: conntrack's hooks are demand-activated,
historically by a ct-using iptables rule. With no frontend left, PNP pins
them itself at init (`nf_ct_netns_get(&init_net, NFPROTO_INET)`); without
that pin `nf_ct_get()` is NULL on every packet and the `FlowState` fact
reads `untracked` forever.

## Two halves

The engine is split along the line that kernels are good at and pure
code is good at.

**`net/pnp/` (C)** owns everything that touches the kernel: the hook
registrations and the dispatch law (`seats.c`), building the fact
snapshot from an `sk_buff` (`snapshot.c`), RCU publication of policy
generations (`policy.c`), walking the registry into the builder
(`ingest.c`), the three machinery stores — flow tags on a conntrack
extension (`tags.c`), counter tables (`counters.c`), report emission into
KMES (`report.c`) — the Flow layer's sentence cache and dispatch
(`flow.c`), the refusals a `REJECT` sends (`refuse.c`), and the verdict
event ring behind `/dev/peios-pnp` (`events.c`).

**`pnp-core` (Rust, `pkm/crates/pnp-core`)** owns everything the policy
*means*: the action language, the fact vocabulary and operators,
registry-shaped ingestion and validation, the forest, and the evaluation
algorithm. It is `no_std`, allocates only through the fallible PKM
wrappers, and has no I/O. The same source compiles twice: under cargo,
where a test suite encodes every ratified law by name, and into the
kernel, staged by `kernel/stage-rust-core.sh` as modules of the
`security/pkm` Rust crate and reached over a C ABI (`kacs/pnp_runtime.rs`,
the bridge). Nothing about a rule's semantics exists in C.

The bridge is the only place the two meet. C hands it a snapshot and a
forest; it resolves the forest's machinery facts against the packet by
calling back into the stores, evaluates, and applies the effects — after
collation, so a `COUNT` lands after this packet's own reads and a
`REPORT` can carry the verdict.

## Terms

- **Traversal** — one packet passing one direction through the machine.
- **Seat** — a netfilter hook PNP stands at: the device *ingress* and
  *egress* seats (per interface) and the two IP seats, *inbound*
  (`LOCAL_IN`) and *outbound* (`LOCAL_OUT`).
- **Layer** — one of the three rule forests, `RawPacket`, `Packet` and
  `Flow`, each a registry key under `Machine\System\Network\Rules`.
- **Flow** — what conntrack tracks: a tuple-identified, bidirectional
  exchange. The unit the Flow layer judges.
- **Sentence** — the Flow layer's cached verdict on a flow: verdict,
  generation, expiry, on the flow's conntrack extension.
- **Snapshot** — the immutable set of facts one traversal is judged
  against at its seat.
- **Generation** — one published policy. Advances on every successful
  ingestion; 0 means nothing was ever ingested and every layer is
  permissive, loudly.
- **Forest** — a layer's rule trees plus the machinery names it mentions:
  the tags it reads or writes, the counter streams it writes, and the
  counter views it reads.
- **Effect** — a side effect an evaluation yields (`TAG`, `COUNT`,
  `REPORT`, a prompt), applied by the glue.
- **Confession** — a counter in the engine status for something the
  engine refused or could not do. Nothing in PNP fails silently.

The chapter follows a packet: the seats it meets (§6.2), the snapshot
taken of it (§6.3), how the forest judges it (§6.4), where that forest
came from (§6.5), the stores its effects land in (§6.6), the event that
records it (§6.7), and what happens when it is the first packet of a
flow (§6.8). §6.A is the generated ABI of `/dev/peios-pnp`; §6.B is what
the ABI tables cannot say.
