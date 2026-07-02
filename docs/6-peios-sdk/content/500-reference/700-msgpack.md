---
title: msgpack.h — MessagePack codec
type: reference
description: Complete reference for <peios/msgpack.h> — the in-house MessagePack encoder, decoder, and validator that builds and parses KMES event payloads.
related:
  - peios-sdk/reference/event
  - peios-sdk/getting-started/library-conventions
---

`<peios/msgpack.h>` is a small, self-contained [MessagePack](https://msgpack.org) codec. It exists because KMES event payloads *are* MessagePack: the kernel only *structurally validates* a payload on emit — it does not build or interpret it — so userspace owns the encode and decode. This codec is that path, and its validator's acceptance is deliberately **matched to the kernel's emit-time check**, so a payload this codec produces and validates is guaranteed to be accepted by [`peios_event_emit`](~peios-sdk/reference/event#emitting-events).

You can use it as a general MessagePack codec, but its reason for being is [events](~peios-sdk/reference/event).

It has three parts: a heap-backed **writer**, a stack-allocatable **reader**, and a **validator**.

## Conventions

A few rules hold across the codec:

- **Integers are written in their smallest MessagePack form** automatically — you write an `int64`/`uint64` and the encoder picks the compact encoding.
- **`str` values must be valid UTF-8.** Use `bin` for arbitrary bytes. The reader enforces this on `str` reads too.
- **A valid payload is exactly one top-level value**, and an **empty buffer is not valid**. (A map or array at the top counts as that one value.)
- **The writer is sticky-error**, exactly like the [`<peios/security.h>` builders](~peios-sdk/getting-started/library-conventions#memory-ownership): the write calls cannot fail individually; the first error latches and surfaces at `peios_mp_writer_bytes` / `peios_mp_writer_error`.

## Writer

```c
typedef struct peios_mp_writer peios_mp_writer;

peios_mp_writer *peios_mp_writer_new(void);
void             peios_mp_writer_free(peios_mp_writer *w);
void             peios_mp_writer_reset(peios_mp_writer *w);
```

Create a writer, append values, take the bytes, free it (or `reset` to reuse). All the append calls return `void` — errors latch.

### Scalars

```c
void peios_mp_write_nil(peios_mp_writer *w);
void peios_mp_write_bool(peios_mp_writer *w, bool v);
void peios_mp_write_int(peios_mp_writer *w, int64_t v);
void peios_mp_write_uint(peios_mp_writer *w, uint64_t v);
void peios_mp_write_float(peios_mp_writer *w, double v);
void peios_mp_write_str(peios_mp_writer *w, const char *s, size_t len);  /* UTF-8 */
void peios_mp_write_bin(peios_mp_writer *w, const void *b, size_t len);
```

Use `peios_mp_write_int` for signed and `peios_mp_write_uint` for unsigned values; both are stored in the smallest form. `peios_mp_write_str` takes UTF-8 with an explicit length (no NUL needed); `peios_mp_write_bin` takes arbitrary bytes.

### Containers

```c
void peios_mp_write_array(peios_mp_writer *w, uint32_t count);
void peios_mp_write_map(peios_mp_writer *w, uint32_t count);
```

Write the header, then exactly the promised number of values. **A map of `count` needs `2 * count` values** — `count` key/value *pairs* — written key, value, key, value…. An under- or over-filled container is not caught at the `write` call; it surfaces at `peios_mp_writer_bytes`, when the whole structure is validated.

```c
/* {"user": "alice", "ok": true} */
peios_mp_write_map(w, 2);
peios_mp_write_str(w, "user", 4);  peios_mp_write_str(w, "alice", 5);
peios_mp_write_str(w, "ok", 2);    peios_mp_write_bool(w, true);
```

### Extensions and raw bytes

```c
void peios_mp_write_ext(peios_mp_writer *w, int8_t ext_type, const void *b, size_t len);
void peios_mp_write_raw(peios_mp_writer *w, const void *b, size_t len);
```

- `peios_mp_write_ext` writes a MessagePack extension value with a signed type id.
- `peios_mp_write_raw` appends **pre-encoded** MessagePack bytes verbatim — the escape hatch for splicing in a value you already have encoded. The result is still structurally validated as a whole at `peios_mp_writer_bytes`, so you can't smuggle malformed bytes through it.

### Taking the bytes

```c
ssize_t peios_mp_writer_bytes(peios_mp_writer *w, const void **out);
int     peios_mp_writer_error(const peios_mp_writer *w);
```

`peios_mp_writer_bytes` **confirms the buffer is exactly one well-formed top-level value**, then borrows it: it writes a pointer to the encoded bytes through `out` (valid until the next mutating call on `w`) and returns the length. Pass `out == NULL` to validate and get the length without borrowing. It returns `-1` with `errno` — `EINVAL` on a latched error or a malformed/under-filled structure, `ENOMEM` on a prior allocation failure. `peios_mp_writer_error` returns the latched errno directly, or `0`.

Because this call validates, a successful `peios_mp_writer_bytes` is your guarantee the bytes are emit-ready.

## Reader

The reader is a **cursor over a borrowed buffer** — stack-allocatable, no heap, no free. It decodes one value at a time, advancing the cursor.

```c
struct peios_mp_reader { uint64_t _opaque[4]; };   /* opaque — do not inspect */

void   peios_mp_reader_init(struct peios_mp_reader *r, const void *buf, size_t len);
size_t peios_mp_reader_remaining(const struct peios_mp_reader *r);
```

Declare a `struct peios_mp_reader` locally and `peios_mp_reader_init` it over your buffer before use. `buf` may be `NULL` only when `len` is zero. Borrowed `str`/`bin`/`ext` pointers the reader hands back point **into the original buffer** and are valid for as long as it lives. `peios_mp_reader_remaining` reports the unconsumed byte count.

### Peeking

```c
enum peios_mp_type {
    PEIOS_MP_NIL, PEIOS_MP_BOOL, PEIOS_MP_INT, PEIOS_MP_FLOAT,
    PEIOS_MP_STR, PEIOS_MP_BIN, PEIOS_MP_ARRAY, PEIOS_MP_MAP, PEIOS_MP_EXT,
};

int peios_mp_peek(const struct peios_mp_reader *r);
```

`peios_mp_peek` returns the `peios_mp_type` of the next value **without consuming it**, or `-1` at end-of-input or on an invalid lead byte. Note that integers of every width and sign report as `PEIOS_MP_INT` — read them with `peios_mp_read_int` or `peios_mp_read_uint` as you prefer. Peek is how you drive a dispatch over a value whose type you don't know ahead of time.

### Reading scalars

```c
int peios_mp_read_nil(struct peios_mp_reader *r);
int peios_mp_read_bool(struct peios_mp_reader *r, bool *out);
int peios_mp_read_int(struct peios_mp_reader *r, int64_t *out);
int peios_mp_read_uint(struct peios_mp_reader *r, uint64_t *out);
int peios_mp_read_float(struct peios_mp_reader *r, double *out);
```

Each **consumes one value on success** (returns `0`) and leaves the cursor **untouched on a type mismatch or truncation** (`-1` with `errno == EINVAL`) — so a failed read is safe to follow with a different-typed read or a `peek`. The `out` pointer is optional: pass `NULL` to consume/type-check a value without receiving its payload.

### Reading strings, bytes, containers, extensions

```c
ssize_t peios_mp_read_str(struct peios_mp_reader *r, const char **out);
ssize_t peios_mp_read_bin(struct peios_mp_reader *r, const void **out);
ssize_t peios_mp_read_array(struct peios_mp_reader *r);
ssize_t peios_mp_read_map(struct peios_mp_reader *r);
ssize_t peios_mp_read_ext(struct peios_mp_reader *r, int8_t *type_out, const void **out);
int     peios_mp_skip(struct peios_mp_reader *r);
```

- `peios_mp_read_str` / `peios_mp_read_bin` **borrow** the bytes (a pointer into the reader's buffer via `out`) and return the length, or `-1`. Strings are **not** NUL-terminated — use the length — and `peios_mp_read_str` rejects invalid UTF-8.
- `peios_mp_read_array` returns the **element count**; `peios_mp_read_map` returns the **key/value pair count** (so read `2 * count` values). After the header you read that many values yourself.
- `peios_mp_read_ext` borrows an extension value's bytes, reporting its signed type id through `type_out` (both `type_out` and `out` are independently optional), and returns the data length.
- `peios_mp_skip` consumes **exactly one complete value**, descending into nested containers — the way to ignore a value (or a whole subtree) you don't care about. `0` / `-1`.

```c
struct peios_mp_reader r;
peios_mp_reader_init(&r, payload, payload_len);

ssize_t pairs = peios_mp_read_map(&r);          /* top-level map */
for (ssize_t i = 0; i < pairs; i++) {
    const char *key; ssize_t klen = peios_mp_read_str(&r, &key);
    /* dispatch on key… then read or skip the value */
    peios_mp_skip(&r);
}
```

## Validator

```c
int peios_mp_validate(const void *buf, size_t len, uint32_t max_depth);
```

`peios_mp_validate` confirms `buf`/`len` is **exactly one well-formed MessagePack value**: UTF-8 strings, nesting bounded by `max_depth`, no trailing bytes, non-empty. Returns `0` if valid, `-1` with `errno == EINVAL` otherwise.

Crucially, its acceptance **matches the kernel's emit-time check**, so a `0` return means the [event emit calls](~peios-sdk/reference/event#emitting-events) will accept the payload — *at this depth bound*. Pass `KMES_CONFIG_MAX_NESTING_DEPTH_DEFAULT` (32) for the default emit limit; the top-level value is depth 1. Validate before emitting when a payload comes from an untrusted or dynamic source, so you turn a would-be `EINVAL` from the kernel into a check you control.

## See also

- **[`<peios/event.h>`](~peios-sdk/reference/event)** — the KMES events these payloads travel in.
- **[Library conventions](~peios-sdk/getting-started/library-conventions)** — the sticky-error builder model the writer follows.
