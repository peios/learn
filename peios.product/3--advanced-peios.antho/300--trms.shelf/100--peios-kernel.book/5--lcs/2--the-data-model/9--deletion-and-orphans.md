---
title: Deletion and Orphans
description: Deletion works on two levels because naming and identity are separate — layer deletion, orphaned keys, and what happens to their watches.
---

Deletion operates on two levels, because naming and identity are
separate things.

## Deleting a key

`REG_IOC_DELETE_KEY` removes **one layer's path entry**. The key's data
— its GUID, descriptor and values — is untouched; only a name is
removed. LCS derives the parent GUID from the fd's ancestor chain and
the child name from the last component of its resolved path, and sends
`RSI_DELETE_ENTRY`.

If path entries remain in other layers, the key is still visible
through them. If none remain anywhere, the key is orphaned.

A key with **visible children** cannot be deleted: `ENOTEMPTY`.
Visibility is evaluated globally, across all enabled layers, and
deliberately ignores the caller's private layer set — so whether a
deletion succeeds does not depend on who is asking. Recursive deletion
is a client-side tree walk, not a kernel primitive.

Deleting a key does not delete its values. Values belong to the GUID,
not to the path entry, and go when the GUID goes.

Hive roots cannot be deleted or hidden (§5.2.5).

## Layer deletion

Deleting a layer removes all of its path entries, value entries and
blanket tombstones, across every source. LCS broadcasts
`RSI_DELETE_LAYER` and each source returns the GUIDs that lost their
last path entry as a result.

Effects on live state follow from the model with no special cases: keys
named only by that layer become orphaned; where the layer held the
winning value entry, the next layer's value becomes effective; blanket
tombstones it held are removed and unmask what they were hiding; and
Security Descriptors are unchanged, because they were never layered.

Watchers are notified by whatever recovery mechanism applies —
per-key events for the orphaned keys, and a source-wide `OVERFLOW` for
the rest (§5.6.3).

Before sending `RSI_DELETE_LAYER`, LCS aborts every bound transaction
whose mutation log touched that layer. Otherwise a transaction could
commit writes into a layer that no longer exists. Those transactions
return `EINVAL` on their next operation or commit attempt.

Layer deletion is what role uninstallation and Group Policy removal
are.

## Orphaned keys

An orphaned key is a GUID with no path entry in any layer. It follows
the Linux unlink model: alive but unnamed.

Existing fds keep working. Operations that address the key by GUID
proceed normally:

- querying, setting and deleting values;
- setting and removing blanket tombstones;
- querying and setting the Security Descriptor;
- querying key metadata;
- flushing the key's hive;
- closing the fd.

Namespace operations return `ENOENT`:

- creating a child key under it;
- opening or creating anything relative to it;
- deleting its path entry;
- hiding it;
- backing it up.

The reason is that an orphaned key is no longer a reachable subtree
root. Allowing new names beneath an unnamed key would build a subgraph
nothing can reach.

## Watches on an orphaned key

A watch armed before the key was orphaned stays armed, and the
transition delivers `KEY_DELETED`. After that the watch may still
observe GUID-local changes made through the surviving fds, though the
subtree is no longer expanded through the orphaned key.

Arming a *new* watch on an already-orphaned key is `ENOENT`. Re-arming
one that is already armed is allowed.

## Dropping the GUID

When the last fd to an orphaned key closes and the source is Active,
LCS sends `RSI_DROP_KEY`, which purges the key record, every value
entry across every layer, and any remaining blanket tombstones. It is
dispatched **before** the in-kernel key state is released.

The request is asynchronous: nothing waits for the answer, and a valid
response is processed as an ordinary response rather than as a late
one (§5.8.5). That distinction is load-bearing — `RSI_DROP_KEY` is a
mutating operation, and without it the arrival of a perfectly normal
answer to a caller-less request would look like an unaccounted
mutation and tear the source down.

If the source is Down, LCS releases its in-kernel state and does **not**
queue a deferred drop. There is no deferred-drop queue. Recovering the
key record then falls to the source's own startup obligation to purge
records with no path entries before it becomes Active (§5.8.2).

`close()` never reports orphan cleanup failure to userspace, and never
can: it returns 0 unconditionally.

## A new key at the same path

A layer can create a new key where another layer's key already exists.
Each layer has its own path entry pointing at its own GUID, and
resolution decides which is visible.

Fds referencing the other GUID are completely isolated from it:
different identity, different data, different value entries. Nothing
observable connects two keys that merely share a name.
