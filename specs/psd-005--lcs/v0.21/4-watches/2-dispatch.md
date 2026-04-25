---
title: Watch Dispatch
---

This section defines how LCS determines which watches are affected
by a mutation and delivers events to them.

## Watch semantics

**Object-semantic, not path-semantic.** A watch is attached to a
key fd, which references a specific key object (GUID). The watch
fires for changes to that object. If a layer change causes a
different key to become visible at the same path, the watch does
NOT transfer to the new key -- it stays on the original object.

To watch the new key, the process must detect the change (via a
parent subtree watch or a KEY_DELETED event on the old object),
re-open the path, and arm a new watch. This is consistent with the
fd model: the fd is a capability bound to a specific key identity.

**One watch per fd.** Each key fd has at most one active watch.
Calling REG_IOC_NOTIFY on an already-armed fd replaces the previous
filter and subtree settings. To watch the same key with different
filters, open it twice. Calling REG_IOC_NOTIFY with a filter of
zero disarms the watch -- pending events are discarded and no
further events are queued.

**Key re-emergence.** If a watched key is hidden (KEY_DELETED
delivered) and the hiding layer is later removed, the key reappears
at its original path. Because the watch is GUID-bound and the GUID
has not changed, the watch resumes receiving events for the
re-emerged key. No explicit re-emergence event is defined -- the
watcher observes the key's continued activity (value changes,
subkey changes) as normal events after the hiding layer is removed.

**Arming.** A watch is armed by calling REG_IOC_NOTIFY on a key fd.
The ioctl takes:

- **Filter:** A bitmask of event types to receive. Events not
  matching the filter are not queued.
- **Subtree flag:** Watch this key only, or this key and
  descendants up to MaxSubtreeWatchDepth levels deep (default 0 =
  unlimited, all descendants).

**Pollable fd.** An armed key fd is pollable via epoll/poll/select.
EPOLLIN indicates pending events. read() returns one or more
structured event records.

## Kernel data structures

LCS maintains two data structures for dispatch:

1. **Watch map.** A hash map from GUID to a list of armed watchers
   (direct watches on that GUID). When a mutation occurs on key B,
   LCS looks up B's GUID in the watch map and fires matching
   watchers. O(1) lookup.

2. **Subtree watch set.** A hash set of GUIDs that have at least
   one active subtree watch. Used for ancestor chain matching.

## Ancestor chain

When a key is opened, LCS resolves the path component by component
via RSI Lookup, collecting the GUID at each level. This ancestor
chain (root GUID → ... → parent GUID → key GUID) is stored on the
key fd at open time.

The ancestor chain is a byproduct of path resolution -- it requires
no additional RSI queries. It is bounded by tree depth (typically
< 20 GUIDs). For keys opened through symlinks, the ancestor chain
reflects the resolved path (the target key's actual position in
the tree), not the symlink path.

For keys opened via relative open (parent fd + relative path), the
ancestor chain is the parent fd's ancestor chain extended with the
GUIDs resolved during the relative path walk.

## Dispatch algorithm

When a mutation occurs on key B (via a key fd whose ancestor chain
is known):

```
// Map event type codes to filter categories.
// KEY_DELETED and OVERFLOW are always delivered regardless of filter.
event_category(event_type):
    if event_type == VALUE_SET or event_type == VALUE_DELETED:
        return REG_NOTIFY_VALUE
    if event_type == SUBKEY_CREATED or event_type == SUBKEY_DELETED:
        return REG_NOTIFY_SUBKEY
    if event_type == SD_CHANGED:
        return REG_NOTIFY_SD
    if event_type == KEY_DELETED or event_type == OVERFLOW:
        return 0  // always delivered

matches_filter(event_type, filter):
    category = event_category(event_type)
    return category == 0 or (filter & category) != 0

dispatch(key_b_guid, ancestor_chain, event_type, event_data):
    // Step 1: Fire direct watches on B
    watchers = watch_map.get(key_b_guid)
    if watchers is not None:
        for watcher in watchers:
            if matches_filter(event_type, watcher.filter):
                enqueue(watcher, event_type, event_data, path_depth=0)

    // Step 2: Walk ancestor chain for subtree watches
    for ancestor_guid in reversed(ancestor_chain):
        if ancestor_guid == key_b_guid:
            continue  // already handled in step 1
        if ancestor_guid not in subtree_watch_set:
            continue  // no subtree watches here, skip
        watchers = watch_map.get(ancestor_guid)
        if watchers is not None:
            for watcher in watchers:
                if not watcher.subtree:
                    continue  // direct watch, not interested
                if matches_filter(event_type, watcher.filter):
                    path = build_relative_path(ancestor_chain, ancestor_guid, key_b_guid)
                    enqueue(watcher, event_type, event_data, path)
```

**Cost per mutation:** O(depth) hash lookups against the subtree
watch set. Depth is bounded by tree structure. No RSI round trips.
No trie. No string matching. The ancestor chain was captured at
open time and hash lookups are O(1) each.

## Transaction batching

When a transaction commits, all changes within the transaction
generate their events as a batch. Events are ordered by the
sequence in which operations were performed within the transaction.
The watcher sees the full set of changes atomically -- no
interleaving with events from other operations between the batch
members.

If the number of events generated for a single watcher from one
transaction commit exceeds MaxTransactionWatchEventBurst (default
4096), LCS stops generating individual events and inserts a single
OVERFLOW event instead. This prevents a large transaction (e.g.,
role installation writing thousands of values) from atomically
filling a watcher's queue.

Aborted transactions generate no events.

## Source restart behaviour

When a source disconnects and re-registers, LCS cannot determine
what changed while the source was down. OVERFLOW is delivered on
**re-registration**, not on disconnect. This ensures watchers can
successfully re-read state when they receive the OVERFLOW (the
source is available). During the window between disconnect and
re-registration, watches remain armed but no events are delivered.
Operations on watched keys return EIO during this window.

Watches remain armed across source restarts. The persistent watch
model means watchers do not need to re-arm after a source restart.

## Queue management

Each armed key fd has an event queue with a configurable maximum
size (NotificationQueueSize, default 256 events). When the queue
is full and a new event arrives:

1. The oldest event in the queue is dropped.
2. An OVERFLOW event is inserted if one is not already present.
3. Subsequent events continue to be queued normally.

The maximum queue size is configurable via the self-configuration
mechanism (§8.2).

### Memory bounding

Each watch queues at most the configured maximum events. Each
process can hold at most RLIMIT_NOFILE fds (and therefore at most
that many watches). The combination of per-queue limits and
per-process fd limits provides kernel memory exhaustion protection
without a registry-specific global cap.
