---
title: The Self-Watch
description: LCS watches its own configuration through the same machinery userspace uses — what it drives, how it is armed, and why the callback is not the atomicity boundary.
---

LCS watches its own configuration and layer metadata subtrees, and it
does so through the same machinery userspace uses — but not through the
same interface.

An internal watch is an entry in the same watch map, taking a reference
on the same subtree watch set, distinguished only by a kind marker. It
has **no fd, no granted access mask and no filter**. Events reach it
through a kernel callback rather than being queued for a `read()`, and
it is therefore not subject to `NotificationQueueSize`. It is also not
subject to `MaxSubtreeWatchDepth`, nor to the transaction burst
suppressor: internal collection happens before either test.

Because there is no filter, deliverability is decided per target rather
than by a bitmask. Each internal target admits only the event types it
cares about: value events on the watched key itself for the
configuration subtrees, and subkey events at depth 0 or value and
descriptor events at depth 1 for the layer metadata subtree.

## What it drives

**Self-configuration.** A change under `Machine\System\Registry\`
triggers a re-read and validation of the parameters (§5.10.3).

**The layer table.** A change under `Machine\System\Registry\Layers\`
marks the affected layer names dirty and drives a bounded refresh of
their precedence, enabled state, owner and cached descriptor.

**Layer lifecycle.** `SUBKEY_CREATED` and `SUBKEY_DELETED` under
`Layers\` add and remove layers, except for `base`, which is ignored
(§5.3.2).

**KMES configuration.** A third internal watch, on
`Machine\System\KMES\`, exists for KMES's own parameters. It is not
LCS configuration, but the registry is where it lives and this is the
mechanism that notices it change.

## The callback is not the atomicity boundary

For layer metadata, internal delivery identifies which layer names are
dirty. It does not itself publish anything, and it must not: publishing
a layer means publishing its table entry, metadata key GUID and cached
descriptor together (§5.3.3), and a callback that published a partial
entry would create a window in which a layer exists and nobody can be
authorised against it.

LCS also does not perform source round trips while holding the
watch-map or layer-table publication locks. The refresh runs outside
them, after the mutating operation commits and before the syscall
returns.

## Arming

At bootstrap, LCS resolves the GUIDs for `Machine\System\Registry\` and
`Machine\System\Registry\Layers\` through `RSI_LOOKUP` and arms
targeted subtree watches. If either does not exist — first boot, empty
database — it arms a subtree watch on the `Machine\` hive root instead,
so that seed restore creating the subtree is noticed. That fallback
event re-enters the whole bootstrap refresh, which resolves the
specific GUIDs and arms the targeted watches.

In practice the kernel arms both: targeted watches for whichever roots
exist, **plus** the `Machine\` root fallback, until a refresh finds
everything present. It is a superset of what is needed rather than a
substitute for it.

## Bootstrap interaction

1. A source registers. LCS reads `Machine\System\Registry\*`; the keys
   do not exist; compiled-in defaults are retained.
2. Seed restore populates them. The subtree watch fires, LCS validates
   and hot-swaps to the seed values.
3. Subsequent administrative changes fire the watch again, and LCS
   validates and hot-swaps, or rejects with an audit event.

At no point is there a state in which LCS is waiting for
configuration.
