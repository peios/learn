---
title: The Upstream Query
description: What resolvd puts on the wire for each transaction — sockets and source ports, the message identifier and 0x20 case pattern, EDNS0, link-local servers, and the TCP retry.
---

PSPU §6.7 sets the upstream behaviour. This article is what resolvd puts
on the wire to meet it.

## Sockets

### One socket per transaction [*engine-query.socket-per-transaction]

Every transaction has its own socket, opened when the transaction is
sent and closed when it ends.

### The UDP socket

- A new socket is bound to the unspecified address of the server's
  family, port 0, so the kernel picks the source address and a fresh
  ephemeral source port. [*engine-query.udp-fresh-ephemeral-port]
- The socket is connected to the server's port 53, so the kernel
  delivers only datagrams from that address and port. [*engine-query.udp-socket-connected-to-server]
- Each datagram is read into a 4 096-byte buffer; a longer datagram is
  truncated by the read. [*engine-query.udp-read-buffer-4096]

The query is sent with one `send`.

### The TCP connection [*engine-query.tcp-one-query-per-connection]

A new nonblocking socket is connected to the server's port 53. When the
connection completes, the query is written with its two-byte length
prefix; once it is all written, the socket is read until the two-byte
length and that many bytes of reply have arrived. Bytes after the first
message are ignored. One query is sent per connection, and the
connection is closed when the transaction ends.

### A transaction that cannot be sent [*engine-query.send-failure-logged]

A failure found while a transaction is being sent — opening or binding
its socket, connecting it, or, for UDP, sending the query — fails the
attempt at once (§4.6) and is logged at warn level as
`upstream <server>: <error>`. A TCP failure found later, once the
connection is under way, is not logged, and neither is a timeout or a
UDP receive error.

## Link-local servers

- An address with a zone, such as `fe80::1%eth0`, is not an IP address
  to resolvd: from netd it is dropped silently (§3.3), and in
  `FallbackServers` it is skipped and logged (§2.3). A server cannot be
  given the interface it is reached through. [*engine-query.zoned-server-address-dropped]
- A bare link-local address such as `fe80::1` is accepted, and every
  transaction to it is opened with no scope identifier. The connect then
  fails at once, so every attempt to that server fails: `upstream
  fe80::1: <error>` is logged, the server is demoted, and `upstream_sent`
  and `upstream_failed` both rise. [*engine-query.link-local-server-sent-unscoped]

## The message

| Field | Value |
|---|---|
| ID | 16 bits from the engine's generator, fresh for every transaction [*engine-query.id-fresh-per-transaction] |
| Flags | `RD` set; `CD` clear; everything else clear [*engine-query.rd-set-other-flags-clear] |
| Question | The candidate, case-randomised; the record type asked; class `IN` [*engine-query.question-is-randomised-candidate-in-class-in] |
| Additional | One `OPT` record: payload size 1 232, `DO` clear, extended response code 0, version 0, no options [*engine-query.opt-record-advertises-1232] |

Authority and answer sections are empty.

### The generator [*engine-query.generator-is-xorshift64-star]

The ID and the case pattern come from a xorshift64\* generator seeded
once at startup from eight bytes of `/dev/urandom` (§2.2). It is not a
cryptographic generator. The ID is the low 16 bits of the first output
drawn for a transaction; the case bits start with the second.

### Case randomisation

- Every ASCII letter in the candidate is flipped between upper and lower
  case when its bit of the generator's output is 1. Digits, hyphens and
  other bytes are unchanged. [*engine-query.letters-flipped-on-generator-bits]
- Bits are taken from one output, lowest first, until 64 have been used,
  and then from the next output. A bit is used only for a letter. [*engine-query.case-bits-consumed-per-letter]
- Each transaction — a retry to the same server, and the TCP retry after
  truncation, included — gets a new pattern and a new ID. [*engine-query.new-pattern-every-transaction]

## No fallback without EDNS0 [*engine-query.no-fallback-without-edns]

Every query carries the `OPT` record. resolvd does not fall back to a
query without EDNS0: a server that answers an EDNS0 query with
`FORMERR` has failed the attempt (§4.6).

## The TCP retry

- A matching UDP reply with `TC` set is not used. The same candidate is
  sent to the same server over TCP as a new transaction, with a new ID,
  a new case pattern and its own two-second deadline. It does not count
  as an attempt (§4.6). [*engine-query.truncated-udp-retried-over-tcp-same-server]
- A TCP reply with `TC` set is used as it is. [*engine-query.truncated-tcp-reply-used-as-is]
