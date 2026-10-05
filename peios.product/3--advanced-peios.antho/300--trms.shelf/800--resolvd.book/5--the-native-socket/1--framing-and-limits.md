---
title: Framing and Limits
description: How resolvd reads a request from a native connection — the connection cap, the size ceiling, the five-second bound, decoding, and the exact error replies — and how it writes the reply.
---

The framing, the one-request-per-connection rule and the requirement to
answer errors with an error reply are PSPU §6.4's. This article is
resolvd's reading of them.

## Accepting

Every waiting connection is accepted when the listener is ready. When
256 accepted connections are still sending their requests, a newly
accepted connection is closed at once, with no reply. [*native-framing.pending-connection-cap-closes-silently] Connections whose
requests have been read do not count towards the 256 (§2.4).

## Reading the request

Each connection is read in 4 096-byte chunks, everything available each
time it is ready, and the bytes are buffered. After each read:

1. If more than 65 540 bytes are buffered — the four-byte length and a
   65 536-byte payload — resolvd replies `request too large` and closes
   the connection. This check is made while reading, so it can be the
   one that fires when a client sends a large request in one burst. [*native-framing.buffered-bytes-ceiling]
2. When at least four bytes are buffered, they are the payload length,
   little-endian. A length above 65 536 gets the reply
   `request too large` and the connection is closed. [*native-framing.length-ceiling]
3. When the whole payload is buffered, it is decoded. Bytes after it are
   ignored. [*native-framing.trailing-bytes-ignored]

Both size checks are made on what has already been read. resolvd reads
whatever the client has sent before it looks at the length, so the
first bytes of an oversized payload are read before it is refused. [*native-framing.payload-read-before-length-check]

A connection that closes, or fails to read, before its request is
complete is dropped without a reply. [*native-framing.early-close-dropped] A connection that has not delivered
a complete request five seconds after it was accepted is closed without
a reply. [*native-framing.five-second-delivery-bound]

## Decoding

The payload is a MessagePack map, decoded as follows:

- every key is a string, and a key repeated in the request's top-level
  map is an error; [*native-framing.duplicate-top-level-key-is-error]
- a key resolvd does not know is skipped, whatever its value — `nil`,
  boolean, integer, string, binary, array or map — but a floating-point
  or extension value in it, or an array or map nested more than 32
  levels deep inside it, fails the decode; [*native-framing.unknown-keys-skipped-except-float-ext-deep]
- `query` names the request; a missing `query` is an error, and an
  unknown one is an error; [*native-framing.missing-or-unknown-query-is-error]
- the fields each request takes are those of §5.3, with the types of
  PSPU §6.5; a field of the wrong type is an error. [*native-framing.wrong-field-type-is-error]

Anything after the top-level map in the payload is ignored. [*native-framing.bytes-after-map-ignored]

## Error replies

Every error reply is `ok: false` with an `error` string and nothing
else:

| `error` | Cause |
|---|---|
| `request too large` | The size checks above |
| `malformed message: truncated message` | The payload ends inside a value, or a container claims more entries than bytes remain [*native-framing.error-truncated] |
| `malformed message: unexpected value type` | A known field, a key, or the payload itself has the wrong MessagePack type [*native-framing.error-unexpected-type] |
| `malformed message: unsupported value type` | A floating-point or extension value [*native-framing.error-unsupported-type] |
| `malformed message: string is not UTF-8` | A string that is not UTF-8 [*native-framing.error-not-utf8] |
| `malformed message: nested too deeply` | Nesting beyond 32 levels inside a skipped value [*native-framing.error-nested-too-deeply] |
| `missing or malformed field <name>` | A field the request needs is absent, `type` is above 65 535, or an `address` is not an IP address [*native-framing.error-missing-or-malformed-field] |
| `duplicate field <name>` | A repeated key [*native-framing.error-duplicate-field] |
| `unknown query "<name>"` | A `query` resolvd does not know [*native-framing.error-unknown-query] |
| `access denied` | The access check (§5.2) |

After an error reply the connection is closed. [*native-framing.connection-closed-after-error-reply]

## Writing the reply

The reply is framed the same way — four-byte little-endian length, then
the MessagePack map — and written in one blocking write with a
one-second timeout (§2.5). A failed write is logged as
`control: reply failed: <error>`. The connection is then closed. [*native-framing.reply-written-then-closed] The
size of a reply is not checked against the 65 536-byte ceiling before it
is written. [*native-framing.reply-size-not-checked]
