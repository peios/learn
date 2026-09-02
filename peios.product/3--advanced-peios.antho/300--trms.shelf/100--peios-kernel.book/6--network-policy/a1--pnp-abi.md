---
title: PNP ABI Reference
description: Every PNP ioctl number, event and status structure layout, counter record layout and constant, generated from the uapi header and measured by compilation.
---

Every name, value, offset and size in this appendix is generated from
`pkm/uapi/pkm/pnp.h` by `pkm/tools/gen-pnp-abi.py`, with struct
layouts measured by compiling a probe against the real header.
Regenerate it whenever the ABI changes; do not edit it by hand. The
names here are the ones a program actually compiles
against. [*abi.generated-from-source]

What a compiler cannot measure -- the device's read and poll
semantics, what each ioctl expects, the error vocabulary, and the
bounds that are not in the header -- is in the notes appendix, §6.B,
which this generator does not touch.

## Ioctl requests [*abi.ioctl-numbers]

Request numbers on `/dev/peios-pnp`, packed as `<linux/ioctl.h>`
packs them (direction, argument size, type `'N'`, number).

| Constant | Value | Definition |
|---|---|---|
| `PEIOS_PNP_IOC_STATUS` | `0x81204E01` | `_IOR(PEIOS_PNP_IOC_TYPE, PEIOS_PNP_IOC_STATUS_NR, struct peios_pnp_status)` |
| `PEIOS_PNP_IOC_COUNTERS` | `0xC0184E02` | `_IOWR(PEIOS_PNP_IOC_TYPE, PEIOS_PNP_IOC_COUNTERS_NR, struct peios_pnp_counters_query)` |

## Structure layouts

Offsets and sizes are measured, not declared.

### `struct peios_pnp_event` [*abi.struct-peios-pnp-event]

Total size 176 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 8 | `__u64` | `seq` |
| 8 | 8 | `__u64` | `t_ns` |
| 16 | 1 | `__u8` | `seat` |
| 17 | 1 | `__u8` | `layer` |
| 18 | 1 | `__u8` | `verdict` |
| 19 | 1 | `__u8` | `flags` |
| 20 | 1 | `__u8` | `direction` |
| 21 | 1 | `__u8` | `addr_family` |
| 22 | 1 | `__u8` | `protocol` |
| 23 | 1 | `__u8` | `flow_state` |
| 24 | 4 | `__u32` | `ifindex` |
| 28 | 2 | `__u16` | `src_port` |
| 30 | 2 | `__u16` | `dst_port` |
| 32 | 2 | `__u16` | `ether_type` |
| 34 | 1 | `__u8` | `reject_kind` |
| 35 | 1 | `__u8` | `_pad0` |
| 36 | 16 | `__u8[16]` | `src_addr` |
| 52 | 16 | `__u8[16]` | `dst_addr` |
| 68 | 4 | `__u32` | `length` |
| 72 | 4 | `__u32` | `effects` |
| 76 | 96 | `__u8[PEIOS_PNP_EV_ATTR_LEN]` | `attributed` |
| 172 | 4 | `__u32` | `_pad1` |

### `struct peios_pnp_status` [*abi.struct-peios-pnp-status]

