---
title: NTFE ABI Notes
description: What the NTFE ABI tables cannot say for themselves — the device's read and poll semantics, what each ioctl expects and returns, the error vocabulary, and the stability promise.
---

§6.A is generated from `pkm/uapi/pkm/ntfe.h` and holds only what a
compiler can measure. This appendix holds the rest.

## Stability

The ABI is **experimental** while NTFE grows (PEI-598): no stability
promise until the design ships. `peios_ntfe_status.abi` carries
`PEIOS_NTFE_ABI_VERSION`; [*ntfe-abi-notes.status-abi-carries-version] a consumer checks it before trusting any other
field or record layout. [*ntfe-abi-notes.consumer-checks-abi-first] Version 2 (the machinery slice) added the
event's `reject_kind`, the store confessions and `counter_cells` and
`reporting_level` in the status, and the counters ioctl. Version 3 (the
Flow layer) added the `LOCAL_OUT` seat and `Flow` layer ids, the
`REJUDGED` event flag, the Flow and refusal counters in the status, and
the flows ioctl. Version 4 (the identity facts) added the endpoints'
identities to the event and the flow record, the `IDENTITY_UNRESOLVED`
event flag and the `identity_unresolved` counter (in a reserved slot,
so the status kept its size). Version 5 renamed the device and every
symbol from `pnp` to `ntfe`, let more than one file hold the device open,
and added `changes_noted`, `changes_walked` and `contexts` to the status:
the first took one of the two reserved words version 4 left, the other
two are new, so the status grew by two words and keeps one reserved. [*ntfe-abi-notes.abi-v5-changes] pnpd and the kernel ship together on the
experimental edition, so the check is a guard, not a negotiation.

## `/dev/peios-ntfe`

A misc device, created mode 0600 and owned by uid 0 — but on Peios mode
bits and uids decide nothing (DAC is neutralised): KACS decides an
`open()` by the opener's token against the node's security descriptor
(§3.9.5). On devtmpfs that descriptor is inherited from the seeded
root's, which grants `GENERIC_ALL` to SYSTEM alone, so the device is
SYSTEM's unless trusted userspace sets another. [*ntfe-abi-notes.device-misc-0600-root-only]

| Operation | Semantics | Errors |
|---|---|---|
| `open()` | Any number of openers. | — [*ntfe-abi-notes.open-any-number-of-openers] |
| `read(buf, len)` | Returns whole `struct peios_ntfe_event` records only — never a partial one — up to 64 per call, oldest first, consuming them. Blocks on an empty ring unless `O_NONBLOCK`. | `EINVAL` — `len` smaller than one record; `EBUSY` — another open file is the stream's reader; `EAGAIN` — empty and non-blocking; `EINTR`; `ENOMEM`; `EFAULT` — the records it took are lost (below) [*ntfe-abi-notes.read-whole-records-oldest-first] [*ntfe-abi-notes.read-einval-len-below-one-record] [*ntfe-abi-notes.read-ebusy-other-file-is-reader] [*ntfe-abi-notes.read-eagain-empty-nonblocking] [*ntfe-abi-notes.read-eintr] [*ntfe-abi-notes.read-enomem] [*ntfe-abi-notes.read-efault] |
| `poll()` | `POLLIN \| POLLRDNORM` when at least one event waits. | — [*ntfe-abi-notes.poll-readable-when-event-waits] |
| `ioctl(PEIOS_NTFE_IOC_STATUS, struct peios_ntfe_status *)` | Fills the status snapshot. Cumulative counters since boot. | `EFAULT` [*ntfe-abi-notes.status-ioctl-fills-snapshot] |
| `ioctl(PEIOS_NTFE_IOC_COUNTERS, struct peios_ntfe_counters_query *)` | `buf`/`buf_len` describe a user buffer of `struct peios_ntfe_counter_rec`; on return `count` is how many were written and `total` how many cells exist. A short buffer is not an error — the two numbers disagree. Best-effort snapshot: cells may change between records. | `EFAULT`; `ENOMEM` [*ntfe-abi-notes.counters-ioctl-count-and-total] [*ntfe-abi-notes.counters-ioctl-efault] [*ntfe-abi-notes.counters-ioctl-enomem] |
| `ioctl(PEIOS_NTFE_IOC_FLOWS, struct peios_ntfe_flows_query *)` | Same contract over `struct peios_ntfe_flow_rec`: `count` written, `total` live flows the walk saw. Records are copied out between hash buckets, so the dump is a best-effort picture of a table that changes under it. | `EFAULT`; `ENOMEM` [*ntfe-abi-notes.flows-ioctl-count-and-total] [*ntfe-abi-notes.flows-ioctl-efault] [*ntfe-abi-notes.flows-ioctl-enomem] |
| `ioctl(PEIOS_NTFE_IOC_LISTENERS, struct peios_ntfe_listeners_query *)` | Same contract over `struct peios_ntfe_listener_rec`: every TCP socket in the listening state and every bound UDP / UDP-Lite socket of the root network namespace, with the identity KACS stamped on it (§6.9). `total` is how many the walk saw. A hash bucket holding more sockets than one copy-out batch is walked again from where the batch filled, so with room for every record `count` equals `total`. | `EFAULT`; `ENOMEM` [*ntfe-abi-notes.listeners-ioctl-count-and-total] [*ntfe-abi-notes.listeners-ioctl-efault] [*ntfe-abi-notes.listeners-ioctl-enomem] |
| other ioctls | — | `ENOTTY` [*ntfe-abi-notes.unknown-ioctl-enotty] |

