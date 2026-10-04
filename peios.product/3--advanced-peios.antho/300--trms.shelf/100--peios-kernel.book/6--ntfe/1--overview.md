---
title: Overview
description: NTFE is the Peios packet engine — where it stands in the kernel, what it replaced, how its C glue and Rust core divide the work, and the terms this chapter uses.
---

NTFE — the Network Traffic Filtering Engine — is the kernel's packet
filter. It executes the packet layers of PNP, the Peios Network Policy:
PNP is the policy language and its registry layout under
`Machine\System\Network`, and NTFE is one of the components that carry
it out (netd is another, for the interface layer). It stands at
the netfilter seats, judges every traversal against the policy it reads
from the LCS registry itself, and applies the result: a verdict on the
packet, side effects on the flow and machine, and an event for whoever
is watching. [*ntfe-engine.judges-from-registry-policy-itself] No userspace process is in the enforcement path; the
viewer daemon (pnpd) observes and authors, it never decides. [*ntfe-engine.no-userspace-in-enforcement-path]

## What it replaced

Peios ships a clean slate below NTFE. The netfilter **hook framework**
and **conntrack** (built in, with events, zones and timeouts; helpers
off) are kept, as are `nf_defrag` and the `nf_reject` machinery NTFE uses
to phrase refusals. [*ntfe-engine.keeps-hooks-conntrack-defrag-reject] Everything that was a policy *frontend* is
configured out: nf_tables, the xtables family (`iptables`, `ip6tables`,
`ebtables`, `arptables`), ipset, NFQUEUE, NFLOG, the flow table offload,
bridge netfilter, the netfilter BPF link and IPVS. [*ntfe-engine.policy-frontends-configured-out] `NF_NAT` is built but
dormant. [*ntfe-engine.nf-nat-built-but-dormant] The kernel config gate (`kernel/verify-kernel-config.sh`)
asserts both halves so a merge cannot quietly bring a frontend back. [*ntfe-engine.config-gate-asserts-both-halves]

One consequence is worth knowing: conntrack's hooks are demand-activated,
historically by a ct-using iptables rule. With no frontend left, NTFE pins
them itself at init (`nf_ct_netns_get(&init_net, NFPROTO_INET)`); without
that pin `nf_ct_get()` is NULL on every packet and the `FlowState` fact
reads `untracked` forever. [*ntfe-engine.pins-conntrack-hooks-at-init]

## Two halves

The engine is split along the line that kernels are good at and pure
code is good at.

**`net/ntfe/` (C)** owns everything that touches the kernel: the hook
registrations and the dispatch law (`seats.c`), building the fact
snapshot from an `sk_buff` (`snapshot.c`), RCU publication of policy
generations (`policy.c`), walking the registry into the builder
(`ingest.c`), the three machinery stores — flow tags on a conntrack
extension (`tags.c`), counter tables (`counters.c`), report emission into
KMES (`report.c`) — the Flow layer's sentence cache and dispatch
(`flow.c`), the refusals a `REJECT` sends (`refuse.c`), and the verdict
event ring behind `/dev/peios-ntfe` (`events.c`). [*ntfe-engine.c-glue-owns-kernel-facing-work]

**`pnp-core` (Rust, `pkm/crates/pnp-core`)** owns everything the policy
*means*: the action language, the fact vocabulary and operators,
registry-shaped ingestion and validation, the forest, and the evaluation
algorithm. [*ntfe-engine.core-owns-policy-meaning] It is `no_std`, allocates only through the fallible PKM
wrappers, and has no I/O. [*ntfe-engine.core-no-std-fallible-alloc-no-io] The same source compiles twice: under cargo,
where a test suite encodes every ratified law by name, and into the
kernel, staged by `kernel/stage-rust-core.sh` as modules of the
`security/pkm` Rust crate and reached over a C ABI (`kacs/ntfe_runtime.rs`,
the bridge). [*ntfe-engine.core-compiles-for-cargo-and-kernel] Nothing about a rule's semantics exists in C. [*ntfe-engine.no-rule-semantics-in-c]

The bridge is the only place the two meet. [*ntfe-engine.bridge-is-only-meeting-point] C hands it a snapshot and a
forest; it resolves the forest's machinery facts against the packet by
calling back into the stores, evaluates, and applies the effects — after
collation, so a `COUNT` lands after this packet's own reads and a
`REPORT` can carry the verdict. [*ntfe-engine.effects-applied-after-collation]

## Terms

- **Traversal** — one packet passing one direction through the machine.
- **Seat** — a netfilter hook NTFE stands at: the device *ingress* and
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
  ingestion; [*ntfe-engine.generation-advances-per-ingestion] 0 means nothing was ever ingested and every layer is
  permissive, loudly. [*ntfe-engine.generation-zero-is-permissive]
- **Forest** — a layer's rule trees plus the machinery names it mentions:
  the tags it reads or writes, the counter streams it writes, and the
  counter views it reads.
- **Effect** — a side effect an evaluation yields (`TAG`, `COUNT`,
  `REPORT`, a prompt), applied by the glue.
- **Confession** — a counter in the engine status for something the
  engine refused or could not do. Nothing in NTFE fails silently. [*ntfe-engine.nothing-fails-silently]
- **Owner** — the identity KACS stamps on an inet socket (§3.12.2): the
  effective token and process facts at the last act that committed the
  socket to a role. What the Flow layer's `Local.*` facts are read from.
- **Endpoint kind** — what stands at a local end of a flow: `program`,
  `kernel`, `shared` or `none` (§6.9).

The chapter follows a packet: the seats it meets (§6.2), the snapshot
taken of it (§6.3), how the forest judges it (§6.4), where that forest
came from (§6.5), the stores its effects land in (§6.6), the event that
records it (§6.7), what happens when it is the first packet of a flow
(§6.8), and who stands at its local end (§6.9). §6.A is the generated
ABI of `/dev/peios-ntfe`; §6.B is what the ABI tables cannot say.
