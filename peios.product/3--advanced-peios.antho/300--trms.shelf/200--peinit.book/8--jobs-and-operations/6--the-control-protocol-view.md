---
title: What a Caller Sees
description: What the job and operation model looks like from outside — identifiers, waiting, and why merging is invisible to the caller.
---

Operations are how a caller observes something taking effect. This
article covers what the model looks like from the outside; the wire
contract itself is PSPU §4.

## Every lifecycle command returns an identifier

A command that creates, merges into, queues, cancels, clears or executes
an operation returns that operation's identifier. A caller can then poll
it, or block on it.

Two cases return no identifier, because no operation exists: a command
whose target is already in the state it asks for, and one that has no
effect at all — a stop on an Inactive service. Both return the service's
status instead of an acknowledgement, which is the honest answer.

Commands that never create an operation — `status`, `list`,
`operation-status` — have their own shapes.

## Waiting

Lifecycle commands block by default until the operation is terminal. The
exception is `reload`, which returns immediately unless asked otherwise,
because a reload's outcome is often advisory and a caller usually wants
the identifier rather than the wait.

A waiting connection is not idle and is never closed by the idle
timeout, however long the operation runs. It is bounded by the
operation's own lifetime instead.

## Merging is invisible

A caller whose command merged receives the surviving operation's
identifier and blocks on that operation's outcome. Nothing tells them
they merged, because there is nothing they could usefully do about it.
The consequence worth knowing is that the identifier a caller gets back
may be older than their request, and its `created_at` will be earlier
than when they sent it — which is exactly right, because that is when
the work they are waiting on actually began.

## What an operation's result carries

A completed operation carries the resulting service state. A failed one
carries the failure reason. A merged one carries the survivor's
identifier. A cancelled or aborted one carries why.

For a reload, the result also determines the reload's *mode* — whether
the service confirmed the reload with a `READY=1`, whether peinit is
merely assuming it happened, or whether it outright failed.
