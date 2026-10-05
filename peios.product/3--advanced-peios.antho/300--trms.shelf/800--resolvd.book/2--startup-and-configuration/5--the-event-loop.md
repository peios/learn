---
title: The Event Loop
description: resolvd's single thread — what it polls, how long it sleeps, the order it services ready descriptors in, and what that order means for a client.
---

## One thread and one poll [*loop.single-thread-single-poll]

resolvd runs on one thread. Every input is a descriptor in one `poll`
call, and the engine sees time only when the loop hands it the current
instant.

## What is polled

Each iteration builds the poll set afresh:

1. the native listener;
2. the stub UDP socket;
3. the stub TCP listener;
4. the netd channel, while connected;
5. the registry watch, while armed;
6. every native connection still sending its request;
7. every stub TCP connection still sending its query;
8. every upstream socket — for reading, or for writing while a TCP
   connection is still being established or its query is still being
   sent.

### The poll timeout [*loop.poll-timeout-is-earliest-deadline]

The poll timeout is the earliest of: the next upstream transaction
deadline, the next netd reconnection time while disconnected, the
moment the oldest stub TCP connection reaches its 10-second bound, and
the moment the oldest native connection reaches its 5-second bound. With
none of these pending, the loop sleeps until a descriptor is ready.

The timeout is the time to that moment in whole milliseconds, rounded
down. A moment less than a millisecond away gives a timeout of zero, so
the loop polls again without sleeping until the moment has passed.

## Service order [*loop.service-order]

After `poll` returns, ready descriptors are serviced in this order:

1. upstream sockets — replies that have arrived are answers already
   owed;
2. the stub UDP socket, reading every datagram waiting;
3. the stub TCP listener, accepting every waiting connection;
4. stub TCP connections;
5. the native listener, accepting every waiting connection;
6. native connections;
7. the netd channel;
8. the registry watch.

## Timers after descriptors [*loop.timers-run-after-descriptors]

Once the ready descriptors have been serviced, the timers run, in this
order: transactions at or past their deadline fail over to their next
attempt (§4.6), a due netd reconnection is attempted (§3.2), stub TCP
connections 10 seconds old or older are closed, and native connections
5 seconds old or older are closed.

## Answers within an iteration [*loop.local-answers-within-the-iteration]

A question that can be answered without the network — synthetic, from
the cache, or refused — is answered within the iteration that read it.

A question that needs the network sends its first transaction within
that iteration too, and is answered in the iteration that sees its
deciding reply or its last deadline.

## Writes are synchronous [*loop.replies-written-blocking]

Replies to native clients and to stub TCP clients are written from
inside the loop, in blocking mode, with a one-second timeout on each
write call. While a write is blocked, nothing else is serviced.

A reply that fits in the socket's buffer is written at once, in one
call. A reply that does not is written in as many calls as it takes: a
call that times out having sent part of the reply is followed by
another for the rest, and the write ends when the whole reply is sent
or a call fails, as one that times out having sent nothing does. Each
call blocks for at most a second, so a large reply to a client that
does not read holds the whole daemon for several seconds (§9.4): about
two on the native socket, where the first call fills the socket's
buffer and the second sends nothing, and about three on a stub TCP
connection whose send buffer is small.

Stub UDP replies and upstream queries are not written this way. The
netd subscription request is written with a two-second timeout when
the channel is opened (§3.1).
