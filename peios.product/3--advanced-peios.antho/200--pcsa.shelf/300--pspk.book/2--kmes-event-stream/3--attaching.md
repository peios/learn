---
title: Attaching and Mapping
description: How a consumer attaches to a per-CPU ring, the double mapping that makes wrapping invisible, and the producer metadata page.
---

## Attaching

A consumer attaches to one per-CPU ring buffer at a time by calling
`kmes_attach` with a logical CPU index and a pointer to a `u64` that
receives the buffer's capacity. The call returns a file descriptor.

The caller MUST hold SeSecurityPrivilege, enabled; the call fails with
`EPERM` otherwise.

The CPU index uses the same numbering as the `cpu_id` field in the
ring buffer metadata and in event headers. Indexes run from 0 to one
below the *slot count*, and the set of buffers is fixed when KMES
initialises and does not change while the system runs.

The slot count is not the number of buffers. Slots are indexed by
logical CPU id, so a slot within the range holds no buffer when that
CPU is not possible, and the two quantities differ on any system whose
possible-CPU mask is sparse. An index at or beyond the slot count fails
with `EINVAL`, and so does an index inside it whose slot holds no
buffer; the two are not distinguishable from the return value.

A consumer discovers the slot count by calling `kmes_attach` with the
CPU index `KMES_ATTACH_QUERY_SLOTS`. The call writes the slot count
through the capacity pointer, returns 0, and opens no descriptor. It is
gated on SeSecurityPrivilege exactly as an attach is.

A consumer MUST enumerate by walking every index from 0 to one below
the slot count, and MUST treat `EINVAL` as "this slot holds no buffer"
and continue. A consumer MUST NOT treat the first `EINVAL` as the end
of the set: doing so silently abandons every buffer above the first
hole, whose events then accumulate and are overwritten with no consumer
able to reach them.

A consumer SHOULD attach to every buffer in the set: a buffer with no
consumer still receives events, and those events are lost when it
wraps.

A consumer MAY call `kmes_attach` more than once for the same CPU and
receives a distinct file descriptor each time. All descriptors for one
CPU refer to the same buffer, and therefore to the same producer
metadata, consumer metadata, and data region. Multiple consumers MAY
attach to one buffer concurrently. Each maintains its own read
position, in its own memory; the kernel does not track consumer read
positions, does not know how many consumers exist, and does not know
how far behind any of them is. The consumer metadata page is shared
per buffer and is not a per-consumer read-position store.

The descriptor supports exactly two operations: `mmap()` and
`close()`. Closing it invalidates the mapping.

## Mapping

The consumer maps the whole region in a single call:

```
mmap(NULL, 8192 + 2 * capacity, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0)
```

The mapping request MUST use `MAP_SHARED`, MUST pass an offset of
zero, and MUST pass a length of exactly `8192 + 2 * capacity`, where
`capacity` is the value `kmes_attach` returned. Any other combination
fails with `EINVAL`. The consumer does not map the regions separately.

The mapped region has three parts:

| Offset | Size | Region | Consumer access |
|---|---|---|---|
| 0 | 4096 | Producer metadata page | Read-only |
| 4096 | 4096 | Consumer metadata page | Read-write |
| 8192 | 2 × capacity | Data region | Read-only |

Per-page permissions are enforced by the kernel regardless of the
`PROT` flags requested: the producer metadata page and the data region
are mapped read-only whatever the consumer asks for, and no privilege
raises that. The consumer metadata page is writable by ordinary
stores.

`capacity` is always a power of two, so a position's offset within the
data region is `position & (capacity - 1)`.

## The double mapping

The data region occupies `2 × capacity` bytes of address space backed
by `capacity` bytes of memory: the same pages appear twice,
consecutively. An event that crosses the end of the buffer is
therefore readable as one contiguous byte sequence starting at its
wrapped offset, and a consumer MUST NOT implement wrap handling of its
own. Reading an event at offset `position & (capacity - 1)` is always
correct, even when the event extends past `capacity`.

A consumer MUST NOT read past `event_size` bytes from the start of an
event. The data region is not scrubbed when events are overwritten, so
the bytes beyond an event are unrelated remnants of older events.

## Producer metadata page

The producer metadata page is written by KMES and read by consumers.
Fields are separated onto 64-byte cache lines by update frequency, so
that the position fields KMES writes on every event do not invalidate
the line holding the fields it never writes.

### Bytes 0–63: identification

| Offset | Size | Type | Field | Description |
|---|---|---|---|---|
| 0 | 8 | `[u8; 8]` | `magic` | `4B 4D 45 53 52 49 4E 47`, `KMESRING` in ASCII. Compared byte by byte, not as an integer. |
| 8 | 4 | `u32` | `version` | Ring buffer format version. This version is 1. |
| 12 | 2 | `u16` | `cpu_id` | The CPU this buffer belongs to. |
| 14 | 2 | `u16` | `reserved0` | Reserved, zero. |
| 16 | 8 | `u64` | `capacity` | Data region capacity in bytes. A power of two. |
| 24 | 8 | `u64` | `data_offset` | Offset from the start of the mapping to the data region. 8192. |
| 32 | 8 | `u64` | `generation` | Buffer generation. Starts at 1 for the first buffer on each CPU and increases by one each time the buffer is replaced. |
| 40 | 24 | -- | `reserved1` | Reserved, zero. |

A consumer MUST verify `magic` and `version` before trusting any other
field in the mapping.

A consumer MAY cache `magic`, `version`, `cpu_id`, `capacity`, and
`data_offset` for the lifetime of the mapping; these do not change
once the buffer exists. A consumer MUST NOT cache `generation`: it
shares this cache line but is written when the buffer is superseded,
and re-reading it is how a consumer learns that it must re-attach.

### Bytes 64–127: positions

| Offset | Size | Type | Field | Description |
|---|---|---|---|---|
| 64 | 8 | `u64` | `write_pos` | Monotonically increasing byte offset at which the next event will be written. Never wraps. |
| 72 | 8 | `u64` | `tail_pos` | Byte offset of the oldest surviving event. Advanced by KMES as events are overwritten. |
| 80 | 48 | -- | `reserved2` | Reserved, zero. |

Both are absolute byte offsets that increase without bound; the
corresponding data region offset is the value masked with
`capacity - 1`. A `u64` byte offset does not overflow in any practical
deployment — at a sustained gigabyte per second it would take over
five hundred years — and consumers MUST NOT implement wrap handling
for these counters.

### Bytes 128–191: notification

| Offset | Size | Type | Field | Description |
|---|---|---|---|---|
| 128 | 4 | `u32` | `futex_counter` | Incremented by KMES when it wakes sleeping consumers. |
| 132 | 60 | -- | `reserved3` | Reserved, zero. |

The counter is 32-bit because the Linux futex operates on 32-bit
integers, and it is incremented only when `need_wake` is set.

## Consumer metadata page

| Offset | Size | Type | Field | Description |
|---|---|---|---|---|
| 4096 | 1 | `u8` | `need_wake` | Set by a consumer that is about to sleep. Read by KMES after writing an event; any nonzero value counts as set. |
| 4097 | 4095 | -- | `reserved4` | Reserved. |

This page is shared by every consumer attached to the buffer. A
consumer MUST NOT store per-consumer state on it, and in particular
MUST NOT store its read position there.

Consumers MUST NOT write to any offset in this page other than
`need_wake`. Reserved bytes are reserved for future extension of this
contract.
