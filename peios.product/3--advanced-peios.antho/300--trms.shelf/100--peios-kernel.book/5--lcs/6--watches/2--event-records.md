---
title: Event Records
description: Events read from the key fd with read() — the record layout, why not every subtree record carries a path, and forward compatibility.
---

Events are read from the key fd with `read()`. A single call returns as
many complete events as fit in the caller's buffer; an event is never
split across two calls. If the buffer cannot hold even the first queued
event, `read()` fails with `EINVAL` — the buffer is too small to make
progress, and the caller has to try again with a larger one. On an
armed fd with an empty queue, `read()` blocks, or returns `EAGAIN` under
`O_NONBLOCK`.

Only events that were copied out in full are dequeued.

## Layout

Every record begins with the same four fields.

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | `total_len` |
| 4 | 2 | `event_type` |
| 6 | 2 | `name_len` |
| 8 | `name_len` | `name`, UTF-8 |

All integers are little-endian. `total_len` is the whole record
including this header; it is how a consumer advances to the next event,
and it is the only safe way to do so.

A subtree watch's records carry additional fields after the name,
locating the key the change happened on relative to the watched key:

| Size | Field |
|---|---|
| 2 | `path_depth` |
| `2 + n` each | `path_components`: `len` (u16) then that many UTF-8 bytes |

`path_depth` is the number of components from the watched key down to
the changed key; zero means the change was on the watched key itself.
The components are length-prefixed rather than joined with a separator,
because registry names can contain any Unicode character and value
names can contain backslashes — a concatenated path string would be
ambiguous.

The header offsets are ABI, named in `uapi/pkm/lcs.h` and listed in
§5.A.

## Not every record on a subtree watch has a path

`OVERFLOW` records are emitted in the bare eight-byte form, on every
watch, whether or not that watch is a subtree watch. `KEY_DELETED` is
not: a subtree watcher receives it in the subtree form, with a
`path_depth` of its own.

A consumer of a subtree watch therefore cannot assume the subtree
fields are present on every record it reads. `total_len` is the cursor;
`path_depth` is read only when the record is long enough to hold it.

## Length limits

`name_len` and each component length are 16-bit. If an event's name or
one of its path components is too long to be represented, LCS does not
emit a truncated or malformed record: it substitutes or preserves an
`OVERFLOW` for that watcher instead, which is a statement the consumer
already knows how to act on.

## Forward compatibility

Future versions may append fields after `path_components`. An existing
consumer skips them, because it advances by `total_len`; a newer one
compares `total_len` against what it has parsed to discover whether the
optional fields are present. This is the whole extension mechanism, and
it is why the length field comes first.
