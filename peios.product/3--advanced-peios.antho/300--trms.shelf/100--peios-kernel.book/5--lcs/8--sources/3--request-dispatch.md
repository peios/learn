---
title: Request Dispatch
description: The RSI is multiplexed — request ids and matching, the single deadline covering three waits, and requests with no caller.
---

The RSI is multiplexed. LCS sends concurrent requests tagged with
request ids and matches responses back to the kernel threads waiting on
them. A source may process requests in any order.

Request ids are allocated per connection, strictly increasing, and
**never reused** while the connection lives — including after a
timeout. The id is allocated inside the queue lock, after the in-flight
limit has been checked, so a caller queued waiting for a slot does not
hold one yet.

`MaxConcurrentRSIRequests`, default 256, bounds how many requests may
be dispatched and awaiting a response at once. It is back-pressure for
a slow source.

## One deadline covers three waits

`RequestTimeoutMs`, default 30 seconds, is measured from the point a
kernel operation first attempts to **reserve an in-flight slot**, after
local validation and access checks have already passed. One deadline is
computed there and reused for all three legs: waiting for a slot,
waiting for the source to read the queued request, and waiting for the
response.

If the deadline expires while contending for a slot, the caller gets
`ETIMEDOUT` and **no request is sent**. If it expires after dispatch,
the caller gets `ETIMEDOUT` and late-response handling applies
(§5.8.5).

Expiry is only noticed while contending. A request that finds a slot
immediately available is dispatched even if its deadline has already
passed, and the caller then times out waiting for the answer.

## Timed-out requests keep their slot

For every dispatched request LCS keeps a **request record** until a
matching response is processed or the connection is torn down. The
record holds the request id, the operation code, the transaction id,
the key GUID it concerns, the runtime limits in force, and any retained
effect the kernel will need if the source later reports success.

When the deadline expires after dispatch, LCS detaches the waiting
caller from the record and returns `ETIMEDOUT`. **The record stays in
the in-flight table and keeps counting against
`MaxConcurrentRSIRequests`.** A timeout does not free a slot; only a
response or a teardown does.

A source that accumulates timed-out requests can therefore exhaust its
own in-flight slots until it answers or disconnects. That is the
intended shape: a source that stops answering stops being usable.

## Requests with no caller

LCS dispatches some requests with nobody waiting: `RSI_DROP_KEY` after
the last fd to an orphaned key closes (§5.2.9), and
`RSI_ABORT_TRANSACTION` cleaning up source transaction state.

Such a record occupies an in-flight slot and is retained like any
other, and its response is validated normally and released normally.
But it is **not** a late response, and the retained-effect recovery
rules do not apply to it merely because nobody is waiting.

The kernel tracks the difference explicitly, with two booleans: whether
a waiter is attached now, and whether one was ever attached. A record
that never had a caller is not a timed-out request; only one whose
caller was detached after its deadline is.

This is load-bearing rather than pedantic. `RSI_DROP_KEY` is a mutating
operation, so without the distinction a perfectly ordinary answer to a
caller-less cleanup request would look like a mutation the kernel could
not account for, and would tear the source down.

## The channel

`/dev/pkm_registry` is message-oriented. One `read()` returns exactly
one complete request; a buffer too small for the next one returns
`EMSGSIZE` **without consuming it**. An empty queue blocks, or returns
`EAGAIN` under `O_NONBLOCK`, or returns 0 if the fd is closing. One
`write()` submits exactly one complete response, and its length must
equal the response's own `total_len` exactly.

`poll` reports the fd readable when a request is queued, writable while
the slot is Active, and `POLLHUP | POLLERR` when the slot is Down or
the fd is closing. An fd that is open but has not yet registered
reports nothing at all.

Any rejected `write()` — short, over-long, an unknown or duplicate
request id, an operation code that does not match the request, a
response for another connection — returns `EINVAL` **and tears the
connection down**. A source that cannot speak the protocol correctly is
not one whose other answers are worth believing.
