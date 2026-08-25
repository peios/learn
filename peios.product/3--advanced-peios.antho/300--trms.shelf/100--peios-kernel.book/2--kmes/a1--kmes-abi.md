---
title: KMES ABI Reference
description: Every KMES syscall number, structure layout, ring-buffer offset and constant, generated from the uapi headers and measured by compilation.
---

Every name, value, offset and size in this appendix is generated from
`pkm/uapi/pkm/kmes.h` by `pkm/tools/gen-kmes-abi.py`, with struct
layouts measured by compiling a probe against the real header.
Regenerate it whenever the ABI changes; do not edit it by hand. The
names here are the ones a program actually compiles against.

What a compiler cannot measure -- the error vocabulary of each
syscall, the privilege each requires by name, what the configuration
keys do, and the implementation bounds that are not in the header --
is in the notes appendix, §2.B, which this generator does not touch.

## Syscall numbers

Signatures are read from the `SYSCALL_DEFINE` sites in `pkm/kmes/`.

| Number | Constant | Signature |
|---|---|---|
| 1090 | `SYS_KMES_EMIT` | `kmes_emit(const char __user *event_type, u16 event_type_len, const void __user *payload, u32 payload_len)` |
| 1091 | `SYS_KMES_ATTACH` | `kmes_attach(unsigned int cpu_id, u64 __user *capacity)` |
| 1092 | `SYS_KMES_EMIT_BATCH` | `kmes_emit_batch(const struct kmes_emit_entry __user *entries, u32 count, u32 __user *emitted_out)` |

## Structure layouts

Offsets and sizes are measured, not declared.

### `struct kmes_emit_entry`

Total size 32 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 8 | `__u64` | `event_type` |
| 8 | 2 | `__u16` | `event_type_len` |
| 10 | 6 | `__u8[6]` | `_pad0` |
| 16 | 8 | `__u64` | `payload` |
| 24 | 4 | `__u32` | `payload_len` |
| 28 | 4 | `__u8[4]` | `_pad1` |

## Constants

Grouped as the header groups them.

*Event origin class — kmes_event_header.origin_class.*

| Constant | Value |
|---|---|
| `KMES_ORIGIN_USERSPACE` | `0` |
| `KMES_ORIGIN_KMES` | `1` |
| `KMES_ORIGIN_KACS` | `2` |
| `KMES_ORIGIN_LCS` | `3` |

*Ring-slot discovery.*

Ring slots are indexed by logical CPU id and the array is sized by the
kernel's nr_cpu_ids, so a slot inside the array holds no ring when that
CPU is not possible. Counting up from 0 until SYS_KMES_ATTACH returns
-EINVAL therefore stops at the first hole and misses every ring above
it, leaving those CPUs' events permanently unreachable.

Call SYS_KMES_ATTACH with cpu_id KMES_ATTACH_QUERY_SLOTS to learn the
slot count instead. It writes the count through the capacity argument,
returns 0, and opens no descriptor. Enumerate 0 .. count-1 and treat
-EINVAL as "this slot holds no ring", not as the end of the array.

The sentinel is outside the index space for good: nr_cpu_ids is bounded
by CONFIG_NR_CPUS, which cannot reach 2^32-1.

| Constant | Value |
|---|---|
| `KMES_ATTACH_QUERY_SLOTS` | `0xFFFFFFFF` |

*Largest entry count a single SYS_KMES_EMIT_BATCH call accepts.*

| Constant | Value |
|---|---|
| `KMES_BATCH_MAX_ENTRIES` | `256` |

*Runtime configuration registry location and keys.*

Type values match the LCS REG_\* constants: REG_DWORD is 4 and REG_QWORD
is 11. They are repeated here so &lt;pkm/kmes.h&gt; remains standalone.

