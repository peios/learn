---
title: Queues and Overflow
description: Each armed fd has its own bounded queue and delivery is best-effort — what a full queue does, and what a watcher does about it.
---

Each armed fd has its own event queue, bounded by
`NotificationQueueSize` — default 256 events, configurable between 16
and 65536 (§5.10.3).

Delivery is best-effort. A watcher that reads promptly sees every
change; one that falls behind is told that it has, rather than being
given a partial history it cannot distinguish from a complete one.

## What happens when the queue is full

When an event arrives for a full queue and no `OVERFLOW` is present:

1. The oldest queued event is dropped.
2. An `OVERFLOW` record is queued in its place.
3. The event that triggered this is **discarded**, not queued.

Once an `OVERFLOW` is in the queue, subsequent events queue normally:
the oldest non-`OVERFLOW` event is dropped to make room and the new
event is added, so the single `OVERFLOW` is preserved and the queue
continues to carry the most recent history behind it.

A queue therefore holds at most one `OVERFLOW` at a time, and that is
an enforced invariant rather than a convention — an attempt to queue a
second is rejected as a bug.

## What a watcher does about it

`OVERFLOW` means the record it has is incomplete. There is no way to
learn what was dropped, and no attempt is made to describe it. The
watcher re-reads the watched key, and its subtree if the watch is a
subtree watch, and continues from the state it finds. Events after the
`OVERFLOW` are complete again.

`REG_IOC_QUERY_KEY_INFO` reports a per-hive generation number
(§5.5.3) that makes this cheaper than it sounds: a watcher that
recorded the generation at its last full read can compare it with the
current one and skip the re-read entirely if nothing committed in
between.

## Memory

There is no registry-specific global cap on watch memory, and none is
needed. A watch costs at most `NotificationQueueSize` queued events, a
watch requires an fd, and a process holds at most `RLIMIT_NOFILE` fds.
The product of the two is the bound, and it is enforced by machinery
that already exists.

The same reasoning covers open key state: per-fd overhead — GUID,
granted mask, ancestor chain, watch state — multiplied by the fd limit.

LCS's own internal watches are outside this. They are delivered
synchronously through a kernel callback rather than queued, so the
queue limit does not apply to them (§5.10.4).
