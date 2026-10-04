---
title: The Channel
description: The admin socket, who may connect to it, and why each connection carries exactly one request.
---

## The socket

The store daemon listens on a Unix stream socket. On Peios it is
`/run/lpsd/admin.sock`.

The socket's descriptor SHOULD admit exactly those the store daemon
would (§10.3, *Who may administer*), so that a caller it would refuse is
refused at `connect` rather than after sending a request. That descriptor
is load-bearing rather than a convenience: the store daemon reads the
caller's token from the connection, and a socket open to everyone would
let anyone hold a connection open against its timeouts.

A client MUST treat a `connect` refused for permission as the store
daemon refusing it, exactly as `Denied` (§10.9).

## One request a connection

Each connection carries **one exchange**: the client sends one request,
the store daemon sends one reply, and the connection is finished. There
is no pipelining, no conversation identifier and nothing to
demultiplex. The store daemon MUST close the connection after replying,
and MUST NOT read a second request from it.

A client MUST open a connection for each request. It MUST NOT hold one
open waiting to use it later: the store daemon closes a connection that
sends nothing (below).

Every request is answered **exactly once**, with its own reply
(§10.A) or with `Failed` (§10.9). A client MUST treat a connection closed
without a reply as the request's outcome being unknown: a change MAY
have been applied. It SHOULD read the store again before telling a person
the change failed.

## Who may administer

The store daemon decides who may administer the store from the caller's
token, read from the connection, and it MUST decide before reading the
request. On Peios a caller may administer the store if its token's user
is `SYSTEM`, or if it carries `BUILTIN\Administrators` **enabled**. A
group present but deny-only grants nothing, and MUST NOT be treated as
membership.

`SYSTEM` is admitted because a machine's first account is created by a
boot-time service, before any person exists to be an administrator.

There is nothing finer. A caller that may administer the store may make
every request on this socket; one that may not, may make none. In
particular a principal may not change their own profile here. What a
principal may do about their own account is served elsewhere: their
display name and a view of their account on the self socket (§10.11),
and their password and SSH keys through PGSS Logon (PGSS §2.20 and PGSS §2.23).

A store daemon refusing a caller MUST reply `Failed` with `Denied` and
then close the connection.

## Timeouts

A store daemon SHOULD bound how long it waits for the request and how
long it spends sending the reply. On Peios each is five seconds.

A client SHOULD wait for a reply far longer than that. A request that
sets a password makes the store daemon derive a verifier, and a store
daemon that also answers PSI may serve a sign-in first; on Peios `lps`
waits thirty seconds.

## Credentials on the wire

`Add` and `SetPassword` (§10.5) carry a password in the clear. On a
kernel-mediated local socket, anything able to read those bytes could as
well read the memory of the process that typed them; what must never
travel is anything a verifier could be recomputed from, and nothing here
does. Both parties SHOULD wipe a buffer that held a password once they
are finished with it.