| Constant | Value |
|---|---|
| `KMES_CONFIG_ROOT_HIVE` | `"Machine"` |
| `KMES_CONFIG_ROOT_SYSTEM_KEY` | `"System"` |
| `KMES_CONFIG_ROOT_KMES_KEY` | `"KMES"` |
| `KMES_CONFIG_KEY_BUFFER_CAPACITY` | `"BufferCapacity"` |
| `KMES_CONFIG_KEY_MAX_EVENT_SIZE` | `"MaxEventSize"` |
| `KMES_CONFIG_KEY_MAX_NESTING_DEPTH` | `"MaxNestingDepth"` |
| `KMES_CONFIG_KEY_MAX_EMIT_RATE_PER_PROCESS` | `"MaxEmitRatePerProcess"` |
| `KMES_CONFIG_TYPE_REG_DWORD` | `4` |
| `KMES_CONFIG_TYPE_REG_QWORD` | `11` |
| `KMES_CONFIG_BUFFER_CAPACITY_TYPE` | `11` |
| `KMES_CONFIG_BUFFER_CAPACITY_DEFAULT` | `4194304` |
| `KMES_CONFIG_BUFFER_CAPACITY_MIN` | `65536` |
| `KMES_CONFIG_BUFFER_CAPACITY_MAX` | `268435456` |
| `KMES_CONFIG_MAX_EVENT_SIZE_TYPE` | `4` |
| `KMES_CONFIG_MAX_EVENT_SIZE_DEFAULT` | `65536` |
| `KMES_CONFIG_MAX_EVENT_SIZE_MIN` | `1024` |
| `KMES_CONFIG_MAX_EVENT_SIZE_MAX` | `4194304` |
| `KMES_CONFIG_MAX_NESTING_DEPTH_TYPE` | `4` |
| `KMES_CONFIG_MAX_NESTING_DEPTH_DEFAULT` | `32` |
| `KMES_CONFIG_MAX_NESTING_DEPTH_MIN` | `4` |
| `KMES_CONFIG_MAX_NESTING_DEPTH_MAX` | `256` |
| `KMES_CONFIG_MAX_EMIT_RATE_PER_PROCESS_TYPE` | `4` |
| `KMES_CONFIG_MAX_EMIT_RATE_PER_PROCESS_DEFAULT` | `10000` |
| `KMES_CONFIG_MAX_EMIT_RATE_PER_PROCESS_MIN` | `100` |
| `KMES_CONFIG_MAX_EMIT_RATE_PER_PROCESS_MAX` | `1000000` |

*Privilege requirements.*

Values mirror the corresponding KACS privilege bits while keeping this
header standalone.

| Constant | Value |
|---|---|
| `KMES_EMIT_REQUIRED_PRIVILEGE` | `0x0000000000200000` (1ULL << 21) |
| `KMES_ATTACH_REQUIRED_PRIVILEGE` | `0x0000000000000100` (1ULL << 8) |

*On-wire event header.*

Every event in a ring begins with a fixed 77-byte header, followed by
event_type_len bytes of type string and then the msgpack payload. Events
abut at event_size stride, so a header is not generally aligned; it
crosses the ABI as raw bytes, not a C struct. Its fields, in order:

```text
__u32  event_size            total event byte length (header + type + payload)
__u32  header_size           byte offset from the event start to the payload
__u64  timestamp_ns
__u64  sequence
__u16  cpu_id
__u8   origin_class          one of KMES_ORIGIN_* above
__u8   effective_token_guid[16]
__u8   true_token_guid[16]
__u8   process_guid[16]
__u16  event_type_len        length of the type string following the header
```

The three GUIDs are 16-byte Microsoft GUID binary values
(Data1/Data2/Data3 little-endian, Data4 raw), captured from KACS at
emission time; the null GUID (16 zero bytes) means identity was
unavailable (KACS not initialised, or no process context). KMES copies
them opaquely.

Read each field at its KMES_EVENT_\*_OFFSET below. header_size locates
the payload: it is KMES_EVENT_HEADER_BASE_SIZE + event_type_len. A
future revision may grow the header, so consumers must use header_size,
not the end of the type string, to find the payload.

