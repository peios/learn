---
title: Dispatch
description: Given a mutation, which armed watches hear about it — computed from object identity and ancestry, with depth, batching and recovery.
---

Dispatch answers one question: given a mutation on a key, which armed
watches hear about it? The answer is computed from object identity and
from ancestry captured at open time, never from a path string resolved
at the moment of the event.

## A watch is bound to an object

A watch is registered against the GUID on the fd it was armed through.
It fires for changes to *that object*. If a layer change causes a
different key to become visible at the same path, the watch does not
move: the new key is a different object with a different GUID, and
nothing about the old watch refers to a name.

To follow the path rather than the object, a process detects the change
— through `KEY_DELETED` on the old object, or a subtree watch on the
parent — re-opens the path, and arms a new watch. This is the fd model
applied consistently: an fd is a capability bound to one identity.

The converse also holds. If a watched key is hidden, `KEY_DELETED` is
delivered, but the watch is not removed. Should the hiding layer later
be deleted, the key reappears at its original path with the same GUID,
and events resume. There is no re-emergence event; the watcher simply
observes the key being active again.

## The ancestor chain

Subtree dispatch needs to know where a key sits in the tree, and it
learns that once, at open.

Resolving a path walks it component by component, and the GUID at each
level is retained on the resulting fd as the **ancestor chain** —
root GUID through parent GUID to the key itself. It costs nothing
extra: the walk had to resolve those components anyway. A relative open
copies the parent fd's chain and extends it with the components the
relative walk resolved. An open that followed a symlink records the
chain of the *resolved* path, so the fd's ancestry reflects the target's
real position in the tree, not the link's.

Dispatch uses that captured chain and never re-resolves it. If an
ancestor in the chain is later hidden, deleted, orphaned, or replaced
at the same path by a different key, watches on the original ancestor
GUID still receive subtree events from descendants mutated through fds
opened through that chain. Watches on a new key that later appears at
the same path receive nothing from the old one.

## The algorithm

Two structures back dispatch. The **watch map** is a hash map from GUID
to the watchers armed on it. The **subtree watch set** is a refcounted
hash set of the GUIDs that have at least one subtree watch, maintained
as watches are armed, re-armed, disarmed and closed.

For a mutation on key *B*, with *B*'s ancestor chain in hand:

1. Look up *B*'s GUID in the watch map and queue the event, with
   `path_depth` 0, to every watcher whose filter admits it.
2. Walk the ancestor chain outward from *B*'s parent. At each ancestor,
   skip it unless it is in the subtree watch set — that test is what
   makes the walk cheap. For an ancestor that is, queue the event to
   each of its watchers that armed with the subtree flag and whose
   filter admits it, with the path from that ancestor down to *B*.

The cost is O(depth) hash lookups, with no RSI round trips, no trie and
no string comparison. The path components handed to a subtree watcher
are sliced out of the resolved path already stored on the mutating fd.

Dispatch runs under a single global registry lock, so it is serialised
across the whole system rather than per hive or per source.

## Depth

`MaxSubtreeWatchDepth` bounds how far below a watched key a subtree
watch is told about. The default is 0, meaning unlimited. A non-zero
value suppresses events whose path is longer than it, limiting both
noise and dispatch cost for a watch armed high in a tree.

The limit applies to watches held by userspace. LCS's own internal
watches are collected before the depth test and are not subject to it
(§5.10.4).

## Transaction batches

Nothing inside an uncommitted transaction dispatches. At commit, and
only when the source reports success, the transaction's mutation log is
walked in operation order and the whole set of events is queued as one
batch, under a single hold of the registry lock, so no other operation
interleaves with it. An aborted, failed or timed-out transaction
dispatches nothing and its log is released.

A large transaction — a role installation writing thousands of values —
could otherwise fill a watcher's queue atomically. So the batch is
counted per watcher first: any watcher whose share exceeds
`MaxTransactionWatchEventBurst`, default 4096, receives exactly one
`OVERFLOW` and none of its individual events. That `OVERFLOW` is queued
ahead of the batch, so it arrives before whatever else that watcher is
still owed.

## Recovery dispatch

Some changes alter effective state for keys whose fds nobody holds and
whose descendants the kernel is retaining no context for. Deleting a
layer, changing its precedence, enabling or disabling it, and restoring
a subtree from a stream are all of this kind. Computing an exact diff
would mean walking arbitrary parts of the tree through the source.

LCS does not attempt it. It increments the affected hive's generation
number and then queues a no-name `OVERFLOW` to every armed watch on the
affected source, which is the notification for those changes. The
watcher re-reads, and can compare the generation number it last saw
against the current one (§5.5.3) to tell whether it missed anything.

Two properties of this delivery are worth stating. It is object-
semantic like every other dispatch — it walks the watch map, resolves
no paths — and it bypasses the filter, because `OVERFLOW` always does.
It does not disarm anything.

The scope is the **source**, not the hive. A source backing several
hives delivers `OVERFLOW` to watches on all of them, including hives
the operation did not touch. The generation counters are maintained per
hive; the watch delivery is not.

For a restore, recovery is published only after the source commit
succeeds. A restore that fails or aborts before commit emits nothing.

## Source restart

When a source disconnects, watches stay armed and nothing is delivered;
operations needing the source return `EIO`. `OVERFLOW` arrives on
**re-registration**, not on disconnect, which is the only ordering that
works: a watcher told to re-read needs the source to be there when it
does. Existing fds resume without re-opening, and no watcher has to
re-arm.
