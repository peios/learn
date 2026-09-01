---
title: KMES ABI Notes
description: What the KMES ABI tables cannot say for themselves — what each syscall parameter means, the privileges each requires, the error vocabulary, the implementation bounds outside the header, and the build configuration.
---

§2.A is generated from `pkm/uapi/pkm/kmes.h` and holds only what a
compiler can measure. This appendix holds the rest.

The split is structural rather than editorial. `gen-kmes-abi.py`
overwrites §2.A wholesale on every run, so anything written there is
lost the next time the ABI changes.

Layouts that form part of the consumer contract — the event header,
the producer and consumer metadata pages, and the mapped region — are
specified normatively in the PSPK event stream specification. §2.A
gives their offsets as the header defines them; the specification
governs.

## Syscall parameters

| Syscall | Parameter | Type | Meaning |
|---|---|---|---|
| `kmes_emit` | `event_type` | `const char *` | Event type string. |
| | `event_type_len` | `u16` | Its length in bytes. |
| | `payload` | `const void *` | MessagePack payload. |
| | `payload_len` | `u32` | Its length in bytes. |
| `kmes_emit_batch` | `entries` | `struct kmes_emit_entry *` | Array of event descriptors. |
| | `count` | `u32` | Number of entries, 1 to `KMES_BATCH_MAX_ENTRIES`. |
| | `emitted_out` | `u32 *` | Receives the number of events emitted. |
| `kmes_attach` | `cpu_id` | `unsigned int` | Ring slot index, or `KMES_ATTACH_QUERY_SLOTS` to query the slot count. |
| | `capacity` | `u64 *` | Receives the ring buffer capacity in bytes. |

`kmes_emit` and `kmes_emit_batch` return 0 on success; `kmes_attach`
returns a file descriptor. All three return -1 and set errno on
failure.

The PKM syscall range is 1090–1099; KMES uses the first three.

## Privilege requirements [*syscalls.privileges-by-name]

`kmes.h` gives these as bit masks so it can stand alone. The names
belong to the KACS privilege catalogue, and the bit index is what the
two agree on.

| Operation | Required privilege | Bit |
|---|---|---|
| `kmes_emit`, `kmes_emit_batch` | SeAuditPrivilege | 21 |
| Rate-limit exemption on both | SeTcbPrivilege | 7 |
| `kmes_attach` | SeSecurityPrivilege | 8 |

Holding a privilege is not enough: it must be *enabled*, and KMES marks
it used before proceeding. A failure to record the used state is itself
an `EPERM`, because an unrecorded privilege use is an audit gap. [*syscalls.privilege-enabled-and-recorded]

SeTcbPrivilege is checked but not required — an emitter that holds it
enabled is exempt from the per-process rate limit, and one that does not
is throttled.

## Implementation bounds

These are properties of the implementation rather than of the ABI, so
they are not in `kmes.h` and a program must not compile against them.
They bound what the interface will accept.

| Quantity | Value | Where |
|---|---|---|
| Maximum event size, structural | 50% of ring capacity | `kmes/kmes.c` |
| MessagePack validator nesting stack | 256 | `kmes/kmes_validate.rs` |
| Self-configuration payload buffer | 768 bytes | `kmes/kmes.c` |
| Self-configuration audit intents per read | 4 | `kmes/kmes.h` |
| Self-configuration parameter name | 64 bytes | `kmes/kmes.h` |

The structural 50% bound is independent of `MaxEventSize` and applies to
kernel emitters too. An event may satisfy the configured maximum and
still be refused because the ring is small.

The validator's 256-frame stack is why `MaxNestingDepth` has a maximum of
256. The two bounds are enforced independently: the configuration range
check refuses a larger value at apply time, and the validator refuses
every event outright if it is somehow handed one, rather than silently
accepting nesting it cannot track.

## Configuration keys