| Constant | Value |
|---|---|
| `KMES_EVENT_SIZE_OFFSET` | `0` |
| `KMES_EVENT_HEADER_SIZE_OFFSET` | `4` |
| `KMES_EVENT_TIMESTAMP_NS_OFFSET` | `8` |
| `KMES_EVENT_SEQUENCE_OFFSET` | `16` |
| `KMES_EVENT_CPU_ID_OFFSET` | `24` |
| `KMES_EVENT_ORIGIN_CLASS_OFFSET` | `26` |
| `KMES_EVENT_EFFECTIVE_TOKEN_GUID_OFFSET` | `27` |
| `KMES_EVENT_TRUE_TOKEN_GUID_OFFSET` | `43` |
| `KMES_EVENT_PROCESS_GUID_OFFSET` | `59` |
| `KMES_EVENT_TYPE_LEN_OFFSET` | `75` |

*Byte width of each identity GUID in the event header.*

| Constant | Value |
|---|---|
| `KMES_EVENT_GUID_SIZE` | `16` |

*Byte size of the fixed event header — the offset at which the type string begins.*

| Constant | Value |
|---|---|
| `KMES_EVENT_HEADER_BASE_SIZE` | `77` |

*Ring-buffer metadata layout.*

An attached ring is mmap'd as:

```text
page 0          producer metadata (read-only to the consumer)
page 1          consumer metadata (read-write)
ring data       the event bytes, mapped twice back-to-back so an event
                that wraps the buffer end is still contiguous.
```

The producer metadata page begins with KMES_RING_MAGIC.

| Constant | Value |
|---|---|
| `KMES_RING_MAGIC` | `"KMESRING"` |
| `KMES_RING_VERSION` | `1` |
| `KMES_METADATA_PAGE_SIZE` | `4096` |
| `KMES_METADATA_TOTAL_SIZE` | `8192` |
| `KMES_MAPPING_PRODUCER_OFFSET` | `0` |
| `KMES_MAPPING_CONSUMER_OFFSET` | `4096` |
| `KMES_MAPPING_DATA_OFFSET` | `8192` |

*Field offsets within the producer metadata page.*

| Constant | Value |
|---|---|
| `KMES_PRODUCER_MAGIC_OFFSET` | `0` |
| `KMES_PRODUCER_VERSION_OFFSET` | `8` |
| `KMES_PRODUCER_CPU_ID_OFFSET` | `12` |
| `KMES_PRODUCER_CAPACITY_OFFSET` | `16` |
| `KMES_PRODUCER_DATA_OFFSET_OFFSET` | `24` |
| `KMES_PRODUCER_GENERATION_OFFSET` | `32` |
| `KMES_PRODUCER_WRITE_POS_OFFSET` | `64` |
| `KMES_PRODUCER_TAIL_POS_OFFSET` | `72` |
| `KMES_PRODUCER_FUTEX_COUNTER_OFFSET` | `128` |

*Field offset within the consumer metadata page.*

| Constant | Value |
|---|---|
| `KMES_CONSUMER_NEED_WAKE_OFFSET` | `0` |

## Tracepoint diagnostic codes

From `uapi/pkm/trace.h`. These are a diagnostic contract for
ftrace, perf and eBPF consumers, letting a tool decode a `kmes:`
event's `reason`, `op` or `state` field without recompiling
against a specific kernel. No KMES syscall accepts or returns
them, and values are append-only.

*kmes_drop reason — why the KMES ring machinery lost an event.*

RING_FULL is a normal overwrite; TAIL_RESYNC is the silent corruption-
recovery path that discards ALL pending events; VALIDATE is a kernel-
emit size/type reject at the ring boundary; BATCH_STRUCT_INVALID is a
per-entry structural reject in the kernel batch path. Emitted by
kmes:kmes_drop. No event payload bytes.

