---
title: Receiving Queries
description: How the stub listener reads queries over UDP and TCP — source checks, connection limits, the per-connection bound, the queries it refuses at the door, and what it ignores in a query it accepts.
---

The stub listener's address, its loopback-only rule and its rendering
are PSPU §6.8. This article covers how resolvd reads queries; the
replies are §6.2.

## UDP

When the UDP socket is readable, every waiting datagram is read. For
each:

1. A datagram whose source address is not a loopback address — anything
   outside `127.0.0.0/8` — is dropped without a reply. [*stub-receive.udp-non-loopback-source-dropped]
2. It is checked as a query (below). A refused query gets its error
   reply, or nothing.
3. An accepted query becomes an engine question (§4.1).

### The UDP read buffer [*stub-receive.udp-read-buffer-4096]

Each datagram is read into a 4 096-byte buffer; a longer datagram is
truncated by the read to its first 4 096 bytes.

### A UDP query longer than the buffer [*stub-receive.udp-oversized-query-formerr]

A query longer than 4 096 bytes therefore arrives cut short. When the
cut falls inside the DNS message, the message no longer decodes and,
being at least 12 bytes long, is answered `FORMERR` (below). Bytes after
the end of the message are ignored by decoding, so a query whose message
fits in 4 096 bytes and is only padded beyond them is answered as usual.

### Where UDP replies go [*stub-receive.udp-reply-to-source]

Replies are sent to the source address and port the query came from.

## TCP

When the TCP listener is readable, every waiting connection is accepted.
A connection is closed at once, without a reply:

- when 256 accepted stub connections are still sending their queries; [*stub-receive.tcp-pending-cap-256]
- when its source is not a loopback address. [*stub-receive.tcp-non-loopback-source-closed]

A connection that cannot be made nonblocking is closed the same way.

### Reading a TCP query

Each held connection is read as it becomes readable, everything
available each time, in 4 096-byte chunks. A message is a two-byte
big-endian length and that many bytes.

- When more than 65 537 bytes are buffered, the connection is closed
  without a reply. [*stub-receive.tcp-buffer-ceiling]
- When a whole message has arrived, it is checked as a query, and the
  connection leaves the set of connections still sending.
- A connection carries one query. Anything sent after the first message
  is ignored, and the connection is closed once the answer, or the
  error reply, has been written. [*stub-receive.tcp-one-query-per-connection]
- A connection that closes, or fails to read, before its message is
  whole is closed without a reply.
- A client that sends its query and then shuts down its writing side
  gets no reply when the end of file is already waiting behind the
  query: the read that finds the query also finds the end of file, and
  the connection is closed without the query being checked. A query
  whose end of file arrives after resolvd has read it is answered as
  usual. [*stub-receive.tcp-query-then-half-close-dropped]
- A connection that has not delivered a whole message ten seconds after
  it was accepted is closed without a reply. [*stub-receive.tcp-ten-second-delivery-bound]
- Once its query has arrived the ten-second bound no longer applies; the
  connection is held until the engine answers. [*stub-receive.tcp-bound-ends-once-query-arrives]

## Checking a query

| The message | Result |
|---|---|
| Does not decode, and is at least 12 bytes long | `FORMERR`: the query's ID, `QR` set, every other header bit clear, no sections [*stub-receive.undecodable-long-message-formerr] |
| Does not decode, and is shorter than 12 bytes | Dropped without a reply [*stub-receive.undecodable-short-message-dropped] |
| Has `QR` set | Dropped without a reply [*stub-receive.response-dropped] |
| Has an opcode other than `QUERY` | `NOTIMP` [*stub-receive.non-query-opcode-notimp] |
| Has no question, or more than one | `FORMERR` [*stub-receive.question-count-formerr] |
| Otherwise | Accepted |

### The `NOTIMP` and question-count `FORMERR` replies

These two replies are built from the query:

- the header copies the query's ID, opcode, `RD` and `CD` bits, and
  sets `QR` and `RA`; every other bit is clear; [*stub-receive.error-reply-header]
- the question section is the query's, whatever it holds; [*stub-receive.error-reply-question]
- when the query carried an `OPT` record, the reply carries one whose
  payload size is the size the query advertised, with `DO` clear and no
  options; without one, the reply has none. [*stub-receive.error-reply-opt-size]

## What an accepted query contributes

- Only the question's name and type reach the engine. The question's
  class is not looked at: a query of any class is answered as if it were
  `IN`. [*stub-receive.class-ignored]
- `RD`, `CD`, the `DO` bit and any EDNS options are not looked at. [*stub-receive.flags-and-edns-options-ignored]
- Stub queries always consult the cache (§4.5).

### Names with escaped labels

The name is handed to the engine in presentation form and parsed again
(§4.1), and the parse does not interpret escapes (§5.3).

- A label holding a dot, a backslash, or a byte outside `!` to `~` is
  printed with an escape, so such a name is asked as a different name: a
  dot inside a label becomes a label boundary, and the escapes' bytes
  become part of the labels. [*stub-receive.escaped-labels-asked-as-different-name]
- When the escapes take a label past 63 bytes, or the name past 255
  bytes on the wire, the question is answered `notfound`. [*stub-receive.escaped-label-overlong-is-notfound]

## Which stub queries are counted [*stub-receive.refused-queries-not-counted]

Every accepted query counts in `queries` (§4.10); refused ones do not.
