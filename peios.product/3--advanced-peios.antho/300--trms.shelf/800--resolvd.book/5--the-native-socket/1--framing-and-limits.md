---
title: Framing and Limits
description: How resolvd reads a request from a native connection — the connection cap, the size ceiling, the five-second bound, decoding, and the exact error replies — and how it writes the reply.
---

The framing, the one-request-per-connection rule and the requirement to
answer errors with an error reply are PSPU §6.4's. This article is
resolvd's reading of them.

## Accepting connections [*native-framing.pending-connection-cap-closes-silently]

Every waiting connection is accepted when the listener is ready. When
256 accepted connections are still sending their requests, a newly
accepted connection is closed at once, with no reply; so is one that
cannot be made nonblocking. Connections whose requests have been read do
not count towards the 256 (§2.4).

## Reading the request

Each connection is read in 4 096-byte chunks, everything available each
time it is ready, and the bytes are buffered.

1. While reading, as soon as more than 65 540 bytes are buffered — the
   four-byte length and a 65 536-byte payload — resolvd replies
   `request too large` and closes the connection. [*native-framing.buffered-bytes-ceiling]
2. After the read, when at least four bytes are buffered, they are the
   payload length, little-endian. A length above 65 536 gets the reply
   `request too large` and the connection is closed. [*native-framing.length-ceiling]
3. When the whole payload is buffered, it is decoded. Bytes after it are
   ignored, as long as the buffered total stayed within the first
   check. [*native-framing.trailing-bytes-ignored]

### Which size check fires [*native-framing.payload-read-before-length-check]

Both size checks are made on what has already been read. resolvd reads
whatever the client has sent before it looks at the length, so the
first bytes of an oversized payload are read before it is refused. A
client that sends more than 65 540 bytes in one burst is refused by the
first check before the length is looked at — even when the length is
within the ceiling and the excess is bytes after the payload.

## A connection that ends early

- A connection that closes, or fails to read, before its request is
  complete is dropped without a reply. [*native-framing.early-close-dropped]
- A client that sends its whole request and then shuts down its writing
  side gets no reply when the end of file is already waiting behind the
  request: the read that finds the request also finds the end of file,
  and the connection is dropped without the request being decoded. A
  request whose end of file arrives after resolvd has read it is
  answered as usual. [*native-framing.request-then-half-close-dropped]
- A connection that has not delivered a complete request five seconds
  after it was accepted is closed without a reply. [*native-framing.five-second-delivery-bound]

## Decoding

The payload is a MessagePack map, decoded as follows:

- Every key is a string, and a key repeated in the request's top-level
  map is an error. Keys inside a skipped value are not checked for
  repeats. [*native-framing.duplicate-top-level-key-is-error]
- A key resolvd does not know is skipped, whatever its value — `nil`,
  boolean, integer, string, binary, array or map. [*native-framing.unknown-keys-skipped]
- A floating-point or extension value anywhere inside an unknown key's
  value fails the decode, and so does a string inside it that is not
  UTF-8: a skipped string is still checked. [*native-framing.unknown-key-unsupported-value-fails]
- An array or map nested more than 32 levels deep inside an unknown
  key's value, counting the value itself as the first level, fails the
  decode. [*native-framing.unknown-key-nesting-limit]
- `query` names the request; a missing `query` is an error, and an
  unknown one is an error. [*native-framing.missing-or-unknown-query-is-error]
- Every key resolvd knows — `query`, `name`, `type`, `no_cache`,
  `family` and `address` — is read and type-checked in every request,
  whether that request takes it or not, with the types of PSPU §6.5. A
  value of the wrong type is an error, so `{query: status, name: 5}` is
  refused; `type` is checked against 65 535 in every request, so
  `{query: status, type: 70000}` is refused too. `family` takes any
  string (§5.3), and `address` is parsed as an address only in a
  `reverse`. [*native-framing.wrong-field-type-is-error]
- Anything after the top-level map in the payload is ignored. [*native-framing.bytes-after-map-ignored]

The map is read in order, and the first error met is the one reported.
A missing field is looked for only after the whole map has been read.

## Error replies

Every error reply is `ok: false` with an `error` string and nothing
else:

| `error` | Cause |
|---|---|
| `request too large` | The size checks above |
| `malformed message: truncated message` | The payload ends inside a value, or an array or map claims more items than bytes remain, a map's keys and values counted separately [*native-framing.error-truncated] |
| `malformed message: unexpected value type` | A known field, a key, or the payload itself has the wrong MessagePack type; this includes a `type` that is negative or above 9 223 372 036 854 775 807 [*native-framing.error-unexpected-type] |
| `malformed message: unsupported value type` | A floating-point or extension value [*native-framing.error-unsupported-type] |
| `malformed message: string is not UTF-8` | A string that is not UTF-8 [*native-framing.error-not-utf8] |
| `malformed message: nested too deeply` | Nesting beyond 32 levels inside a skipped value [*native-framing.error-nested-too-deeply] |
| `missing or malformed field <name>` | A field the request needs is absent; a `type`, in any request, from 65 536 to 9 223 372 036 854 775 807; or the `address` of a `reverse` that is not an IP address [*native-framing.error-missing-or-malformed-field] |
| `duplicate field <name>` | A repeated key [*native-framing.error-duplicate-field] |
| `unknown query "<name>"` | A `query` resolvd does not know [*native-framing.error-unknown-query] |
| `access denied` | The access check (§5.2) |

### The connection after an error reply [*native-framing.connection-closed-after-error-reply]

After an error reply the connection is closed.

## Writing the reply

- The reply is framed the same way — four-byte little-endian length,
  then the MessagePack map — and written in one blocking write with a
  one-second timeout (§2.5). A failed write is logged as
  `control: reply failed: <error>`. The connection is then closed. [*native-framing.reply-written-then-closed]
- The size of a reply is not checked against the 65 536-byte ceiling
  before it is written. [*native-framing.reply-size-not-checked]
