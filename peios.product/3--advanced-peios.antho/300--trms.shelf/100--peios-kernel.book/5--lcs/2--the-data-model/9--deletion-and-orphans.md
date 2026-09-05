---
title: Deletion and Orphans
description: Deletion works on two levels because naming and identity are separate — layer deletion, orphaned keys, and what happens to their watches.
---

Deletion operates on two levels, because naming and identity are
separate things.

## Deleting a key

`REG_IOC_DELETE_KEY` removes **one layer's path entry**. The key's data
— its GUID, descriptor and values — is untouched; only a name is
removed. [*orphan.delete-key.removes-one-layer-path-entry]

LCS derives the parent GUID from the fd's ancestor chain and the child
name from the last component of its resolved path, and sends
`RSI_DELETE_ENTRY`. [*orphan.delete-key.parent-and-name-derived-from-the-fd]

If path entries remain in other layers, the key is still visible
through them. [*orphan.delete-key.remaining-entries-keep-the-key-visible]

If none remain anywhere, the key is orphaned. [*orphan.delete-key.last-entry-removed-orphans-the-key]

A key with **visible children** cannot be deleted:
`ENOTEMPTY`. [*orphan.delete-key.visible-children-is-enotempty]

Visibility is evaluated globally, across all enabled layers, and
deliberately ignores the caller's private layer set — so whether a
deletion succeeds does not depend on who is asking. [*orphan.delete-key.visibility-ignores-the-callers-private-layers]

Recursive deletion is a client-side tree walk, not a kernel
primitive. [*orphan.delete-key.no-recursive-delete-primitive]

Deleting a key does not delete its values. Values belong to the GUID,
not to the path entry, and go when the GUID goes. [*orphan.delete-key.values-survive-entry-deletion]

Hive roots cannot be deleted or hidden (§5.2.5).

## Layer deletion

Deleting a layer removes all of its path entries, value entries and
blanket tombstones, across every source. [*orphan.layer-delete.removes-every-entry-across-all-sources]

LCS broadcasts `RSI_DELETE_LAYER` and each source returns the GUIDs
that lost their last path entry as a
result. [*orphan.layer-delete.sources-report-newly-orphaned-guids]

Effects on live state follow from the model with no special cases:

- keys named only by that layer become
  orphaned; [*orphan.layer-delete.keys-named-only-by-it-become-orphaned]
- where the layer held the winning value entry, the next layer's value
  becomes effective; [*orphan.layer-delete.next-layers-value-becomes-effective]
- blanket tombstones it held are removed and unmask what they were
  hiding;
- and Security Descriptors are unchanged, because they were never
  layered. [*orphan.layer-delete.security-descriptors-unchanged]

Watchers are notified by whatever recovery mechanism applies —
per-key events for the orphaned keys, and a source-wide `OVERFLOW` for
the rest (§5.6.3).

Before sending `RSI_DELETE_LAYER`, LCS aborts every bound transaction
whose mutation log touched that layer. [*orphan.layer-delete.aborts-transactions-touching-the-layer] Otherwise a transaction could
commit writes into a layer that no longer exists.

Those transactions return `EINVAL` on their next operation or commit
attempt. [*orphan.layer-delete.aborted-transactions-return-einval]

Layer deletion is what role uninstallation and Group Policy removal
are.

## Orphaned keys

An orphaned key is a GUID with no path entry in any layer. It follows
the Linux unlink model: alive but unnamed. [*orphan.definition.guid-with-no-path-entry-anywhere]

Existing fds keep working. Operations that address the key by GUID
proceed normally:

- querying, setting and deleting values; [*orphan.allowed.value-operations]
- setting and removing blanket tombstones; [*orphan.allowed.blanket-tombstone-operations]
- querying and setting the Security Descriptor; [*orphan.allowed.security-descriptor-operations]
- querying key metadata; [*orphan.allowed.query-key-metadata]
- flushing the key's hive; [*orphan.allowed.flush-the-hive]
- closing the fd. [*orphan.allowed.close-the-fd]

Namespace operations return `ENOENT`:

- creating a child key under it; [*orphan.refused.create-a-child-key]
- opening or creating anything relative to it; [*orphan.refused.relative-open-or-create]
- deleting its path entry; [*orphan.refused.delete-its-path-entry]
- hiding it; [*orphan.refused.hide-it]
- backing it up. [*orphan.refused.back-it-up]

The reason is that an orphaned key is no longer a reachable subtree
root. Allowing new names beneath an unnamed key would build a subgraph
nothing can reach.

## Watches on an orphaned key

A watch armed before the key was orphaned stays armed, and the
transition delivers `KEY_DELETED`. [*orphan.watch.stays-armed-and-delivers-key-deleted]

After that the watch may still observe GUID-local changes made through
the surviving fds, though the subtree is no longer expanded through the
orphaned key. [*orphan.watch.still-sees-guid-local-changes]

Arming a *new* watch on an already-orphaned key is
`ENOENT`. [*orphan.watch.arming-a-new-watch-is-enoent]

Re-arming one that is already armed is allowed. [*orphan.watch.re-arming-an-armed-watch-is-allowed]

## Dropping the GUID

When the last fd to an orphaned key closes and the source is Active,
LCS sends `RSI_DROP_KEY`, which purges the key record, every value
entry across every layer, and any remaining blanket
tombstones. [*orphan.drop.last-close-sends-rsi-drop-key]

It is dispatched **before** the in-kernel key state is
released. [*orphan.drop.dispatched-before-state-is-released]

The request is asynchronous: nothing waits for the answer, and a valid
response is processed as an ordinary response rather than as a late
one (§5.8.5). [*orphan.drop.request-is-asynchronous] That distinction is load-bearing — `RSI_DROP_KEY` is a
mutating operation, and without it the arrival of a perfectly normal
answer to a caller-less request would look like an unaccounted
mutation and tear the source down.

If the source is Down, LCS releases its in-kernel state and does **not**
queue a deferred drop. There is no deferred-drop
queue. [*orphan.drop.down-source-queues-no-deferred-drop] Recovering the
key record then falls to the source's own startup obligation, under
the Registry Source Interface specification in PSPK, to purge records
with no path entries before it becomes Active.

`close()` never reports orphan cleanup failure to userspace, and never
can: it returns 0 unconditionally. [*orphan.drop.close-always-returns-zero]

## A new key at the same path

A layer can create a new key where another layer's key already exists.
Each layer has its own path entry pointing at its own GUID, and
resolution decides which is visible.

Fds referencing the other GUID are completely isolated from it:
different identity, different data, different value entries. Nothing
observable connects two keys that merely share a name. [*orphan.same-path.fds-to-the-other-guid-stay-isolated]