Sequence numbers are monotonic per boot. [*ntfe-abi-notes.sequence-monotonic-per-boot] A gap between consecutive
records read is the number of events the ring overwrote while the
reader was away, plus any a faulting `read()` consumed; [*ntfe-abi-notes.sequence-gap-equals-overwritten] `events_dropped` in the status is the running
total of the overwrites. [*ntfe-abi-notes.events-dropped-running-total] A `read()` that fails with `EFAULT` has
already taken its records off the ring: they are lost, and counted
nowhere but in that gap. [*ntfe-abi-notes.read-efault-consumes-records]

## Event fields

- `attributed` is the winning rule's path relative to its layer key,
  UTF-8, NUL-terminated, truncated to `PEIOS_NTFE_EV_ATTR_LEN` − 1 bytes
  (95), which may split a multi-byte character. [*ntfe-abi-notes.event-attributed-relative-nul-truncated]
  Two reserved values: `backstop` (nothing yielded) and `fail-closed`
  (evaluation failed). [*ntfe-abi-notes.event-attributed-reserved-values]
- `effects` packs the effect counts the evaluation *yielded* — `tags |
  counts << 8 | reports << 16 | prompts << 24`, each saturating at 255. [*ntfe-abi-notes.event-effects-packing-saturating]
  What the stores then *applied* is in the status confessions, not in
  the event. [*ntfe-abi-notes.event-effects-yielded-not-applied]
- `reject_kind` is meaningful only when `verdict` is
  `PEIOS_NTFE_EV_VERDICT_REJECT`; [*ntfe-abi-notes.event-reject-kind-only-on-reject] a degraded reject (`flags &
  PEIOS_NTFE_EV_F_REJECT_DEGRADED`) still carries the kind the rule
  chose. [*ntfe-abi-notes.event-degraded-reject-keeps-kind]
- `PEIOS_NTFE_EV_F_REJUDGED` marks a `Flow`-layer evaluation that
  replaced a stale sentence (policy change or time edge). [*ntfe-abi-notes.event-rejudged-flag] A packet
  answered by a current sentence produces no event at all. [*ntfe-abi-notes.cached-sentence-packet-no-event]
- `layer` 2 is `Flow`; `seat` 4 is `LOCAL_OUT`. [*ntfe-abi-notes.layer-2-flow-seat-4-local-out] A `Flow` event's
  `direction` is the endpoint judged: the originator's side for a normal
  flow, each seat's own for a loopback flow's two judgments. [*ntfe-abi-notes.flow-event-direction-is-endpoint-judged]
- Addresses: the first 4 bytes when `addr_family` is 4, all 16 when 6,
  undefined when 0. [*ntfe-abi-notes.event-address-bytes-by-family] Ports are 0 when the fact was absent — check
  `protocol`. [*ntfe-abi-notes.event-ports-zero-when-absent]
- `flow_state` 0 means the fact was absent (the ingress seat), not that
  the flow was untracked; untracked is 5. [*ntfe-abi-notes.event-flow-state-0-absent-5-untracked]
- The identity fields (ABI 4) are set on `Flow` events only and zero
  elsewhere. [*ntfe-abi-notes.event-identity-fields-flow-only] `local_kind` / `remote_kind` are `PEIOS_NTFE_EV_LOCAL_*`:
  `ABSENT` (0) for a non-Flow event, and for `remote` whenever the
  other end is not local; [*ntfe-abi-notes.event-kind-absent-cases] `remote` is filled only on a loopback flow. [*ntfe-abi-notes.event-remote-loopback-only]
  For a `PROGRAM` end, `*_guid`, `*_pid` and `*_comm` are the process
  facts at the socket's stamp, `*_user` the token's user SID and
  `*_service` its per-service SID, both binary and self-sized (byte 1
  is the sub-authority count; all zero = absent — a user program has no
  service SID). [*ntfe-abi-notes.event-program-end-fields] `*_unresolved` says the end could not be attributed and
  was reported as the kernel's or as absent. [*ntfe-abi-notes.event-unresolved-flag]

