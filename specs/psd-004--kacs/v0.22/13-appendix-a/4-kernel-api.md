---
title: Kernel-Internal API
---

This appendix defines the kernel-internal API functions that KACS exports for
use by other kernel subsystems. These are NOT syscalls — they are C functions
callable only from kernel context. The primary consumer is KMES, which calls
these functions during event emission to stamp events with identity information.

## Constraints

All functions in this API MUST be safe to call with preemption disabled. This
means:

- No sleeping (no allocations, no mutex acquisition, no waiting).
- No RCU grace period waits.
- Constant-time field reads only (pointer chases to immutable data).

These constraints exist because KMES emits events from contexts where
preemption is disabled, including interrupt handlers and scheduler paths.

All functions return a null UUID (all zero bytes) when:

- KACS is not yet initialized (early boot before LSM registration).
- The current context has no PSB (kernel threads without KACS state).
- The relevant token or PSB pointer is NULL.

## Identity accessors

### kacs_effective_token_guid

```c
kacs_uuid_t kacs_effective_token_guid(void);
```

Returns the `token_guid` of the current thread's effective token. If the thread
is impersonating, this is the impersonation token's GUID. Otherwise, it is the
process's primary token's GUID.

This is the GUID that should appear in most KMES events — it identifies the
security context under which the operation is executing.

### kacs_primary_token_guid

```c
kacs_uuid_t kacs_primary_token_guid(void);
```

Returns the `token_guid` of the current thread's primary (process) token,
regardless of impersonation state. Always returns the same GUID for all threads
in the same process (unless the process's primary token has been replaced via
external token replacement).

Useful when an event needs to record the true service identity separately from
the impersonated client identity.

### kacs_process_guid

```c
kacs_uuid_t kacs_process_guid(void);
```

Returns the `process_guid` from the current thread's PSB. The Process GUID is
assigned at fork and is immutable for the lifetime of the process.

## Type

`kacs_uuid_t` is an opaque 16-byte value. The in-memory representation is
implementation-defined. Comparison is bytewise equality. A null UUID is 16 zero
bytes.

Generated UUIDs are UUIDv4 per RFC 4122: 122 random bits with version (4) and
variant (RFC 4122) bits set. The kernel uses `get_random_bytes()` for
generation.
