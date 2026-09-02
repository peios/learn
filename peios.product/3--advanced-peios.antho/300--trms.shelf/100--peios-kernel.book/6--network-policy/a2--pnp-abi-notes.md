---
title: PNP ABI Notes
description: What the PNP ABI tables cannot say for themselves — the device's read and poll semantics, what each ioctl expects and returns, the error vocabulary, and the stability promise.
---

§6.A is generated from `pkm/uapi/pkm/pnp.h` and holds only what a
compiler can measure. This appendix holds the rest.

## Stability

The ABI is **experimental** while PNP grows (PEI-598): no stability
promise until the design ships. `peios_pnp_status.abi` carries
`PEIOS_PNP_ABI_VERSION`; a consumer checks it before trusting any other
field or record layout. Version 2 (the machinery slice) added the
event's `reject_kind`, the store confessions and `counter_cells` and
`reporting_level` in the status, and the counters ioctl. Version 3 (the
Flow layer) added the `LOCAL_OUT` seat and `Flow` layer ids, the
`REJUDGED` event flag, the Flow and refusal counters in the status, and
the flows ioctl. Version 4 (the identity facts) added the endpoints'
identities to the event and the flow record, the `IDENTITY_UNRESOLVED`
event flag and the `identity_unresolved` counter (in a reserved slot,
so the status kept its size). pnpd and the kernel ship together on the
experimental edition, so the check is a guard, not a negotiation.

## `/dev/peios-pnp`

A misc device, mode 0600, root-only by ownership.

| Operation | Semantics | Errors |
|---|---|---|
| `open()` | One reader at a time. | `EBUSY` — already open elsewhere |
| `read(buf, len)` | Returns whole `struct peios_pnp_event` records only — never a partial one — up to 64 per call, oldest first, consuming them. Blocks on an empty ring unless `O_NONBLOCK`. | `EINVAL` — `len` smaller than one record; `EAGAIN` — empty and non-blocking; `EINTR`; `ENOMEM`; `EFAULT` |
| `poll()` | `POLLIN \| POLLRDNORM` when at least one event waits. | — |
| `ioctl(PEIOS_PNP_IOC_STATUS, struct peios_pnp_status *)` | Fills the status snapshot. Cumulative counters since boot. | `EFAULT` |
| `ioctl(PEIOS_PNP_IOC_COUNTERS, struct peios_pnp_counters_query *)` | `buf`/`buf_len` describe a user buffer of `struct peios_pnp_counter_rec`; on return `count` is how many were written and `total` how many cells exist. A short buffer is not an error — the two numbers disagree. Best-effort snapshot: cells may change between records. | `EFAULT`; `ENOMEM` |
| `ioctl(PEIOS_PNP_IOC_FLOWS, struct peios_pnp_flows_query *)` | Same contract over `struct peios_pnp_flow_rec`: `count` written, `total` live flows the walk saw. Records are copied out between hash buckets, so the dump is a best-effort picture of a table that changes under it. | `EFAULT`; `ENOMEM` |
| `ioctl(PEIOS_PNP_IOC_LISTENERS, struct peios_pnp_listeners_query *)` | Same contract over `struct peios_pnp_listener_rec`: every TCP socket in the listening state and every bound UDP / UDP-Lite socket of the root network namespace, with the identity KACS stamped on it (§6.9). `total` is how many the walk saw. | `EFAULT`; `ENOMEM` |
| other ioctls | — | `ENOTTY` |

Sequence numbers are monotonic per boot. A gap between consecutive
records read is exactly the number of events the ring overwrote while
the reader was away; `events_dropped` in the status is the running
total.

## Event fields

- `attributed` is the winning rule's path relative to its layer key,
  UTF-8, NUL-terminated, truncated to `PEIOS_PNP_EV_ATTR_LEN` − 1 bytes.
  Two reserved values: `backstop` (nothing yielded) and `fail-closed`
  (evaluation failed).
- `effects` packs the effect counts the evaluation *yielded* — `tags |
  counts << 8 | reports << 16 | prompts << 24`, each saturating at 255.
  What the stores then *applied* is in the status confessions, not in
  the event.
- `reject_kind` is meaningful only when `verdict` is
  `PEIOS_PNP_EV_VERDICT_REJECT`; a degraded reject (`flags &
  PEIOS_PNP_EV_F_REJECT_DEGRADED`) still carries the kind the rule
  chose.
- `PEIOS_PNP_EV_F_REJUDGED` marks a `Flow`-layer evaluation that
  replaced a stale sentence (policy change or time edge). A packet
  answered by a current sentence produces no event at all.
- `layer` 2 is `Flow`; `seat` 4 is `LOCAL_OUT`. A `Flow` event's
  `direction` is the endpoint judged: the originator's side for a normal
  flow, each seat's own for a loopback flow's two judgments.
- Addresses: the first 4 bytes when `addr_family` is 4, all 16 when 6,
  undefined when 0. Ports are 0 when the fact was absent — check
  `protocol`.
- `flow_state` 0 means the fact was absent (the ingress seat), not that
  the flow was untracked; untracked is 5.
