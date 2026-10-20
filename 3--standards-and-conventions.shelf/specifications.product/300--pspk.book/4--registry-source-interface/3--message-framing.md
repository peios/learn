---
title: Message Framing
description: The 22-byte request header and its response, the binary encoding, the asymmetry in how each side may be extended, and the concurrency rules.
---

The protocol is binary and multiplexed. All multi-byte integers are
little-endian.

## The request header

A request is 22 bytes of header followed by an operation-specific
payload.

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | `total_len` |
| 4 | 8 | `request_id` |
| 12 | 2 | `op_code` |
| 14 | 8 | `txn_id` |

`total_len` is the whole message including the header.

`request_id` matches a response to its request. Request ids are
allocated by the kernel, are strictly increasing within one connection,
and are never reused while that connection lives — including after a
request has timed out.

`txn_id` is the transaction the operation belongs to, or zero for none.
When non-zero, the source MUST process the operation inside that
transaction's context.

## The response header

A response is 14 bytes of header followed by a payload. It carries no
`txn_id`.

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | `total_len` |
| 4 | 8 | `request_id` |
| 12 | 2 | `op_code` |

A source MUST copy `request_id` from the request into its response, and
MUST set `op_code` to the request's operation code with the high bit
set — that is, `op_code | 0x8000`. Every operation has a named response
code for this value.

Every response payload begins with a `u32` status at offset 14, so the
minimum response size is 18 bytes.

## Encoding

A **length-prefixed field** is a `u32` byte count followed by that many
bytes. Strings so encoded are UTF-8 and carry no terminator; a
terminator byte counted in the length is a null byte and is therefore
invalid. Some length-prefixed fields carry binary rather than text —
Security Descriptors and value data — and are not UTF-8.

A **GUID** is 16 raw bytes.

An **array** is a `u32` count followed by that many entries.

A **boolean** is one byte.

## Extension, and its asymmetry

Requests and responses extend differently, and a source MUST implement
both rules.

A **request** MAY carry trailing fields beyond those a source
recognises. A source MUST skip them, using `total_len` to find the end
of the message. This is how the kernel adds an optional field without
an RSI version bump.

A **response** MUST NOT. The kernel rejects any trailing bytes in a
response payload as malformed data. A source MUST emit exactly the
payload each operation defines, and no more. Extending the protocol in
this direction is done with new operations, never by growing an
existing payload.

## Reading and writing

The device fd is message-oriented. `total_len` frames messages, but a
successful I/O call never splits or joins one.

**`read()`** returns exactly one complete request. If none is queued, a
blocking read waits until one is, or until the fd is closing, in which
case it returns 0. Under `O_NONBLOCK` an empty queue returns `EAGAIN`.
If the caller's buffer is too small for the next queued request,
`read()` returns `EMSGSIZE` and **does not consume it**.

**`write()`** submits exactly one complete response. The buffer length
MUST equal the response header's `total_len`, and MUST be at least the
response header size. A successful write is never short.

The following all fail `EINVAL` **and tear the connection down**,
marking the source Down:

- a length shorter than the response header;
- a length that does not equal `total_len`;
- an unknown `request_id`;
- a response to a request that has not been delivered;
- a second response to a request already answered;
- an `op_code` that is not the request's with the response bit set;
- a response written on a descriptor that is not the slot's active one.

A source that cannot frame its own messages correctly is not one whose
other answers can be relied on. Ordinary per-operation errors are
reported through the status vocabulary and do not tear anything down.

**`poll()`** reports the fd readable when at least one complete request
is queued, writable while the slot is Active, and `POLLHUP | POLLERR`
when the slot is Down or the fd is closing. An fd that is open but not
yet registered reports nothing.

## Concurrency and timing

A source MAY process requests in any order and MUST handle multiple
in-flight requests without head-of-line blocking. Responses are matched
by `request_id`, not by arrival order.

The kernel bounds in-flight requests per source by
`MaxConcurrentRSIRequests`, default 256.

A source MUST respond to **every** request it has read, exactly once,
even if the kernel-side caller has already given up. The kernel applies
a request timeout — `RequestTimeoutMs`, default 30 seconds, measured
from the moment it first tries to reserve an in-flight slot and
covering the whole wait — and a source is **not** disconnected for
exceeding it. Late responses are validated and processed exactly like
on-time ones.

A timed-out request remains in the kernel's in-flight table, and keeps
occupying one of the source's slots, until the source answers or the
connection is torn down. A source that accumulates unanswered requests
will exhaust its own concurrency budget.