| Constant | Value | Notes |
|---|---|---|
| `KMES_DROP_RING_FULL` | `0` | capacity overwrite; oldest event dropped |
| `KMES_DROP_TAIL_RESYNC` | `1` | corrupt ring header; pending events silently discarded |
| `KMES_DROP_VALIDATE` | `2` | single kernel-emit size/type reject |
| `KMES_DROP_BATCH_STRUCT_INVALID` | `3` | kernel-batch entry structurally invalid |

*kmes_swap reason — a bounded ring capacity swap lifecycle marker.*

BEGIN and COMPLETE/FAILED are whole-topology (cpu field is U16_MAX);
MIGRATE_SKIP is per-CPU and carries the skipped byte count in `ret`.
Emitted by kmes:kmes_swap.

| Constant | Value | Notes |
|---|---|---|
| `KMES_SWAP_BEGIN` | `0` | capacity change accepted, rings allocating |
| `KMES_SWAP_COMPLETE` | `1` | swap committed across all CPUs |
| `KMES_SWAP_MIGRATE_SKIP` | `2` | shrink: old event too large, skipped (ret=bytes) |
| `KMES_SWAP_FAILED` | `3` | swap aborted; ret is the errno |

*kmes_rate reason — the per-process token-bucket backpressure signal.*

THROTTLE is an -EAGAIN emit rejection; RECONFIGURE marks an admin rate
change clamping all buckets. Emitted by kmes:kmes_rate.

| Constant | Value | Notes |
|---|---|---|
| `KMES_RATE_THROTTLE` | `0` | emit denied -EAGAIN; tokens &lt; requested |
| `KMES_RATE_RECONFIGURE` | `1` | max emit rate reconfigured for all buckets |

*kmes_wake reason — consumer wakeup machinery.*

NOTE arms a pending wake; FUTEX is the actual futex wake of blocked
consumers. Emitted by kmes:kmes_wake.

| Constant | Value | Notes |
|---|---|---|
| `KMES_WAKE_NOTE` | `0` | wake armed; futex counter incremented |
| `KMES_WAKE_FUTEX` | `1` | blocked consumers woken |

*kmes_ring_lifecycle reason — a generation-stable ring object transition.*

`ret` is the outcome. Emitted by kmes:kmes_ring_lifecycle.

| Constant | Value | Notes |
|---|---|---|
| `KMES_RING_ALLOC` | `0` | ring backing allocated (or -ENOMEM) |
| `KMES_RING_FREE` | `1` | ring backing released |
| `KMES_RING_PRODUCER_PAGE` | `2` | producer shmem/meta page attached |
| `KMES_RING_CONSUMER_FD` | `3` | consumer anon-inode fd created |

*kmes_ingress_reject reason — why an emit request was rejected before the ring.*

OVER_MAX/OVER_CAP_HALF/SIZE_OVERFLOW are declared-size rejects;
EMIT_OVERSIZE is a staged event too large at ring-write time;
BATCH_PARTIAL marks a batch that validated fewer entries than requested.
Emitted by kmes:kmes_ingress_reject.

| Constant | Value | Notes |
|---|---|---|
| `KMES_INGRESS_OVER_MAX` | `0` | event_size exceeds configured max_event_size |
| `KMES_INGRESS_OVER_CAP_HALF` | `1` | event_size exceeds ring_capacity/2 |
| `KMES_INGRESS_SIZE_OVERFLOW` | `2` | declared header/event size overflow |
| `KMES_INGRESS_EMIT_OVERSIZE` | `3` | staged event exceeds live capacity/2 at emit |
| `KMES_INGRESS_BATCH_PARTIAL` | `4` | batch staged fewer entries than requested |

*kmes_validate reason — the C-boundary result of the Rust staged-event validator.*

The Rust side collapses its structural checks into one nonzero return;
only visible type/payload lengths and `ret` are recorded here. Emitted
by kmes:kmes_validate.

| Constant | Value | Notes |
|---|---|---|
| `KMES_VAL_EINVAL` | `0` | Rust msgpack/structural validation rejected |
