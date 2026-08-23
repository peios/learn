---
title: Framing and Encoding
description: One compact JSON object per newline-terminated frame, in both directions — what counts as malformed, and when the manager closes.
---

## Frames

Every message in both directions is one frame: a single JSON object,
serialised compactly, followed by one `0x0A` byte. This applies to
requests and to responses alike, and the manager MUST terminate every
response with a newline.

Framing is byte-oriented and is performed before any JSON is parsed. A
`0x0A` byte ends the frame wherever it appears, so a raw newline inside
what a sender intended as a JSON string does not produce one frame with
an embedded newline — it produces two malformed ones. (A raw `0x0A`
inside a JSON string is not valid JSON in any case; the `\n` escape
sequence is unaffected and is the way to carry a newline in a value.)

The manager MUST NOT emit pretty-printed JSON, and MUST NOT emit more
than one object per frame.

## Encoding

Frames are UTF-8. The manager MUST reject a frame that is not
well-formed UTF-8 with `MALFORMED_REQUEST`.

## What is malformed

The manager MUST answer with `MALFORMED_REQUEST` when a frame:

- is empty — a bare newline with no content;
- is not well-formed UTF-8;
- is not valid JSON;
- is valid JSON but not an **object**. An array, a string, a number,
  `true`, `false` and `null` are all malformed requests.

## Closing after an error

The manager MUST distinguish two classes of failure, because they say
different things about the connection.

A **frame-level** failure means the manager cannot trust the stream's
framing any more: it does not know where the next frame begins.
`MALFORMED_REQUEST` for an empty frame and `REQUEST_TOO_LARGE` are both
frame-level. The manager MUST send the error response, discard any
buffered input, and close the connection.

A **command-level** failure means the frame was well-formed and the
command in it could not be carried out: unparseable JSON content, an
unknown command, missing arguments, a denied access check, an unknown
service. The manager MUST send the error response and MUST keep the
connection open.

A client MUST NOT assume a connection survives an error response, and
MUST be prepared for either.

## Timestamps

Every timestamp field the manager emits MUST be a UTC RFC 3339 string
with exactly **nine** fractional-second digits and the literal offset
marker `Z`:

```
"2026-06-01T12:34:56.123456789Z"
```

The manager MUST NOT emit a numeric offset in place of `Z`, and MUST NOT
vary the number of fractional digits.

These are wall-clock instants, presented for a reader. The manager MUST
NOT derive elapsed-time decisions — timeouts, retries, ordering — from
wall-clock differences, and a client MUST NOT assume that two timestamps
in the same response were taken from a clock that did not move between
them.
