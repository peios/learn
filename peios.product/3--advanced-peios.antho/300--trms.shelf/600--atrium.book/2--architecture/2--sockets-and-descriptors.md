---
title: Sockets and Descriptors
description: One socketpair per relationship, descriptors handed rather than dialed, and what the server rewrites on the way through.
---

Nothing in Atrium dials a rendezvous socket. Every internal link is a
socketpair created by the process that owns the relationship, with one
end handed down at spawn — trust is structural, and there is no path
to clean up and no peer to verify.

- **atriumd ↔ atrium-server**: one socketpair, created before the
  fork; the child finds its end on descriptor 3. It carries the control
  protocol — the login conversation relay, and the handover of each
  new session's socket. Frames are a 32-bit little-endian length
  prefix followed by one JSON document; a file descriptor, when one
  travels, rides as `SCM_RIGHTS` on the length prefix, so a frame and
  its descriptor cannot separate.
- **atriumd → atrium-session**: the session's control socket, created
  by atriumd and attached to the peinit job submission as the
  descriptor named `atrium-control`; peinit places it on descriptor 3
  of the session host. The server holds the other end.
- **atrium-server → atrium-session, per connection**: for each browser
  connection bound to a session, the server creates a fresh
  socketpair, sends one end down the session's control socket, and
  pumps the connection's bytes through the other for the connection's
  life. To a session host, "accept a connection" means "receive a
  descriptor". A websocket is the same pump; after the upgrade it is
  just bytes.

The server rewrites each forwarded request's head before replaying it:
the `Cookie` header is removed — the bearer never crosses into user
space — and two headers are added, `X-Atrium-Browser-Session` (a
random tag distinct from the cookie value, letting a session tell its
browsers apart) and `X-Atrium-Client-Addr`. A session host can trust
those headers for exactly one reason: nothing but atrium-server can
reach it. The descriptors arrive over a private socketpair, the host
listens on nothing, and that property is what the whole arrangement
leans on.

atriumd watches each session host through the pidfd that peinit
returns at submission, and reads how a session ended from peinit's job
record rather than from `wait`.
