---
title: Lifecycle Commands
description: The five commands that move a service through its state machine — none acting directly, each creating, merging into, queuing or cancelling an advisory.
---

Five commands move a service through its state machine. None of them
acts directly: each creates, merges into, queues or cancels an
**operation**, and the operation is what actually happens.

| Command | Effect | Default `wait` |
|---|---|---|
| `start` | Start the service. | true |
| `stop` | Stop the service, escalating if it does not exit. | true |
| `restart` | Stop then start, under one operation. | true |
| `reload` | Tell the service to re-read its configuration. | **false** |
| `reset` | Clear a terminal state, returning the service to inactive. | false |

`reload` defaults to not waiting because a reload's outcome is often
advisory, and a client usually wants the identifier rather than the
block. `reset` is synchronous and completes before the response is sent,
so waiting on it would mean nothing.

## Operations

The manager MUST return an operation identifier from any lifecycle
command that created, merged into, queued, cancelled, cleared or
executed an operation. The client uses it to poll (§4.14) or to
correlate.

The manager MUST NOT invent an operation solely so that it has an
identifier to return. Where a command had no effect, or the service was
already in the state asked for, the manager MUST return the status shape
instead of an acknowledgement (§4.12).

## Merging

Where an operation of the same type is already in flight for the same
service, the manager MUST merge the new request into it and MUST return
the **existing** operation's identifier.

A merged caller therefore receives an identifier that may be older than
its own request, whose `requested_at` precedes the moment it sent the
command. This is correct — that is when the work being waited on began —
and a client MUST NOT treat an identifier older than its request as an
error.

The manager MUST NOT tell the caller that a merge occurred. A merge is
not a distinguishable outcome, and a client cannot do anything with the
knowledge.

## What completion means

| Command | The operation completes when |
|---|---|
| `start` | The service reaches a dependent-satisfying state, or a state indicating its start-time conditions did not apply. |
| `stop` | The service is no longer running. |
| `restart` | The service reaches its normal successful start target after the restart. |
| `reload` | The reload resolves, whatever its mode. |
| `reset` | Immediately. |

## Timeouts

Every operation has a maximum lifetime, derived from the target
service's own configured timeouts.

**The lifetime is measured from the operation's creation, including any
time it spent queued.** From the caller's point of view they have been
waiting since they sent the command, and an operation that sat behind
another for longer than its lifetime MUST fail rather than begin.

An operation whose lifetime expires while it is still queued MUST fail,
and MUST fail its waiters. Expiry of the operation object MUST NOT by
itself authorise the manager to act on the service — a stop operation
that timed out while waiting its turn does not license signalling the
service ahead of that turn.
