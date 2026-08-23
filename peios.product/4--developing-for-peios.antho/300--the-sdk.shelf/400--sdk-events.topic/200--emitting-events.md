---
title: Emitting events
type: how-to
description: Build a MessagePack payload and emit an event — singly, and in batches for high-rate producers.
related:
  - peios/sdk-events-api/event-h-events-kmes
  - peios/sdk-msgpack/msgpack-h-messagepack-codec
---

Emitting an event is two steps: build a MessagePack payload, then hand it and an event type to the kernel. This guide shows both; [`event.h`](~peios/sdk-events-api/event-h-events-kmes) and [`msgpack.h`](~peios/sdk-msgpack/msgpack-h-messagepack-codec) are the full references. Emitting requires `SeAuditPrivilege`.

## Build the payload

Use the [MessagePack writer](~peios/sdk-msgpack/msgpack-h-messagepack-codec#writer) to encode a single top-level value — typically a map of fields:

```c
peios_mp_writer *w = peios_mp_writer_new();

peios_mp_write_map(w, 2);                              /* {"user":…, "ok":…} */
peios_mp_write_str(w, "user", 4);  peios_mp_write_str(w, "alice", 5);
peios_mp_write_str(w, "ok", 2);    peios_mp_write_bool(w, true);

const void *payload;
ssize_t plen = peios_mp_writer_bytes(w, &payload);     /* validates as it borrows */
if (plen < 0) { /* EINVAL: malformed/under-filled — check peios_mp_writer_error */ }
```

`peios_mp_writer_bytes` validates that what you built is exactly one well-formed value, so a non-negative return means the payload is emit-ready. (Remember a map of `n` needs `2*n` values — one per key *and* value.)

## Emit it

```c
int rc = peios_event_emit("my.app.login", 12, payload, (uint32_t)plen);
peios_mp_writer_free(w);

if (rc != 0) {
    switch (errno) {
    case EPERM:  /* no SeAuditPrivilege */          break;
    case EINVAL: /* zero-length type or bad payload */ break;
    case ENOSPC: /* payload too large */            break;
    case EAGAIN: /* rate-limited — back off */      break;
    }
}
```

The event type is length-counted UTF-8 and must be non-zero length (`"my.app.login"` is 12 bytes — not NUL-terminated on the wire). On success the kernel stamps the trusted metadata (timestamp, sequence, identity GUIDs) and sets `origin_class = userspace`; you don't provide any of that.

### Validating untrusted payloads first

If a payload's shape comes from dynamic or untrusted input, validate it in userspace before emitting so you handle the failure on your terms rather than as an `EINVAL` from the kernel:

```c
if (peios_mp_validate(payload, plen, KMES_CONFIG_MAX_NESTING_DEPTH_DEFAULT) != 0) {
    /* reject it yourself */
}
```

The validator's acceptance matches the kernel's emit-time check at that depth bound.

## Emitting in batches

A high-rate producer should batch. [`peios_event_emit_batch`](~peios/sdk-events-api/event-h-events-kmes#batch-emit) emits many events in one call, so a single timestamp capture, identity capture, and consumer wake cover the whole set:

```c
struct peios_event_entry entries[3] = {
    { "my.app.a", 8, pa, pa_len },
    { "my.app.b", 8, pb, pb_len },
    { "my.app.c", 8, pc, pc_len },
};

uint32_t emitted = 0;
int rc = peios_event_emit_batch(entries, 3, &emitted);
if (rc != 0) {
    /* errno is from entries[emitted] — the first that failed.
       entries[0..emitted) were emitted; resume from `emitted`. */
}
```

`count` must be in `[1, KMES_BATCH_MAX_ENTRIES]`. On failure, `errno` is the reason the first failing entry failed and `emitted` tells you how many succeeded before it, so you know exactly where to resume. One caveat: rate-limiting is **all-or-nothing** for a batch — an `EAGAIN` emits *none* of it, so on `EAGAIN` back off and retry the whole batch.

## Next

- **[Consuming events](~peios/sdk-events/consuming-events)** — the other side of the pipe.
- **[`msgpack.h` reference](~peios/sdk-msgpack/msgpack-h-messagepack-codec)** — the full encoder, including containers, extensions, and raw splicing.