Total size 288 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 8 | `__u64` | `abi` |
| 8 | 8 | `__u64` | `generation` |
| 16 | 8 | `__u64` | `enforcing` |
| 24 | 8 | `__u64` | `events_dropped` |
| 32 | 8 | `__u64` | `seen_ingress` |
| 40 | 8 | `__u64` | `seen_egress` |
| 48 | 8 | `__u64` | `seen_local_in` |
| 56 | 8 | `__u64` | `deferred` |
| 64 | 8 | `__u64` | `fallback_judged` |
| 72 | 8 | `__u64` | `parse_errors` |
| 80 | 8 | `__u64` | `judged` |
| 88 | 8 | `__u64` | `permissive` |
| 96 | 8 | `__u64` | `fail_closed` |
| 104 | 8 | `__u64` | `verdict_pass` |
| 112 | 8 | `__u64` | `verdict_drop` |
| 120 | 8 | `__u64` | `verdict_reject` |
| 128 | 8 | `__u64` | `reject_degraded` |
| 136 | 8 | `__u64` | `fx_tags` |
| 144 | 8 | `__u64` | `fx_counts` |
| 152 | 8 | `__u64` | `fx_reports` |
| 160 | 8 | `__u64` | `fx_prompts` |
| 168 | 8 | `__u64` | `last_ingest_error` |
| 176 | 8 | `__u64` | `last_ingest_t_ns` |
| 184 | 8 | `__u64` | `tag_writes` |
| 192 | 8 | `__u64` | `tag_untracked` |
| 200 | 8 | `__u64` | `tag_refused` |
| 208 | 8 | `__u64` | `count_writes` |
| 216 | 8 | `__u64` | `count_key_absent` |
| 224 | 8 | `__u64` | `count_refused` |
| 232 | 8 | `__u64` | `reports_emitted` |
| 240 | 8 | `__u64` | `counter_cells` |
| 248 | 8 | `__u64` | `reporting_level` |
| 256 | 32 | `__u64[4]` | `_reserved` |

### `struct peios_pnp_counter_rec` [*abi.struct-peios-pnp-counter-rec]

Total size 232 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 64 | `__u8[PEIOS_PNP_COUNTER_NAME_LEN]` | `name` |
| 64 | 8 | `__u64` | `hash` |
| 72 | 1 | `__u8` | `keyspec` |
| 73 | 1 | `__u8` | `family` |
| 74 | 2 | `__u8[2]` | `_pad0` |
| 76 | 4 | `__s32` | `ifindex` |
| 80 | 16 | `__u8[16]` | `src_addr` |
| 96 | 16 | `__u8[16]` | `dst_addr` |
| 112 | 8 | `__u64` | `total` |
| 120 | 8 | `__u64` | `last_secs` |
| 128 | 4 | `__u32` | `n_windows` |
| 132 | 4 | `__u32` | `_pad1` |
| 136 | 32 | `__u32[PEIOS_PNP_COUNTER_MAX_WINDOWS]` | `window_secs` |
| 168 | 64 | `__u64[PEIOS_PNP_COUNTER_MAX_WINDOWS]` | `window_value` |

### `struct peios_pnp_counters_query` [*abi.struct-peios-pnp-counters-query]

Total size 24 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 8 | `__u64` | `buf` |
| 8 | 4 | `__u32` | `buf_len` |
| 12 | 4 | `__u32` | `count` |
| 16 | 4 | `__u32` | `total` |
| 20 | 4 | `__u32` | `_pad0` |

## Constants

Grouped as the header groups them.

*PNP — Peios Network Policy: the verdict event stream and engine status.*

The engine (net/pnp) judges every traversal at its standing seats and
appends one event per evaluation to a bounded ring. /dev/peios-pnp (mode
0600; one reader at a time) drains it: read() returns whole events only
— never a partial record — and blocks when the ring is empty unless
O_NONBLOCK; poll() raises POLLIN when events are waiting. A slow reader
loses the OLDEST events, and the loss is confessed in
peios_pnp_status.events_dropped (the honesty rule: drops are counted,
never silent).

Events are emitted for real evaluations (a published forest judged the
traversal) and for fail-closed drops; permissive traversals (a layer
with no forest — all of them at generation 0) emit nothing, because
there is no decision to attribute. Status tells that story instead:
generation 0 means "not enforcing", loudly.

This ABI is EXPERIMENTAL while PNP grows: no stability promise until the
design ships (PEI-598). Check `abi` before trusting the rest.

| Constant | Value |
|---|---|
| `PEIOS_PNP_ABI_VERSION` | `2` |

