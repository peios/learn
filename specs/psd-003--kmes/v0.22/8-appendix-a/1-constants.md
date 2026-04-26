---
title: Constants
---

All numeric constants used in the KMES interface. An independent implementer can derive all magic numbers from this page.

## Syscall numbers

| Syscall | Number | Description |
|---|---|---|
| kmes_emit | 1090 | Emit a single event from userspace. |
| kmes_attach | 1091 | Attach as a consumer of a single per-CPU ring buffer. |
| kmes_emit_batch | 1092 | Emit multiple events from userspace as a single operation. Maximum 256 events per call. |

## Origin class values

| Value | Origin |
|---|---|
| 0 | Userspace (syscall) |
| 1 | KMES |
| 2 | KACS |
| 3 | LCS |

Values 4--255 are reserved for future kernel subsystems.

## Event header layout

Packed, no padding. All multi-byte integers little-endian. GUIDs in Microsoft GUID binary format.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 4 | `u32` | `event_size` |
| 4 | 4 | `u32` | `header_size` |
| 8 | 8 | `u64` | `timestamp` |
| 16 | 8 | `u64` | `sequence` |
| 24 | 2 | `u16` | `cpu_id` |
| 26 | 1 | `u8` | `origin_class` |
| 27 | 16 | `GUID` | `effective_token_guid` |
| 43 | 16 | `GUID` | `true_token_guid` |
| 59 | 16 | `GUID` | `process_guid` |
| 75 | 2 | `u16` | `type_len` |
| 77 | var | `[u8]` | `type` |

Header size: `77 + type_len` bytes. All fields before `type_len` are at fixed offsets. Payload begins at `header_size` from event start.

## Producer metadata page layout (offset 0, read-only)

One producer metadata page (4096 bytes) per CPU. Cache-line-aligned fields.

### Cache line 0 -- static fields (bytes 0--63)

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 8 | `[u8; 8]` | `magic` |
| 8 | 4 | `u32` | `version` |
| 12 | 2 | `u16` | `cpu_id` |
| 14 | 2 | `u16` | `reserved0` |
| 16 | 8 | `u64` | `capacity` |
| 24 | 8 | `u64` | `data_offset` |
| 32 | 8 | `u64` | `generation` |
| 40 | 24 | -- | `reserved1` |

### Cache line 1 -- producer fields (bytes 64--127)

| Offset | Size | Type | Field |
|---|---|---|---|
| 64 | 8 | `u64` | `write_pos` |
| 72 | 8 | `u64` | `tail_pos` |
| 80 | 48 | -- | `reserved2` |

### Cache line 2 -- notification fields (bytes 128--191)

| Offset | Size | Type | Field |
|---|---|---|---|
| 128 | 4 | `u32` | `futex_counter` |
| 132 | 60 | -- | `reserved3` |

## Consumer metadata page layout (offset 4096, read-write)

| Offset | Size | Type | Field |
|---|---|---|---|
| 4096 | 1 | `u8` | `need_wake` |
| 4097 | 4095 | -- | `reserved4` |

## Ring buffer magic

```
0x4B 0x4D 0x45 0x53 0x52 0x49 0x4E 0x47
 K    M    E    S    R    I    N    G
```

Compared byte-by-byte, not as an integer. Endianness-independent.

## Ring buffer version

v0.22 uses ring buffer format version 1. The ring buffer metadata page layout is unchanged from v0.20. The event header format has changed (identity GUID fields added), but events are self-describing via `header_size` -- consumers that use `header_size` to locate the payload handle the larger header without modification.

## Mapped region layout

Per-CPU mapping returned by `mmap()` on a `kmes_attach` file descriptor:

| Offset | Size | Description |
|---|---|---|
| 0 | 4096 | Producer metadata page (read-only) |
| 4096 | 4096 | Consumer metadata page (read-write) |
| 8192 | 2 × capacity | Double-mapped data region (read-only) |

Total mapping size: `8192 + (2 × capacity)` bytes.

## Syscall error codes

### kmes_emit errors

| Errno | Condition |
|---|---|
| EPERM | Caller does not hold SeAuditPrivilege. |
| EAGAIN | Per-process rate limit exceeded. |
| EINVAL | Event type length is zero, or event type is not valid UTF-8, or payload is invalid msgpack, or payload nesting depth exceeds MaxNestingDepth. |
| EFAULT | Event type or payload pointer is inaccessible. |
| ENOSPC | Event exceeds MaxEventSize or 50% of per-CPU ring buffer capacity. |
| ENOMEM | Kernel memory allocation for staging buffer failed. |

### kmes_emit_batch errors

| Errno | Condition |
|---|---|
| EPERM | Caller does not hold SeAuditPrivilege. |
| EAGAIN | Per-process rate limit exceeded. |
| EINVAL | Count is 0 or exceeds 256, or failing entry has zero-length event type, or failing entry's event type is not valid UTF-8, or failing entry's payload is invalid msgpack or exceeds MaxNestingDepth. |
| EFAULT | Entry array, event type, or payload pointer is inaccessible. |
| ENOSPC | Failing entry exceeds MaxEventSize or 50% of per-CPU ring buffer capacity. |
| ENOMEM | Kernel memory allocation failed. |

### kmes_attach errors

| Errno | Condition |
|---|---|
| EPERM | Caller does not hold SeSecurityPrivilege. |
| EINVAL | `cpu_id` is greater than or equal to the number of CPUs. |
| EFAULT | `capacity` pointer is inaccessible. |
| ENOMEM | Kernel memory allocation failed. |

## kmes_emit_entry struct layout (x86-64)

C ABI natural alignment. Total size: 32 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 8 | `pointer` | `event_type` |
| 8 | 2 | `u16` | `event_type_len` |
| 10 | 6 | -- | padding |
| 16 | 8 | `pointer` | `payload` |
| 24 | 4 | `u32` | `payload_len` |
| 28 | 4 | -- | padding |

## Configuration keys

Registry path: `Machine\System\KMES\`

| Key | Type | Default | Valid range |
|---|---|---|---|
| BufferCapacity | REG_QWORD | 4194304 (4 MB) | 65536--268435456 (64 KB--256 MB), power of two |
| MaxEventSize | REG_DWORD | 65536 (64 KB) | 1024--4194304 (1 KB--4 MB) |
| MaxNestingDepth | REG_DWORD | 32 | 4--256 |
| MaxEmitRatePerProcess | REG_DWORD | 10000 | 100--1000000 |

## Privilege requirements

| Operation | Required privilege |
|---|---|
| Emit event from userspace (`kmes_emit`, `kmes_emit_batch`) | SeAuditPrivilege |
| Attach as consumer (`kmes_attach`) | SeSecurityPrivilege |
