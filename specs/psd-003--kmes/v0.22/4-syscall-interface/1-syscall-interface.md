---
title: Syscall Interface
---

## Overview

KMES exposes three syscalls in the PKM range (1090--1099):

- `kmes_emit` (1090) -- emit a single event from userspace.
- `kmes_attach` (1091) -- attach as a consumer and obtain per-CPU ring buffer file descriptors.
- `kmes_emit_batch` (1092) -- emit multiple events from userspace as a single operation.

All three syscalls use standard Linux error conventions: return -1 and set errno on failure.

## kmes_emit (1090)

Emits a single event into KMES from userspace. The origin class is set to 0 (userspace) unconditionally -- the caller cannot specify it. The event is written to the ring buffer of the CPU on which the calling thread is currently executing.

### Privilege requirement

The caller's effective token MUST hold SeAuditPrivilege. If the privilege is not held or not enabled, the syscall fails with EPERM.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `event_type` | `const char *` | Pointer to the event type string. |
| `event_type_len` | `u16` | Length of the event type string in bytes. |
| `payload` | `const void *` | Pointer to the msgpack-encoded payload. |
| `payload_len` | `u32` | Length of the payload in bytes. |

### Validation

KMES performs the following validation on every `kmes_emit` call, in order:

1. The caller MUST hold SeAuditPrivilege. Fails with EPERM.
2. If the caller does not hold SeTcbPrivilege, the per-process rate limit is checked using a token bucket algorithm. The bucket refills at `MaxEmitRatePerProcess` tokens per second and has a burst capacity equal to `MaxEmitRatePerProcess`. The bucket is created on the process's first emit call, initialized to full capacity. The bucket is destroyed when the process exits. If `MaxEmitRatePerProcess` changes at runtime, the bucket capacity and refill rate are updated immediately; the current token count is clamped to the new capacity if it exceeds it. If the bucket is empty, the syscall fails with EAGAIN. One token is consumed after the event is successfully written to the ring buffer. Validation failures do not consume a token. Callers holding SeTcbPrivilege are exempt from rate limiting. If KACS is not yet initialized and privilege checks cannot be performed, the syscall fails with EPERM (fail-closed).
3. `event_type_len` MUST be nonzero. Fails with EINVAL.
4. The event type and payload are copied from userspace into a kernel buffer. The event type MUST be valid UTF-8. Fails with EINVAL if the event type contains invalid UTF-8 byte sequences. If either pointer is inaccessible, fails with EFAULT. All subsequent validation and the ring buffer write operate on the kernel copy, not the original userspace memory. This prevents TOCTOU (time-of-check-time-of-use) attacks where userspace modifies the payload between validation and the ring buffer write.
5. The total event size (header + payload) MUST NOT exceed the configured maximum event size. Fails with ENOSPC.
6. The total event size MUST NOT exceed 50% of the per-CPU ring buffer capacity. Fails with ENOSPC.
7. The payload MUST be valid msgpack with nesting depth not exceeding the configured maximum. Fails with EINVAL.

Validation stops at the first failure. The error reflects the first check that failed.

### Preemption

Validation (steps 1--7) runs with preemption enabled. The userspace copy at step 4 may trigger page faults, and msgpack validation at step 7 may take microseconds for large payloads. Neither requires CPU affinity.

Preemption is disabled only for the ring buffer write: determining the current CPU, constructing the header (stamping timestamp, sequence number, cpu_id, and capturing identity GUIDs from KACS), writing the event, advancing `write_pos`, and checking `need_wake`. The three KACS GUID accessor calls add negligible overhead (each reads a field from an in-memory kernel structure with no allocation or sleeping). This keeps the non-preemptible window to a few hundred nanoseconds regardless of payload size. The `cpu_id` and identity GUIDs in the event header reflect the state at write time, not at syscall entry time.

### Behavior

On success, KMES writes the event to the current CPU's ring buffer and returns 0. The event is visible to consumers immediately.

If the ring buffer is full, KMES overwrites the oldest events. The syscall never blocks due to buffer pressure.

### Return

Returns 0 on success. Returns -1 and sets errno on failure.

### Errors