*Which standing seat judged the traversal.* [*abi.seat-values]

| Constant | Value |
|---|---|
| `PEIOS_PNP_EV_SEAT_INGRESS` | `1` |
| `PEIOS_PNP_EV_SEAT_EGRESS` | `2` |
| `PEIOS_PNP_EV_SEAT_LOCAL_IN` | `3` |

*Which rules layer.* [*abi.layer-values]

| Constant | Value |
|---|---|
| `PEIOS_PNP_EV_LAYER_PACKET` | `0` |
| `PEIOS_PNP_EV_LAYER_RAWPACKET` | `1` |

*The verdict, in strictness order.* [*abi.verdict-values]

| Constant | Value |
|---|---|
| `PEIOS_PNP_EV_VERDICT_PASS` | `0` |
| `PEIOS_PNP_EV_VERDICT_REJECT` | `1` |
| `PEIOS_PNP_EV_VERDICT_DROP` | `2` |

*The story a REJECT told (meaningful iff verdict == REJECT).* [*abi.reject-kinds]

| Constant | Value | Notes |
|---|---|---|
| `PEIOS_PNP_EV_REJECT_REFUSED` | `0` | RST / port-unreachable |
| `PEIOS_PNP_EV_REJECT_PROHIBITED` | `1` | admin-prohibited |

*Traversal direction.* [*abi.direction-values]

| Constant | Value |
|---|---|
| `PEIOS_PNP_EV_DIR_IN` | `0` |
| `PEIOS_PNP_EV_DIR_OUT` | `1` |

*Flow state as the snapshot carried it (0 = the fact was absent).* [*abi.flow-state-values]

| Constant | Value |
|---|---|
| `PEIOS_PNP_EV_FLOW_ABSENT` | `0` |
| `PEIOS_PNP_EV_FLOW_NEW` | `1` |
| `PEIOS_PNP_EV_FLOW_ESTABLISHED` | `2` |
| `PEIOS_PNP_EV_FLOW_RELATED` | `3` |
| `PEIOS_PNP_EV_FLOW_INVALID` | `4` |
| `PEIOS_PNP_EV_FLOW_UNTRACKED` | `5` |

*Event flags.* [*abi.event-flags]

| Constant | Value | Notes |
|---|---|---|
| `PEIOS_PNP_EV_F_BACKSTOP` | `0x01` | nothing yielded; DROP |
| `PEIOS_PNP_EV_F_FAIL_CLOSED` | `0x02` | evaluation failed; DROP |
| `PEIOS_PNP_EV_F_REJECT_DEGRADED` | `0x04` | REJECT emitted as DROP |
| `PEIOS_PNP_EV_ATTR_LEN` | `96` |  |

One counter cell, as the counters dump reports it: the stream and key-
spec of its table, the key it holds (only the facts the key-spec names
are meaningful; the rest are zero), the cumulative total, and the value
of every window the table answers.

| Constant | Value |
|---|---|
| `PEIOS_PNP_COUNTER_NAME_LEN` | `64` |
| `PEIOS_PNP_COUNTER_MAX_WINDOWS` | `8` |

*Key-spec bits.* [*abi.keyspec-bits]

| Constant | Value |
|---|---|
| `PEIOS_PNP_KEY_SRC_ADDR` | `0x01` |
| `PEIOS_PNP_KEY_DST_ADDR` | `0x02` |
| `PEIOS_PNP_KEY_INTERFACE` | `0x04` |

The counters dump: fills `buf` with as many records as fit; `count` is
how many were written, `total` how many cells exist (so a short buffer
is visible).

| Constant | Value |
|---|---|
| `PEIOS_PNP_IOC_TYPE` | `0x0000004E` |
| `PEIOS_PNP_IOC_STATUS_NR` | `0x00000001` |
| `PEIOS_PNP_IOC_COUNTERS_NR` | `0x00000002` |
