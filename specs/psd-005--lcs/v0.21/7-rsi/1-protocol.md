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

### File-operation semantics

The `/dev/pkm_registry` fd is message-oriented. The total_len field
frames messages, but successful Linux I/O calls never split or join
RSI messages.

**read().** One successful read() returns exactly one complete RSI
request. If no request is queued, blocking read() waits until a
request is available or the source fd is closing. If O_NONBLOCK is
set and no request is queued, read() returns EAGAIN. If the caller's
buffer is too small for the next queued request, read() returns
EMSGSIZE and does not consume the request.

**write().** One successful write() submits exactly one complete RSI
response. The user buffer length MUST equal the response header's
total_len and MUST be at least the response header size. Short
responses, trailing bytes beyond total_len, unknown request IDs,
duplicate responses, response opcodes that do not match the original
request, and responses for another source connection fail with
EINVAL. No partial response is accepted and successful writes are not
short.

Malformed framing or protocol corruption that prevents reliable
message parsing is treated as malformed protocol: LCS tears down the
connection and marks the source Down. Ordinary per-response semantic
errors are reported through RSI status codes and do not tear down the
source.

**poll()/epoll().** The source fd reports readable when at least one
complete request is queued. It reports writable while the source slot
is Active and the fd may submit responses. It reports POLLHUP |
POLLERR when the source slot is Down or the fd is closing.

MaxConcurrentRSIRequests limits requests dispatched to the source and
awaiting response. Kernel callers waiting for an in-flight slot are
not themselves dispatched requests and do not have request IDs yet.

Request IDs are monotonic per source connection and are never reused
while that connection is live, including after request timeout. A
timed-out request remains an in-flight request until a matching
response arrives or the source connection is torn down.

RequestTimeoutMs starts when a kernel operation first attempts to
reserve an in-flight RSI slot, after local validation and access
checks. The same deadline covers waiting for a slot, waiting for the
source to read the queued request, and waiting for the response. If
the deadline expires before a slot is reserved, the caller receives
ETIMEDOUT and no RSI request is sent. If the deadline expires after
dispatch, the caller receives ETIMEDOUT and late-response handling
follows §10.1.

### Timed-out request records

For every dispatched request, LCS keeps a request record until a
matching response is processed or the source connection is torn down.
The record includes at least the request ID, op code, transaction ID,
assigned sequence numbers, affected-object metadata, and any mutation
log needed to perform kernel-side effects if the source later reports
success.

When RequestTimeoutMs expires after dispatch, LCS detaches the
waiting caller from the request record and returns ETIMEDOUT to that
caller. The request record remains in the source's in-flight table
and continues to count against MaxConcurrentRSIRequests. A source
that accumulates timed-out requests can therefore exhaust its
in-flight slots until it sends responses or disconnects.

A late response for a retained request is validated exactly like an
on-time response. A late response for an unknown request ID, a
duplicate response, or any response whose request record has already
been released is malformed protocol; LCS tears down the source
connection and marks the source Down. This avoids processing a
mutation whose kernel-side metadata has been lost.

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
  the operation within the specified transaction's context. A
  read-write transaction provides read-your-own-writes isolation; a
  read-only transaction provides point-in-time snapshot isolation.
  Present on all requests; responses do not include txn_id.
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

### Source slots and re-registration

Successful registration creates a source slot. A source slot is the
kernel object that owns one source connection and the hive set
registered on that connection.

Each registered hive has a stable hive identity:

- the case-folded hive name
- visibility: global or private
- the private scope GUID, for private hives
- the hive root GUID

Active and Down source slots both reserve their hive identities.
Collision checks include Down source slots. A source crash or fd
close marks the slot Down; it does not unregister or retire the
hive identities.

A new process may resume a Down source slot if it holds
SeTcbPrivilege and registers exactly the same hive set as the Down
slot. For every hive, the case-folded hive name, visibility, scope
GUID, and root GUID must match the previous registration. Partial
re-registration is rejected.

If a registration attempts to claim a hive identity reserved by a
Down source slot but does not exactly match the complete Down slot,
registration fails. If the only mismatch is stale identity data such
as a different root GUID for an otherwise matching hive, registration
fails with ESTALE. Other malformed or partial resume attempts fail
with EINVAL or EEXIST according to the collision being reported.

LCS authenticates a replacement source by SeTcbPrivilege, not by
process ID continuity. Process identity cannot survive crash/restart.

New hives must be registered through a new source slot. They cannot
be added by mutating a Down source slot during resume. v0.21 defines
no implicit retirement or unreservation of Down source slots; any
future administrative retirement operation must be explicit.

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
| EOVERFLOW | Max sequence number is uint64 max, so LCS cannot advance the global sequence counter above it. |
| ESTALE | Registration attempted to resume a Down source slot with stale or mismatched hive identity. |

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
  marks hives as unavailable. The source slot and its hive identities
  remain reserved. Active key fds remain valid but operations
  requiring source round-trips return EIO. Watches remain armed.
- **Down → Active:** A source process resumes the Down source slot
  by registering the exact same hive set and root GUIDs. LCS resumes
  routing. OVERFLOW delivered to all affected watches.
