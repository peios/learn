---
title: Watch Records
description: Watch records are not KMES events — binary records read from a key file descriptor, their layout, and what a subtree watch adds.
---

Watch records are **not KMES events**. They are binary records read from
a key file descriptor with `read()`, and they exist to tell a watcher
that something under a key changed.

They are documented here because an operator asking what the registry
reports would otherwise miss them, but nothing else in this book applies
to them: no msgpack, no envelope, no identity stamps, no audit meaning.

## Reading

A single `read()` returns as many complete records as fit in the
caller's buffer. A record is never split across two calls.

If the buffer cannot hold even the first queued record, `read()` fails
with `EINVAL` — the buffer is too small to make progress, and the caller
retries with a larger one. On an armed fd with an empty queue, `read()`
blocks, or returns `EAGAIN` under `O_NONBLOCK`.

Only records copied out in full are dequeued.

## Layout

Every record begins with the same four fields.

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | `total_len` |
| 4 | 2 | `event_type` |
| 6 | 2 | `name_len` |
| 8 | `name_len` | `name`, UTF-8 |

All integers are little-endian. `total_len` is the whole record
including this header, it is how a consumer advances to the next record,
and it is the **only** safe way to do so.

## Subtree watches carry a path

A subtree watch's records carry additional fields after the name,
locating the key the change happened on relative to the watched key.

| Size | Field |
|---|---|
| 2 | `path_depth` |
| `2 + n` each | `path_components`: a `u16` length, then that many UTF-8 bytes |

`path_depth` is the number of components from the watched key down to
the changed key. Zero means the change was on the watched key itself.

The components are length-prefixed rather than joined by a separator
because registry names can contain any Unicode character and value names
can contain backslashes. A concatenated path string would be ambiguous.

`OVERFLOW` records are emitted in the bare eight-byte form, with no path
even on a subtree watch — there is no single key to name when the queue
itself overflowed.

The header offsets are ABI, named in `uapi/pkm/lcs.h` and listed in the
Peios Kernel TRM §5.A.