| Errno | Meaning |
|---|---|
| EPERM | Caller does not hold SeAuditPrivilege. |
| EAGAIN | Per-process rate limit exceeded. Caller SHOULD back off and retry. |
| EINVAL | Event type length is zero, or event type is not valid UTF-8, or payload is invalid msgpack, or payload nesting depth exceeds MaxNestingDepth. |
| EFAULT | Event type or payload pointer is inaccessible. |
| ENOSPC | Event exceeds MaxEventSize or 50% of per-CPU ring buffer capacity. |
| ENOMEM | Kernel memory allocation for the staging buffer failed. |

## kmes_emit_batch (1092)

Emits multiple events into KMES from userspace as a single operation. All events share a single timestamp and the overhead of privilege checking, notification, and the write_pos release barrier is incurred once for the batch rather than per event.

### Privilege requirement

The caller's effective token MUST hold SeAuditPrivilege. If the privilege is not held or not enabled, the syscall fails with EPERM.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `entries` | `struct kmes_emit_entry __user *` | Pointer to an array of event descriptors. |
| `count` | `u32` | Number of entries in the array. MUST be at least 1 and at most 256. The limit of 256 bounds the worst-case preemption-disabled window during the ring buffer write phase to approximately 50--100 microseconds for typical event sizes, while providing strong syscall overhead amortization. |

Each `kmes_emit_entry` uses C ABI natural alignment on the target architecture. On x86-64:

| Offset | Size | Type | Field | Description |
|---|---|---|---|---|
| 0 | 8 | `pointer` | `event_type` | Pointer to the event type string. |
| 8 | 2 | `u16` | `event_type_len` | Length of the event type string in bytes. |
| 10 | 6 | -- | padding | |
| 16 | 8 | `pointer` | `payload` | Pointer to the msgpack-encoded payload. |
| 24 | 4 | `u32` | `payload_len` | Length of the payload in bytes. |
| 28 | 4 | -- | padding | |

Total struct size: 32 bytes.

### Validation

1. The caller MUST hold SeAuditPrivilege. Fails with EPERM.
2. `count` MUST be between 1 and 256 inclusive. Fails with EINVAL.
3. If the caller does not hold SeTcbPrivilege, the per-process rate limit is checked using the same token bucket as `kmes_emit`. The bucket MUST have at least `count` tokens available. If not, the syscall fails with EAGAIN and no events are emitted. Step 3 MUST atomically reserve `count` tokens from the bucket to prevent concurrent threads from passing the rate check simultaneously. After all processing is complete, unused tokens for events that were not emitted (due to validation failure) are returned to the bucket. Only events actually emitted consume tokens (see Return). Callers holding SeTcbPrivilege are exempt from rate limiting. If KACS is not yet initialized, the syscall fails with EPERM.
4. The entry descriptor array is copied from userspace. Fails with EFAULT if inaccessible.
5. For each entry in order, starting from index 0: the event type and payload are copied from userspace into kernel memory. Each entry is validated using the same rules as `kmes_emit` (nonzero event type length, valid UTF-8 event type, total size within MaxEventSize, total size within 50% of buffer capacity, valid msgpack within MaxNestingDepth). If any entry fails validation, processing stops. Events before the failing entry that passed validation are emitted. The failing entry and all subsequent entries are not processed.

### Preemption

The userspace copies and msgpack validation run with preemption enabled. Preemption is disabled only for the ring buffer writes, the single write_pos release barrier, and the need_wake check.

### Behavior

All successfully validated events share a single wall clock timestamp and a single set of identity GUIDs, captured once at the start of the ring buffer write phase. Each event receives its own sequence number. The origin class is set to 0 (userspace) for all events.

If the ring buffer is full, KMES overwrites the oldest events. The syscall never blocks due to buffer pressure.

### Return

Returns the number of events successfully emitted (0 to `count`). If all events are emitted, the return value equals `count`. If validation fails on entry N, the return value is N (events 0 through N-1 were emitted) and errno is set to indicate why entry N failed. Events that fail validation (entry N and all subsequent entries) do not consume sequence numbers -- they never enter the ring buffer write phase. Only the N events actually emitted are charged against the rate limit, not the full `count`.

