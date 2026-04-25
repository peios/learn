---
title: Protocol
---

The Registry Source Interface (RSI) is the binary protocol and
contract between LCS and its backing stores. This section defines
the communication channel, message format, and registration
lifecycle.

## Communication channel

Sources communicate with LCS via the `/dev/pkm_registry` character
device. The protocol is binary and multiplexed.

**Binary.** Kernel code produces and consumes fixed-layout messages.
No text parsing. Each message has a fixed header followed by
operation-specific fields.

**Multiplexed.** LCS sends concurrent requests tagged with unique
request IDs (uint64, monotonic per source connection). The source
MAY process requests in any order and sends responses tagged with
the matching request ID. LCS matches responses to waiting kernel
threads. The maximum number of simultaneously in-flight requests
per source is bounded by MaxConcurrentRSIRequests (default 256).
When the limit is reached, new operations block until an in-flight
request completes or times out.

## Message framing

**Request header (22 bytes):**

```
┌───────────┬──────────────┬──────────┬──────────┬─────────────┐
│ total_len │ request_id   │ op_code  │ txn_id   │ payload     │
│ uint32    │ uint64       │ uint16   │ uint64   │ (variable)  │
└───────────┴──────────────┴──────────┴──────────┴─────────────┘
```

**Response header (14 bytes):**

```
┌───────────┬──────────────┬──────────┬─────────────┐
│ total_len │ request_id   │ op_code  │ payload     │
│ uint32    │ uint64       │ uint16   │ (variable)  │
└───────────┴──────────────┴──────────┴─────────────┘
```

Responses do not include txn_id.

- **total_len:** Total message size in bytes, including the header.
  Allows the reader to frame messages on the byte stream.
- **request_id:** Matches responses to requests. The source copies
  the request_id from the request into its response.
- **op_code:** The RSI operation. Responses use the same op_code
  as the request with the high bit set (op_code | 0x8000).
- **txn_id:** Transaction ID for operations within a transaction.
  Zero means no transaction. When non-zero, the source processes
  the operation within the specified transaction's context
  (read-your-own-writes isolation). Present on all requests;
  responses do not include txn_id.
- **payload:** Operation-specific fields. Fixed-size fields first
  (GUIDs, integers, flags), followed by variable-length data
  (names, SD bytes, value data) with uint32 length prefixes.

All multi-byte integers are little-endian.

## Response status

Every response includes a status code (uint32) as the first field
of the payload. Zero indicates success. Non-zero indicates an
error from the defined error vocabulary (see Source Errors below).

## Registration

Before entering the request loop, a source registers its hives:

1. Source opens `/dev/pkm_registry`. The char device's open()
   handler checks SeTcbPrivilege on the calling thread's token.
   If the privilege is not held, open() returns EPERM. This
   prevents unprivileged processes from obtaining an fd to the
   device at all.
2. Source issues REG_SRC_REGISTER ioctl with:
   - Hive names (string array)
   - Root GUID for each hive
   - Max sequence number (highest write sequence persisted in this
     source's storage -- LCS uses this to initialise the global
     counter above any existing value)
   - Flags per hive: PRIVATE (0x01) for private hives
   - Scope GUID per hive (only if PRIVATE flag set -- the scope
     identifier that threads must carry in their credentials to
     see this hive)
3. LCS validates:
   - No hive name collisions with other sources' global hives.
   - For private hives: no collisions with other private hives
     sharing the same scope GUID.
   - SeTcbPrivilege is held by the registering process.
4. On success, the source enters the request loop: read() for
   requests, write() for responses.

The maximum number of hives per source is bounded by
MaxHivesPerSource (default 64). The maximum number of
concurrently registered sources is bounded by
MaxRegisteredSources (default 32).

**Registration errors:**

| Errno | Condition |
|---|---|
| EPERM | Caller does not hold SeTcbPrivilege. |
| EEXIST | A hive name is already registered by another source. |
| EINVAL | Malformed arguments (zero hive count, invalid hive name). |
| ENOSPC | MaxRegisteredSources or MaxHivesPerSource exceeded. |

**Layer awareness.** Sources do not need the layer table. Sources
store entries tagged with layer name strings and return all entries
on request. Layer resolution (precedence, enabled state, tombstone
evaluation) is performed entirely by LCS. A source that has never
seen a particular layer name simply stores entries tagged with it
when LCS sends writes. The layer table is a kernel-side concern.

## Source lifecycle

```
Closed ──register──► Active ──disconnect/crash──► Down
                       ▲                            │
                       └────────re-register─────────┘
```

- **Closed → Active:** Source opens `/dev/pkm_registry`, registers
  hives. LCS routes traffic to it.
- **Active → Down:** Source disconnects (fd close) or crashes. LCS
  marks hives as unavailable. Active key fds remain valid but
  operations requiring source round-trips return EIO. Watches
  remain armed.
- **Down → Active:** Source re-registers the same hive names. LCS
  resumes routing. OVERFLOW delivered to all affected watches.
