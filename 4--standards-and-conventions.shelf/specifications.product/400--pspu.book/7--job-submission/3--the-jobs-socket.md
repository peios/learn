---
title: The Jobs Socket
description: The manager's sequenced-packet socket at a well-known path, why reaching it is the whole of the submission permission, and the limits placed on a connection.
---

The manager MUST listen on a Unix `SOCK_SEQPACKET` socket at a
well-known path. On Peios that path is:

```
/run/services/peinit/jobs.sock
```

The socket MUST exist for as long as the manager is serving, and the
manager MUST unlink it when it stops. The manager MUST create the
listening socket and every accepted connection with close-on-exec set,
so that no connection descriptor is inherited by a job it starts.

## Why a second socket

The control channel (§4.4) is an administrator's door: its commands
change the state of the system's services, and the descriptor on its
socket admits the principals entitled to do that. Submitting a job is
a different permission held by a different population. Any principal
may reasonably be allowed to run a program under supervision, subject
to a quota, without being allowed to stop `registryd`.

Putting the two on one socket would force one descriptor to serve both
populations. Two sockets let the filesystem say who may submit and who
may administer, separately, with no policy inside the manager.

## Why a sequenced-packet socket

A message on this channel carries more than bytes. It carries the
token a job is to run as, and the descriptors a job is to be given,
as ancillary data. The kernel associates ancillary data with the
record it was sent with, and on a stream that association is only as
precise as the reader's record boundaries. `SOCK_SEQPACKET` makes one
`send` one message and one identity (the Peios Kernel TRM §3.5), so
the manager never has to decide which request an attached token or
descriptor belongs to.

The cost is that a message has a maximum size (§7.A) and cannot be
split. A definition is small; nothing here needs to be large.

## Who may submit

**Being able to connect is the submission permission.** The manager
MUST NOT perform an access check of its own before accepting a
`submit`; the check is the one the kernel performs against the
socket's inode descriptor when the submitter connects, and the manager
relies on it entirely.

The manager MUST therefore ensure the socket, and each directory
containing it, carries a Security Descriptor admitting exactly the
principals it intends to let submit. The default a Peios service
manager applies is in §7.A. §4.3's warning applies with full force: a
socket that inherits nothing is reachable by nobody, and one in a
permissive place is reachable by anything.

What a submitter may do *to a job* is a separate question, answered by
the job's own descriptor (§7.8). Reaching the socket confers the right
to submit, and nothing else.

## A connection

A submitter connects, issues one or more messages, and closes. The
manager MUST NOT require a submitter to issue any message before
another, and MUST NOT hold state across connections beyond the jobs
themselves: a connection carries an identity (§7.5) and nothing else.

Messages on one connection MUST be answered in the order they were
received. The manager MAY read no further messages from a connection
while a response on it is outstanding.

Closing a connection MUST NOT affect any job submitted on it. A job
belongs to its submitter's identity, not to the connection that
submitted it; a submitter that reconnects — after a restart, say —
finds its jobs where it left them.

## Limits

The manager MUST enforce three limits on the channel and one on the
submitter, and MUST make their values discoverable to an administrator
through the same surface that sets them. The values a Peios service
manager uses by default are in §7.A.

**Concurrent connections.** A connection accepted while the manager is
already at its limit MUST be closed at the socket level, without a
response, and a submitter MUST treat an immediate close with no
response as a refusal rather than a protocol error.

**Message size.** A message whose content exceeds the limit MUST be
answered with `REQUEST_TOO_LARGE`. The manager MUST detect a message
the kernel truncated to fit its receive buffer (`MSG_TRUNC`) and MUST
NOT interpret the truncated content: a truncated JSON object is
malformed by construction, but a truncated attachment list is not,
and the manager MUST NOT act on a request whose attachments it did
not fully receive.

**Idle timeout.** A connection with no message outstanding MAY be
closed once it has been idle for the configured period, without a
response. A connection blocked on a `wait` (§7.8), or on a `submit`
whose job has not yet confirmed exec, is not idle and MUST NOT be
closed for idleness.

**Live jobs per submitter.** The manager MUST bound the number of live
jobs one submitter may hold, counted by the submitter's user SID, and
MUST answer a `submit` that would exceed the bound with
`QUOTA_EXCEEDED`, creating nothing. The manager MAY exempt the SYSTEM
principal (`S-1-5-18`). A job that reaches a terminal state stops
counting at once, not when its record is dropped (§7.7).
