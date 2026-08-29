---
title: Conformance
description: Every requirement of this chapter collected by role — manager, client and service — and what conformance deliberately is not.
---

## A conforming manager

**The channels.** Listens on a Unix stream socket at a well-known path
and on a Unix datagram socket whose path it gives each service in
`NOTIFY_SOCKET`. Ensures both sockets, and the directories containing
them, carry a Security Descriptor admitting the parties intended to
reach them, and relies on no POSIX mode bits (§4.3, §4.4, §4.16).

**Framing.** Emits exactly one compact JSON object per newline-terminated
frame. Answers a malformed frame with `MALFORMED_REQUEST` and an
oversized one with `REQUEST_TOO_LARGE`, closing the connection after a
frame-level failure and holding it open after a command-level one
(§4.5).

**Identity.** Obtains every client's identity from the kernel once, at
accept, and uses no UID, GID or asserted identity (§4.6).

**Authorisation.** Checks every command against the appropriate Security
Descriptor with the mappings in §4.7, records every denial, filters
`list` rather than denying it, and does not let `operation-status`
distinguish an operation the caller may not see from one that does not
exist.

**Commands.** Implements all thirteen, with the outcomes in §4.12 for
every command-and-state pair, the response shapes in §4.9, §4.14 and
§4.15, and only the error codes in §4.10. Filters `job-list` by
`JOB_QUERY` as it filters `list`, and answers `job-status` and
`job-stop` against the job's own descriptor (§4.7, §4.14).

**Operations.** Returns an identifier from every lifecycle command that
produced one and none where it did not; merges same-type requests and
returns the surviving identifier; measures every operation's lifetime
from its creation including queue time; and holds a terminal record for
at least the grace period (§4.11, §4.14).

**Waiting.** Honours the per-command `wait` default, holds a waiting
connection open past the idle timeout, and carries a `mode` on every
reload response (§4.13).

**Notification.** Authenticates every datagram through all five steps of
§4.18, including verifying the attested PID against a kernel handle and
checking the activation generation for a service's job. Applies all
lines of an accepted datagram and none of a rejected one. Rejects a
truncated datagram rather than processing it. Implements every field in
§4.19, retaining `STATUS`, `PROGRESS` and `PROGRESS_UNIT` and bounding
how often a progress change becomes an event.

**The descriptor store.** Closes rather than keeps what it refuses;
returns descriptors from 3 upward with `LISTEN_FDS`, `LISTEN_FDNAMES`
and `LISTEN_PID` set; clears the store on a deliberate stop and keeps it
across a restart the service did not ask for (§4.20).

**Extension.** Ignores unrecognised request and notification fields, and
introduces nothing from §4.21's closed list without a negotiated
version.

## A conforming client

Sends one compact JSON object per newline-terminated frame. Treats an
immediate close with no response as a refusal. Does not parse `message`.
Accepts `null` for every nullable field, and unrecognised fields
everywhere it is told to. Treats an unrecognised enumerated value or
error code as an error for that request rather than guessing. Reads
`state` rather than the presence of `error` to decide whether an
operation succeeded. Does not infer its own rights from an
`INVALID_STATE` received during shutdown. Opens a new connection to act
under a different identity.

## A conforming service

Reads `NOTIFY_SOCKET` from its environment and hardcodes no path. Sends
`READY=1` when it can genuinely serve, not when its process exists.
Sends no recognised key with an undefined value, no newline inside a
`STATUS` value, and no `PROGRESS` outside its three forms. Sends no datagram exceeding the bounds in §4.A. Expects
no reply, and no acknowledgement that a field was applied. Treats
`EXTEND_TIMEOUT_USEC` as replacing a deadline rather than adding to one.
Checks `LISTEN_PID` against its own PID before adopting any descriptor.

## What conformance is not

A system that offers neither channel is still Peios (PSPU §1.2). These
are contracts for the components that do offer them, not a bar the
platform requires anything to clear.
