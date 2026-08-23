---
title: The Control Channel
description: The manager's stream socket at a well-known path, what a connection is, and the limits placed on one.
---

The manager MUST listen on a Unix `SOCK_STREAM` socket at a
well-known path. On Peios that path is:

```
/run/services/peinit/control.sock
```

The socket MUST exist for as long as the manager is serving, and the
manager MUST unlink it when it stops.

The manager MUST create the listening socket and every accepted
connection with close-on-exec set, so that no connection descriptor is
inherited by a process the manager starts.

## A connection

A client connects, issues one or more commands, and closes. The manager
MUST NOT require a client to issue any command before another, and MUST
NOT hold state across connections: a connection carries an identity
(§4.6) and nothing else.

Requests on one connection MUST be answered in the order they were
received. The manager MAY read no further frames from a connection while
a response on it is outstanding.

## Limits

The manager MUST enforce three limits, and MUST make their values
discoverable to an administrator through the same configuration surface
that sets them. The values a Peios service manager uses by default are
in §4.A.

**Concurrent connections.** A connection accepted while the manager is
already at its limit MUST be closed at the socket level, without a
response. There is no error code for this condition: the manager has
declined to enter the protocol at all, and a client MUST treat an
immediate close with no response as a refusal rather than as a protocol
error.

**Request size.** A request frame whose content exceeds the limit MUST
be answered with `REQUEST_TOO_LARGE` and the connection MUST then be
closed. The limit applies to the frame's content and MUST NOT count the
terminating newline, so a request of exactly the limit plus its newline
is within bounds.

**Idle timeout.** A connection with no request outstanding MAY be closed
once it has been idle for the configured period. The manager MUST NOT
treat a connection as idle while a request on it is outstanding — in
particular a connection blocked on a `wait=true` operation (§4.13) is
not idle, however long the operation runs, and MUST be held open until
the operation resolves. Such a connection is bounded by the operation's
own timeout, not by the idle timeout.

A connection closed for idleness MUST be closed without a response.