Returns -1 and sets errno for errors that prevent any processing (EPERM, EAGAIN, EINVAL on count, EFAULT on the entry array itself, ENOMEM).

Per-entry validation failures (EINVAL, EFAULT on a per-entry pointer, ENOSPC) return N (number of events emitted before the failure), not -1. EFAULT on the entry array itself (step 4) returns -1 because no entries could be read.

### Errors

| Errno | Meaning |
|---|---|
| EPERM | Caller does not hold SeAuditPrivilege. |
| EAGAIN | Per-process rate limit exceeded. Caller SHOULD back off and retry. |
| EINVAL | `count` is 0 or exceeds 256, or the failing entry has a zero-length event type, or the failing entry's event type is not valid UTF-8, or the failing entry's payload is invalid msgpack or exceeds MaxNestingDepth. |
| EFAULT | Entry array, event type, or payload pointer is inaccessible. |
| ENOSPC | The failing entry exceeds MaxEventSize or 50% of per-CPU ring buffer capacity. |
| ENOMEM | Kernel memory allocation failed. |

## kmes_attach (1091)

Attaches the caller as a consumer of the KMES ring buffers. Returns one file descriptor per CPU, each independently mappable.

### Privilege requirement

The caller's effective token MUST hold SeSecurityPrivilege. If the privilege is not held or not enabled, the syscall fails with EPERM.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `fds` | `int __user *` | Pointer to a caller-provided buffer for the returned file descriptors. |
| `count` | `int __user *` | Pointer to an integer. On entry, the size of the `fds` buffer (number of int-sized slots). On return, the number of CPUs (and thus the number of file descriptors written). |
| `capacity` | `u64 __user *` | Pointer to a u64. On return, the per-CPU ring buffer capacity in bytes. The consumer uses this to compute the mmap size: `8192 + 2 * capacity`. |

### Behavior

KMES writes one file descriptor per CPU into the `fds` buffer, in CPU order (index 0 = CPU 0, index 1 = CPU 1, etc.). The number of CPUs is written to `*count`. The current per-CPU ring buffer capacity is written to `*capacity`.

If the buffer is too small (`*count` on entry is less than the number of CPUs), no file descriptors are created. `*count` is set to the required number and the syscall fails with ERANGE. The caller SHOULD retry with a sufficiently large buffer.

File descriptor creation is all-or-nothing. If allocation of any file descriptor fails (e.g., ENOMEM), all previously created file descriptors from this call are closed internally before the error is returned. The caller receives either all N file descriptors or none.

Each file descriptor independently supports:

- `mmap()` -- maps that CPU's ring buffer into the caller's address space. The mapped region layout is defined in §5.1.5.
- `close()` -- releases the file descriptor. The mapping becomes invalid.

The mapped region is split into read-only and read-write sections. The producer metadata page and the data region are mapped read-only -- no privilege, capability, or token grants write access to these regions from userspace. Only KMES writes event data and producer metadata. The consumer metadata page is mapped read-write for consumer notification state (`need_wake`). KMES treats consumer metadata as advisory and validates all values read from it.

Multiple consumers MAY attach simultaneously. Each consumer maintains its own read position per buffer independently.

### Notification

Each per-CPU ring buffer has its own futex counter (`u32`) in its metadata page. When KMES writes an event to a CPU's ring buffer and `need_wake` is set, it increments that buffer's futex counter and issues a `futex_wake` that wakes all waiting threads. This ensures that multiple consumers attached to the same buffer are all woken when events arrive.

This allows consumers to dedicate one thread per CPU buffer, each sleeping independently on its own futex. Under sustained load, consumer threads remain in the drain loop, `need_wake` stays 0, and KMES skips all notification overhead.

### Return

Returns 0 on success. Returns -1 and sets errno on failure.

### Errors

| Errno | Meaning |
|---|---|
| EPERM | Caller does not hold SeSecurityPrivilege. |
| ERANGE | The `fds` buffer is too small. `*count` is set to the required number of slots. |
| EFAULT | `fds`, `count`, or `capacity` points to inaccessible memory. |
| ENOMEM | Kernel memory allocation failed. |
