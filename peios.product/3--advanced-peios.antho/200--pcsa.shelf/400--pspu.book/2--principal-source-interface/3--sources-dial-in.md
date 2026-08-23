---
title: Sources Dial In
description: The authority never dials a source; sources connect inward. The most consequential shape decision in the chapter, and what it buys.
---

**The authority listens. Sources connect to it.** The authority never
initiates a connection to a source.

This is the most consequential shape decision in this chapter, and it is
worth being explicit about what it buys.

## Why the direction matters

The authority holds the privilege to mint tokens. It is the most
privileged userspace process on the system. An authority that dialled
out would need, in its configuration, a list of paths to connect to —
and a process holding that privilege having a configurable list of
things to go and talk to is a liability out of proportion to the
convenience.

Because sources connect inward, the authority's sockets are
`accept()`-only. It never opens an outbound connection to anything, for
any reason.

## What follows

**Restart is the source's problem.** A source whose connection drops
reconnects. The authority does not retry, does not queue, and does not
track sources it has not heard from. A source that has gone away is
simply not registered.

**A source is not required to exist.** An authority with no registered
sources cannot authenticate anybody, and that is a coherent state rather
than an error — it means no identity has been made available to it yet.

**Ordering is the init system's problem.** The authority must be
listening before a source can register, and a service that depends on
authentication must start after a source has. Expressing that is a
service-ordering question, not a protocol one, and this chapter says
nothing about it.

> [!NOTE]
> A source SHOULD report itself ready only once its registration has
> been *acknowledged*, so that "the source is running" and "the source
> can authenticate" are the same statement to anything ordered after it.
> This is what makes the `Registered` acknowledgement load-bearing
> despite carrying almost nothing.
