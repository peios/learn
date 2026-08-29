---
title: The Control Socket
description: The Unix stream socket every runtime command arrives on — how it is created and protected, and the peer token it captures.
---

peinit serves every runtime command on a Unix stream socket at
`/run/services/peinit/control.sock`, created during Phase 1
infrastructure setup and existing for the lifetime of the system. Its
wire protocol is specified in PSPU §4; this chapter is how peinit
implements its side. A second socket beside it, the jobs socket, is the
door for submitting jobs rather than administering services; it is
§10.7.

## Creation and protection

The socket is created with `SOCK_CLOEXEC | SOCK_NONBLOCK` and a listen
backlog of 32, and unlinked when peinit drops it. Accepted connections
come from `accept4` with both flags, so no connection descriptor is ever
inherited by a service.

peinit sets **no POSIX mode bits** on the socket, on the notification
socket, or on anything else it creates. Under KACS, mode bits are not
what governs access — a Security Descriptor is — so setting them would
be inert.

What governs access is the descriptor on the socket inode, which the
kernel checks at `connect()` before any peer identity is established.
peinit creates `/run/services/peinit/` and stamps the control socket
explicitly, after binding and before anything can connect:

```
O:SYG:SYD:(A;;GA;;;SY)(A;;GA;;;BA)
```

The notification socket inherits the `/run` seed of §2.3, which grants
the same two principals. The jobs socket carries a broader descriptor
of its own, because reaching it is a different permission (§10.7).

## Connections

peinit accepts a connection, obtains the peer's token, and only then
admits it against the connection limit:

| Key | Default | Meaning |
|---|---|---|
| `Machine\System\Init\MaxControlConnections` | 32 | Concurrent connections. |
| `Machine\System\Init\MaxRequestSize` | 65536 | Maximum request size, in bytes. |
| `Machine\System\Init\ConnectionTimeout` | 30 | Seconds before an idle connection is closed. |

A connection over the limit is closed at the socket level, before any
request is read and without a response — there is no error code for it,
because there is no protocol state in which to deliver one. A peer whose
token cannot be obtained is closed the same way.

The jobs socket has its own three, under `Machine\System\Init\`:
`MaxJobsConnections` (64), `MaxJobMessageSize` (65536) and
`JobsConnectionTimeout` (30), plus a fourth bound that is the
submitter's rather than the connection's, `MaxJobsPerSubmitter` (64).
All four are read at boot and on reload-config, and are listed with the
other operational keys in the registry key reference.

## The peer token

The token is read **once**, when the connection is accepted, through
the kernel's peer-token socket option (`getsockopt(SOL_KACS,
KACS_SO_PEER_TOKEN)`; the Peios Kernel TRM §3.5). It is the identity the
peer thread was acting under when it connected, so a peer that was
impersonating is captured as the impersonated identity — which is what
makes access decisions reflect the identity a client is actually
operating under rather than its underlying service identity.

Because it is captured once, a peer that changes identity mid-connection
is still evaluated against the identity it connected with.

## Idle and waiting

A connection is idle only when it has nothing in flight. One blocked on
a `wait=true` operation, on a `job-stop` with `wait`, or with output
still buffered, is never idle and is never closed by
`ConnectionTimeout` — it stays open until the operation or job
resolves, bounded by the operation's own timeout rather than the
connection's. A job wait has no timeout of its own; it is bounded by
the job.

peinit handles one frame per readiness turn, and reads no further frames
from a connection while a wait is pending on it. Pipelined requests are
therefore serialised behind a wait.

## Timestamps

Every timestamp peinit puts on the wire is derived by projecting a
monotonic event stamp through the current offset between the realtime
and monotonic clocks. Elapsed-time decisions stay monotonic; only the
presentation is wall-clock.
