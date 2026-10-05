---
title: The Event Loop
description: resolvd's single thread — what it polls, how long it sleeps, the order it services ready descriptors in, and what that order means for a client.
---

resolvd runs on one thread. Every input is a descriptor in one `poll`
call, and the engine sees time only when the loop hands it the current
instant. [*loop.single-thread-single-poll]

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

The poll timeout is the earliest of: the next upstream transaction
deadline, the next netd reconnection time while disconnected, the
moment the oldest stub TCP connection reaches its 10-second bound, and
the moment the oldest native connection reaches its 5-second bound. With
none of these pending, the loop sleeps until a descriptor is ready. [*loop.poll-timeout-is-earliest-deadline]

## Service order

After `poll` returns, ready descriptors are serviced in this order: [*loop.service-order]

1. upstream sockets — replies that have arrived are answers already
   owed;
2. the stub UDP socket, reading every datagram waiting;
3. the stub TCP listener, accepting every waiting connection;
4. stub TCP connections;
5. the native listener, accepting every waiting connection;
6. native connections;
7. the netd channel;
8. the registry watch.

Then the timers run: transactions past their deadline fail over to their
next attempt (§4.6), a due netd reconnection is attempted (§3.2), stub
TCP connections past 10 seconds are closed, and native connections past
5 seconds are closed. [*loop.timers-run-after-descriptors]

A question that can be answered without the network — synthetic, from
the cache, or refused — is answered within the iteration that read it. [*loop.local-answers-within-the-iteration]
A question that needs the network sends its first transaction within
that iteration too, and is answered in the iteration that sees its
deciding reply or its last deadline.

## Writes are synchronous

Replies to native clients and to stub TCP clients are written from
inside the loop, in blocking mode with a one-second write timeout. While
a write is blocked, nothing else is serviced. [*loop.replies-written-blocking-one-second] A reply that fits in the
socket's buffer is written at once; a large reply to a client that does
not read can hold the whole daemon for up to a second (§9.4). Stub UDP
replies and upstream queries are not written this way. The netd
subscription request is written with a two-second timeout when the
channel is opened (§3.1).
