---
title: Emitting events
description: Emitting a single event or a batch — the type string, the payload, and what the call validates.
---

```c
int peios_event_emit(const char *event_type, uint16_t event_type_len,
                     const void *payload, uint32_t payload_len);
```

Emits a single event. `event_type` is a **length-counted UTF-8** event kind such as `"my.app.login"` — *not* NUL-terminated, and its length must be non-zero. `payload` is `payload_len` bytes of MessagePack (one well-formed value). The kernel validates the payload (one well-formed MessagePack value within the configured size and nesting limits) and stamps `origin_class = userspace`. Returns `0`, or `-1` with `errno`:

| errno | Cause |
|---|---|
| `EPERM` | No `SeAuditPrivilege`. |
| `EINVAL` | Zero-length type, or a malformed payload. |
| `ENOSPC` | Payload exceeds the size caps. |
| `EAGAIN` | Rate-limited. |
| `EFAULT` | Bad pointer. |

Since the kernel's payload check matches [`peios_mp_validate`](~peios/sdk-msgpack/msgpack-h-messagepack-codec#validator), you can validate in userspace first and turn a would-be `EINVAL` into a check you control.

```c
/* Build a payload, then emit. */
peios_mp_writer *w = peios_mp_writer_new();
peios_mp_write_map(w, 1);
peios_mp_write_str(w, "user", 4); peios_mp_write_str(w, "alice", 5);

const void *buf; ssize_t n = peios_mp_writer_bytes(w, &buf);
if (n >= 0)
    peios_event_emit("my.app.login", 12, buf, (uint32_t)n);
peios_mp_writer_free(w);
```

### Batch emit

```c
struct peios_event_entry {
    const char *event_type;      /* length-counted UTF-8; not NUL-terminated */
    uint16_t    event_type_len;
    const void *payload;         /* MessagePack bytes */
    uint32_t    payload_len;
};

int peios_event_emit_batch(const struct peios_event_entry *entries,
                           uint32_t count, uint32_t *emitted_out);
```

`peios_event_emit_batch` emits several events in one call, **amortising the per-call overhead** — a single timestamp capture, identity capture, and consumer wake cover the whole batch. `count` is in `[1, KMES_BATCH_MAX_ENTRIES]`. It returns `0` if all `count` were emitted, or `-1` with the `errno` **of the first entry that failed**, with `*emitted_out` (if non-`NULL`) set to how many entries preceded the failure — so you know exactly where to resume. Rate-limiting is all-or-nothing here: an `EAGAIN` emits **none** of the batch.
