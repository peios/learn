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
`reporting_level` in the status, and the counters ioctl. pnpd and the
kernel ship together on the experimental edition, so the check is a
guard, not a negotiation.

## `/dev/peios-pnp`

A misc device, mode 0600, root-only by ownership.

| Operation | Semantics | Errors |
|---|---|---|
| `open()` | One reader at a time. | `EBUSY` — already open elsewhere |
| `read(buf, len)` | Returns whole `struct peios_pnp_event` records only — never a partial one — up to 64 per call, oldest first, consuming them. Blocks on an empty ring unless `O_NONBLOCK`. | `EINVAL` — `len` smaller than one record; `EAGAIN` — empty and non-blocking; `EINTR`; `ENOMEM`; `EFAULT` |
| `poll()` | `POLLIN \| POLLRDNORM` when at least one event waits. | — |
| `ioctl(PEIOS_PNP_IOC_STATUS, struct peios_pnp_status *)` | Fills the status snapshot. Cumulative counters since boot. | `EFAULT` |
| `ioctl(PEIOS_PNP_IOC_COUNTERS, struct peios_pnp_counters_query *)` | `buf`/`buf_len` describe a user buffer of `struct peios_pnp_counter_rec`; on return `count` is how many were written and `total` how many cells exist. A short buffer is not an error — the two numbers disagree. Best-effort snapshot: cells may change between records. | `EFAULT`; `ENOMEM` |
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
- Addresses: the first 4 bytes when `addr_family` is 4, all 16 when 6,
  undefined when 0. Ports are 0 when the fact was absent — check
  `protocol`.
- `flow_state` 0 means the fact was absent (the ingress seat), not that
  the flow was untracked; untracked is 5.

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

## Bounds not in the header

| Bound | Value |
|---|---|
| Event ring | 4096 records, overwrite-oldest |
| Records per `read()` | 64 |
| Counter cells per table | 4096 (`PEIOS_PNP_COUNTER_MAX_KEYS`, kernel-internal) |
| Distinct tags per flow | 64 (`PEIOS_PNP_TAG_MAX_PER_FLOW`, kernel-internal) |
| Rule depth / rules per layer | 12 / 4096 (ingestion) |
| Longest counter window | 86 400 s |

## Build configuration

`CONFIG_PEIOS_PNP` (bool) depends on `SECURITY_PKM`, `NETFILTER_INGRESS`,
`NETFILTER_EGRESS` and `NF_CONNTRACK=y` — PNP is built in and reads flow
facts on the packet path, so conntrack must be too. `CONFIG_PEIOS_PNP_KUNIT`
builds the kernel-resident tests (`pkm_kunit_pnp`), defaulting to
`SECURITY_PKM_KUNIT`. The production fragment (`build/config/pkm.fragment`)
enables PNP and configures the nf_tables/xtables family out;
`kernel/verify-kernel-config.sh` asserts both.