- The identity fields (ABI 4) are set on `Flow` events only and zero
  elsewhere. `local_kind` / `remote_kind` are `PEIOS_PNP_EV_LOCAL_*`:
  `ABSENT` (0) for a non-Flow event, and for `remote` whenever the
  other end is not local; `remote` is filled only on a loopback flow.
  For a `PROGRAM` end, `*_guid`, `*_pid` and `*_comm` are the process
  facts at the socket's stamp, `*_user` the token's user SID and
  `*_service` its per-service SID, both binary and self-sized (byte 1
  is the sub-authority count; all zero = absent — a user program has no
  service SID). `*_unresolved` says the end could not be attributed and
  was reported as the kernel's or as absent.

## Counter records

- `name` is the stream name (a rule's `COUNT(Name)`), NUL-terminated;
  `hash` is its FNV-1a identity as the kernel keys tables.
- `keyspec` says which of `src_addr`, `dst_addr`, `ifindex` are
  meaningful for this cell's key; the others are zero. `family` is 4, 6,
  or 0 when no address fact is keyed.
- `window_secs[i]` / `window_value[i]` for `i < n_windows` are the
  table's windows and this cell's current value in each; `total` is
  cumulative since the cell was created (or migrated — see §6.6);
  `last_secs` is `CLOCK_REALTIME` seconds of the last write, for
  staleness.
- The dump lists every table's cells consecutively; group by `(name,
  keyspec)` to reconstruct tables.

## Flow records

- `id` is conntrack's own id for the entry (`nf_ct_get_id()`), stable
  for the flow's life and the key to use across dumps.
- `src_addr`/`dst_addr`, the ports and the ICMP fields are the
  *original-direction* tuple — the originator first. For ICMP, `src_port`
  carries the echo id and `icmp_type`/`icmp_code` the type and code;
  `dst_port` is 0.
- `direction`, `ifindex` and `loopback` are meaningful only when `judged`
  is 1: they were recorded at the Flow layer's first judgment. A flow
  with `judged == 0` began under a permissive generation.
- The sentences are parallel arrays indexed by slot (UAPI records hold
  scalars only): slot 0 is the flow's sentence; slot 1 is only ever
  filled for a loopback flow (its inbound endpoint). A slot with
  `sentence_generation == 0` is empty. `sentence_expires_at` 0 means
  never. `sentence_rule_hash` is FNV-1a-64 (offset
  `0xcbf29ce484222325`, prime `0x100000001b3`) of the attributing path
  relative to the layer key — `backstop` and `fail-closed` hash like any
  other path.
- `packets`/`bytes` are conntrack's accounting, original then reply;
  PNP enables `nf_conntrack_acct` at init.
- `timeout_secs` is the entry's remaining lifetime as conntrack sees it;
  `start_secs` is `CLOCK_REALTIME` seconds when conntrack created it.
- `tag_hash`/`tag_value` hold up to `PEIOS_PNP_FLOW_MAX_TAGS` (8)
  present tags by name hash and value; `n_tags` is the flow's *total*,
  so a value above 8 means some are not listed.
- The identities (ABI 4) are per sentence slot, recorded at the flow's
  first judgment and fixed: `owner_kind[slot]` is `PEIOS_PNP_EV_LOCAL_*`
  (`ABSENT` = not yet resolved); the per-slot arrays are flattened at a
  fixed stride — `owner_guid` 16 bytes per slot, `owner_comm` 16,
  `owner_user` 68, `owner_service` 32 — so slot 1's user SID starts at
  byte 68. Slot 1 is filled only for a loopback flow.

## Listener records

- One record per socket prepared to receive: TCP in `LISTEN`, and UDP /
  UDP-Lite bound to a port (`connected` when it also has a peer and so
  receives from one address only). `addr` all zero is the wildcard;
  `ifindex` is `SO_BINDTODEVICE`, 0 for any; `reuseport` marks a member
  of a `SO_REUSEPORT` group, of which each member is listed. `v6only`
  says an `AF_INET6` socket refuses v4-mapped traffic — a v6 socket
  without it answers on both families.
- The owner fields are those of the flow record's slot, for the socket's
  current stamp: `owner_kind` is `PROGRAM` or `KERNEL` (a socket nobody
  stamped reads `KERNEL` with `owner_unresolved` set).
- The walk is the root namespace's tables only, copied out between hash
  buckets: a best-effort list of a set that changes under it.

## Bounds not in the header

| Bound | Value |
|---|---|
| Event ring | 4096 records, overwrite-oldest |
| Records per `read()` | 64 |
| Counter cells per table | 4096 (`PEIOS_PNP_COUNTER_MAX_KEYS`, kernel-internal) |
| Distinct tags per flow | 64 (`PEIOS_PNP_TAG_MAX_PER_FLOW`, kernel-internal) |
| Rule depth / rules per layer | 12 / 4096 (ingestion) |
| Longest counter window | 86 400 s |
| Sentences per flow | 2 (slot 1 only for loopback flows) |
| Flow records batched per copy-out | 32 (kernel-internal) |
| Listener records batched per copy-out | 32 (kernel-internal) |

## Build configuration

`CONFIG_PEIOS_PNP` (bool) depends on `SECURITY_PKM`, `NETFILTER_INGRESS`,
`NETFILTER_EGRESS` and `NF_CONNTRACK=y` — PNP is built in and reads flow
facts on the packet path, so conntrack must be too. `CONFIG_PEIOS_PNP_KUNIT`
builds the kernel-resident tests (`pkm_kunit_pnp`), defaulting to
`SECURITY_PKM_KUNIT`. The production fragment (`build/config/pkm.fragment`)
enables PNP and configures the nf_tables/xtables family out;
`kernel/verify-kernel-config.sh` asserts both.