Registry path `Machine\System\KMES\`. The type codes, defaults and
ranges are in §2.A; what each key does is here.

| Key | Effect |
|---|---|
| `BufferCapacity` | Per-CPU ring size in bytes. Must be a power of two. Changing it swaps every ring; see §2.6. |
| `MaxEventSize` | Largest event a syscall emitter may produce. |
| `MaxNestingDepth` | Deepest MessagePack container nesting the validator will accept. |
| `MaxEmitRatePerProcess` | Token-bucket rate, events per second, per process. |

`MaxEventSize`, `MaxNestingDepth` and `MaxEmitRatePerProcess` apply only
to syscall emitters. A kernel emitter is not rate-limited and its payload
is not parsed as MessagePack, but it is still checked structurally —
non-empty type string within `PKM_KMES_MAX_KERNEL_TYPE_LEN`, a payload
pointer if the length is non-zero, no size arithmetic overflow, and the
50% bound. A kernel event that fails is dropped with
`KMES_DROP_VALIDATE`, not emitted.

A key that is missing, of the wrong type, or out of range does not fail
the read: the previous value is retained and the disagreement is
recorded as an audit intent. At most four such intents are carried out
of one read, so a configuration with five bad keys reports four.

## Error codes

### `kmes_emit` [*emit.errors]

| Errno | Condition |
|---|---|
| `EPERM` | SeAuditPrivilege not held or not enabled, or recording its used state failed. |
| `EAGAIN` | Per-process rate limit exceeded. |
| `EINVAL` | Zero event type length, event type not valid UTF-8, declared size arithmetic overflowed, payload not valid msgpack, or nesting depth over `MaxNestingDepth`. |
| `EFAULT` | Event type or payload pointer inaccessible. |
| `ENOSPC` | Event exceeds `MaxEventSize` or 50% of ring capacity. |
| `ENOMEM` | Staging buffer allocation failed, or KMES not initialised. |

### `kmes_emit_batch` [*batch.errors]

| Errno | Condition |
|---|---|
| `EPERM` | As `kmes_emit`. |
| `EAGAIN` | Fewer than `count` tokens available. |
| `EINVAL` | `count` is 0 or over `KMES_BATCH_MAX_ENTRIES`, or the failing entry hit one of `kmes_emit`'s `EINVAL` conditions. |
| `EFAULT` | `emitted_out`, the entry array, or the failing entry's type or payload pointer inaccessible. |
| `ENOSPC` | The failing entry exceeds `MaxEventSize` or 50% of ring capacity. |
| `ENOMEM` | Kernel allocation failed, or KMES not initialised. |

### `kmes_attach` [*attach.errors]

| Errno | Condition |
|---|---|
| `EPERM` | SeSecurityPrivilege not held or not enabled, or recording its used state failed. |
| `EINVAL` | `cpu_id` at or beyond the ring array size, or its slot holds no live ring. |
| `EFAULT` | `capacity` pointer inaccessible. |
| `ENOMEM` | Kernel allocation failed, or KMES not initialised. |

A `KMES_ATTACH_QUERY_SLOTS` call takes the same `EPERM`, `EFAULT` and
`ENOMEM` conditions and cannot return `EINVAL`. [*attach.query-slots-errors]

The ring array is sized by `nr_cpu_ids`, not by the number of rings
allocated. On a machine with a sparse possible-CPU mask the two differ,
and a slot inside the array with no live ring returns `EINVAL` exactly
as an index beyond the array does. A consumer therefore enumerates
against the slot count from `KMES_ATTACH_QUERY_SLOTS` and skips the
`EINVAL` slots rather than stopping at the first one; see §2.4.

## Build configuration [*build.config-security-pkm]

KMES is built by `CONFIG_SECURITY_PKM`, a boolean option, so it is
linked into `vmlinux` rather than loaded. `CONFIG_RUST=y` is required:
the MessagePack validator is Rust. The whole subsystem is staged into
the kernel tree as `security/pkm/kmes` by `pkm/kernel/stage-sources.sh`,
which also stages `<trace/events/kmes.h>` so the tracepoints resolve.

The three syscall numbers are added to the syscall table by
`kernel/patches/arch/syscall-table-pkm.patch`, which patches both
`arch/x86/entry/syscalls/syscall_64.tbl` and the copy of it that ships
under `tools/perf/`. They are registered `common`, so they are reachable
from the x32 ABI as well as from x86-64. [*build.syscalls-registered-common]

`CONFIG_SECURITY_PKM_KUNIT` compiles in the in-kernel test harness.