## Counter records

- `name` is the stream name (a rule's `COUNT(Name)`), NUL-terminated;
  `hash` is its FNV-1a identity as the kernel keys tables. [*ntfe-abi-notes.counter-rec-name-and-hash]
- `keyspec` says which of `src_addr`, `dst_addr`, `ifindex` are
  meaningful for this cell's key; the others are zero. [*ntfe-abi-notes.counter-rec-keyspec-unkeyed-zero] `family` is 4, 6,
  or 0 when no address fact is keyed. [*ntfe-abi-notes.counter-rec-family]
- `window_secs[i]` / `window_value[i]` for `i < n_windows` are the
  table's windows and this cell's current value in each; [*ntfe-abi-notes.counter-rec-window-values] `total` is
  cumulative since the cell was created (or migrated — see §6.6); [*ntfe-abi-notes.counter-rec-total-cumulative]
  `last_secs` is `CLOCK_REALTIME` seconds of the last write, for
  staleness. [*ntfe-abi-notes.counter-rec-last-secs]
- The dump lists every table's cells consecutively; group by `(name,
  keyspec)` to reconstruct tables. [*ntfe-abi-notes.counter-dump-tables-consecutive]

## Flow records

- `id` is conntrack's own id for the entry (`nf_ct_get_id()`), stable
  for the flow's life and the key to use across dumps. [*ntfe-abi-notes.flow-rec-id-stable]
- `src_addr`/`dst_addr`, the ports and the ICMP fields are the
  *original-direction* tuple — the originator first. [*ntfe-abi-notes.flow-rec-original-direction-tuple] For ICMP, `src_port`
  carries the echo id and `icmp_type`/`icmp_code` the type and code;
  `dst_port` is 0. [*ntfe-abi-notes.flow-rec-icmp-fields]
- `direction`, `ifindex` and `loopback` are meaningful only when `judged`
  is 1: they were recorded at the Flow layer's first judgment. [*ntfe-abi-notes.flow-rec-judged-gates-first-judgment-fields] A flow
  with `judged == 0` has had no Flow judgment recorded: every packet of
  it that reached the flow dispatch (§6.8) found no Flow forest (a
  permissive generation) or failed closed, or none did — or it has no
  extension at all, and so nowhere to record one (`flow_uncached`; its
  sentences and identities read empty too). [*ntfe-abi-notes.flow-rec-unjudged-began-permissive]
- The sentences are parallel arrays indexed by slot (UAPI records hold
  scalars only): slot 0 is the flow's sentence; slot 1 is only ever
  filled for a loopback flow (its inbound endpoint). [*ntfe-abi-notes.flow-rec-sentence-slots] A slot with
  `sentence_generation == 0` is empty. [*ntfe-abi-notes.flow-rec-generation-0-empty] `sentence_expires_at` 0 means
  never. [*ntfe-abi-notes.flow-rec-expires-0-never] `sentence_rule_hash` is FNV-1a-64 (offset
  `0xcbf29ce484222325`, prime `0x100000001b3`) of the whole attributing
  path relative to the layer key, however long — not of the event's
  truncated `attributed`. `backstop` hashes like any other path; [*ntfe-abi-notes.flow-rec-rule-hash-fnv1a-64]
  `fail-closed` is never a sentence's, since a failed evaluation is
  not cached. [*ntfe-abi-notes.flow-rec-fail-closed-never-cached]
- `packets`/`bytes` are conntrack's accounting, original then reply; [*ntfe-abi-notes.flow-rec-accounting-original-then-reply]
  NTFE turns conntrack accounting on at init
  (`net.netfilter.nf_conntrack_acct`). [*ntfe-abi-notes.init-enables-conntrack-acct]
- `timeout_secs` is the entry's remaining lifetime as conntrack sees it; [*ntfe-abi-notes.flow-rec-timeout-remaining]
  `start_secs` is `CLOCK_REALTIME` seconds when conntrack created it. [*ntfe-abi-notes.flow-rec-start-secs]
- `tag_hash`/`tag_value` hold up to `PEIOS_NTFE_FLOW_MAX_TAGS` (8)
  present tags by name hash and value; [*ntfe-abi-notes.flow-rec-up-to-8-tags] `n_tags` is the flow's *total*,
  so a value above 8 means some are not listed. [*ntfe-abi-notes.flow-rec-n-tags-is-total]
- The identities (ABI 4) are per sentence slot, recorded at the flow's
  first judgment and fixed: `owner_kind[slot]` is `PEIOS_NTFE_EV_LOCAL_*`
  (`ABSENT` = not resolved; `ABSENT` with `owner_unresolved[slot]` set
  = judged but unattributed, such as a loopback sender the outbound seat
  never recorded); [*ntfe-abi-notes.flow-rec-owner-kind-per-slot] the per-slot arrays are flattened at a
  fixed stride — `owner_guid` 16 bytes per slot, `owner_comm` 16,
  `owner_user` 68, `owner_service` 32 — so slot 1's user SID starts at
  byte 68. [*ntfe-abi-notes.flow-rec-owner-array-strides] Slot 1 is filled only for a loopback flow. [*ntfe-abi-notes.flow-rec-owner-slot-1-loopback-only]

## Listener records

- One record per socket prepared to receive: TCP in `LISTEN`, and UDP /
  UDP-Lite bound to a port (`connected` when it also has a peer and so
  receives from one address only). [*ntfe-abi-notes.listener-rec-one-per-receiving-socket] `addr` all zero is the wildcard; [*ntfe-abi-notes.listener-rec-zero-addr-wildcard]
  `ifindex` is `SO_BINDTODEVICE`, 0 for any; [*ntfe-abi-notes.listener-rec-ifindex-bindtodevice] `reuseport` marks a member
  of a `SO_REUSEPORT` group, of which each member is listed. [*ntfe-abi-notes.listener-rec-reuseport-each-member-listed] `v6only`
  says an `AF_INET6` socket refuses v4-mapped traffic — a v6 socket
  without it answers on both families. [*ntfe-abi-notes.listener-rec-v6only]
- The owner fields are those of the flow record's slot, for the socket's
  current stamp: `owner_kind` is `PROGRAM` or `KERNEL` (a socket nobody
  stamped reads `KERNEL` with `owner_unresolved` set). [*ntfe-abi-notes.listener-rec-owner-current-stamp]
- The walk is the root namespace's tables only, copied out between hash
  buckets: a best-effort list of a set that changes under it. [*ntfe-abi-notes.listener-dump-root-ns-best-effort]

## Bounds not in the header

| Bound | Value |
|---|---|
| Event ring | 4096 records, overwrite-oldest [*ntfe-abi-notes.bound-event-ring-4096] |
| Records per `read()` | 64 [*ntfe-abi-notes.bound-read-64-records] |
| Counter cells per table | 4096 (`PEIOS_NTFE_COUNTER_MAX_KEYS`, kernel-internal) [*ntfe-abi-notes.bound-counter-cells-per-table-4096] |
| Distinct tags per flow | 64 (`PEIOS_NTFE_TAG_MAX_PER_FLOW`, kernel-internal) [*ntfe-abi-notes.bound-tags-per-flow-64] |
| Rule depth / rules per layer | 12 (roots are depth 0: 13 levels) / 4096 (ingestion) [*ntfe-abi-notes.bound-rule-depth-12-rules-4096] |
| Longest counter window | 86 400 s [*ntfe-abi-notes.bound-counter-window-86400s] |
| Sentences per flow | 2 (slot 1 only for loopback flows) [*ntfe-abi-notes.bound-sentences-per-flow-2] |
| Flow records batched per copy-out | 32 (kernel-internal) [*ntfe-abi-notes.bound-flow-batch-32] |
| Listener records batched per copy-out | 32 (kernel-internal) [*ntfe-abi-notes.bound-listener-batch-32] |

## Build configuration

`CONFIG_PEIOS_NTFE` (bool) depends on `SECURITY_PKM`, `NETFILTER`,
`NETFILTER_INGRESS`, `NETFILTER_EGRESS` and `NF_CONNTRACK=y` — NTFE is built in and reads flow
facts on the packet path, so conntrack must be too. [*ntfe-abi-notes.config-ntfe-dependencies] `CONFIG_PEIOS_NTFE_KUNIT`
builds the kernel-resident tests (`pkm_kunit_ntfe`), defaulting to
`SECURITY_PKM_KUNIT`. [*ntfe-abi-notes.config-kunit-default] The production fragment (`build/config/pkm.fragment`)
enables NTFE and configures the nf_tables/xtables family out; [*ntfe-abi-notes.production-fragment-ntfe-on-nftables-off]
`kernel/verify-kernel-config.sh` asserts both. [*ntfe-abi-notes.verify-kernel-config-asserts-fragment]
