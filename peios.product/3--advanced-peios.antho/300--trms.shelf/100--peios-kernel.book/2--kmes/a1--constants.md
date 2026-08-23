---
title: KMES Constants
description: Every KMES numeric constant and consumer-contract layout — syscall numbers and signatures, origin classes, ring bounds and entry layouts.
---

Every KMES-specific numeric constant. Layouts that form part of the
consumer contract — the event header, the producer and consumer
metadata pages, and the mapped region — are defined in the PSPK event
stream specification and are not repeated here.

## Syscall numbers

| Syscall | Number | Description |
|---|---|---|
| `kmes_emit` | 1090 | Emit a single event from userspace. |
| `kmes_attach` | 1091 | Attach as a consumer of one per-CPU ring buffer. |
| `kmes_emit_batch` | 1092 | Emit up to 256 events in one call. |

The PKM syscall range is 1090–1099; KMES uses the first three.

## Syscall signatures

```
long kmes_emit(const char __user *event_type, u16 event_type_len,
               const void __user *payload, u32 payload_len);

long kmes_emit_batch(const struct kmes_emit_entry __user *entries,
                     u32 count, u32 __user *emitted_out);

long kmes_attach(u32 cpu_id, u64 __user *capacity);
```

| Syscall | Parameter | Type | Description |
|---|---|---|---|
| `kmes_emit` | `event_type` | `const char *` | Event type string. |
| | `event_type_len` | `u16` | Its length in bytes. |
| | `payload` | `const void *` | MessagePack payload. |
| | `payload_len` | `u32` | Its length in bytes. |
| `kmes_emit_batch` | `entries` | `struct kmes_emit_entry __user *` | Array of event descriptors. |
| | `count` | `u32` | Number of entries, 1 to 256. |
| | `emitted_out` | `u32 __user *` | Receives the number of events emitted. |
| `kmes_attach` | `cpu_id` | `u32` | Logical CPU index, in `[0, num_cpus)`. |
| | `capacity` | `u64 __user *` | Receives the ring buffer capacity in bytes. |

`kmes_emit` and `kmes_emit_batch` return 0 on success; `kmes_attach`
returns a file descriptor. All three return -1 and set errno on
failure.

## Origin class values

| Value | Origin |
|---|---|
| 0 | Userspace (syscall) |
| 1 | KMES |
| 2 | KACS |
| 3 | LCS |

Values 4–255 are unassigned. KMES does not range-check the byte
written by kernel emitters.

## Ring buffer bounds

| Quantity | Value |
|---|---|
| Ring buffer format version | 1 |
| Ring buffer magic | `4B 4D 45 53 52 49 4E 47` (`KMESRING`) |
| Maximum event size, structural | 50% of ring capacity |
| Validator nesting stack depth | 256 |
| Self-configuration payload buffer | 768 bytes |
| Self-configuration audit intents per read | 4 |

## `kmes_emit_entry` layout (x86-64)

C ABI natural alignment; total 32 bytes. The pointer fields are
declared as `__u64` in the ABI header, which is equivalent on x86-64.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 8 | `pointer` | `event_type` |
| 8 | 2 | `u16` | `event_type_len` |
| 10 | 6 | -- | padding |
| 16 | 8 | `pointer` | `payload` |
| 24 | 4 | `u32` | `payload_len` |
| 28 | 4 | -- | padding |

Maximum entries per `kmes_emit_batch` call: 256.

## Configuration keys

Registry path `Machine\System\KMES\`.

| Key | Type | Default | Valid range |
|---|---|---|---|
| `BufferCapacity` | `REG_QWORD` | 4194304 (4 MB) | 65536–268435456 (64 KB–256 MB), power of two |
| `MaxEventSize` | `REG_DWORD` | 65536 (64 KB) | 1024–4194304 (1 KB–4 MB) |
| `MaxNestingDepth` | `REG_DWORD` | 32 | 4–256 |
| `MaxEmitRatePerProcess` | `REG_DWORD` | 10000 | 100–1000000 |

`MaxEventSize`, `MaxNestingDepth`, and `MaxEmitRatePerProcess` apply
only to syscall emitters. The registry type codes are LCS's:
`REG_DWORD` is 4 and `REG_QWORD` is 11.

## Privilege requirements

Bit indexes and masks are in the KACS privilege catalogue; KMES uses
these standalone gates.

| Operation | Required privilege |
|---|---|
| `kmes_emit`, `kmes_emit_batch` | SeAuditPrivilege |
| Rate-limit exemption on both | SeTcbPrivilege |
| `kmes_attach` | SeSecurityPrivilege |

## Error codes

### `kmes_emit`

| Errno | Condition |
|---|---|
| `EPERM` | SeAuditPrivilege not held or not enabled, or recording its used state failed. |
| `EAGAIN` | Per-process rate limit exceeded. |
| `EINVAL` | Zero event type length, event type not valid UTF-8, declared size arithmetic overflowed, payload not valid msgpack, or nesting depth over `MaxNestingDepth`. |
| `EFAULT` | Event type or payload pointer inaccessible. |
| `ENOSPC` | Event exceeds `MaxEventSize` or 50% of ring capacity. |
| `ENOMEM` | Staging buffer allocation failed, or KMES not initialised. |

### `kmes_emit_batch`

| Errno | Condition |
|---|---|
| `EPERM` | As `kmes_emit`. |
| `EAGAIN` | Fewer than `count` tokens available. |
| `EINVAL` | `count` is 0 or over 256, or the failing entry hit one of `kmes_emit`'s `EINVAL` conditions. |
| `EFAULT` | `emitted_out`, the entry array, or the failing entry's type or payload pointer inaccessible. |
| `ENOSPC` | The failing entry exceeds `MaxEventSize` or 50% of ring capacity. |
| `ENOMEM` | Kernel allocation failed, or KMES not initialised. |

### `kmes_attach`

| Errno | Condition |
|---|---|
| `EPERM` | SeSecurityPrivilege not held or not enabled, or recording its used state failed. |
| `EINVAL` | `cpu_id` at or beyond the ring count, or its slot holds no live ring. |
| `EFAULT` | `capacity` pointer inaccessible. |
| `ENOMEM` | Kernel allocation failed, or KMES not initialised. |
