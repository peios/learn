---
title: Deletion
order: 8
---

Key deletion operates on two levels: path entries (per-layer naming)
and key data (identity and properties).

## Explicit deletion

When a process deletes a key via syscall, LCS removes the path
entry for the specified layer. The key's data (GUID, SD, values)
is not affected -- only the naming is removed.

If the key still has path entries in other layers, those remain.
The key is still visible through those layers.

If no path entries remain across any layer after the deletion, the
key is orphaned.

## Layer deletion

When a layer is deleted, all its path entries and value entries
are removed across all sources. LCS broadcasts the deletion to
all registered sources.

Any GUIDs that lose their last path entry (across all layers) are
orphaned. Values that were the highest-precedence entry for their
name are removed, and the next-highest-precedence entry becomes
effective. Blanket tombstones held by the deleted layer are removed,
unmasking lower-precedence values.

Layer deletion is the mechanism for role uninstallation and Group
Policy removal.

**Interaction with transactions.** Before sending RSI_DELETE_LAYER,
LCS MUST abort all bound transactions that have written to the
layer being deleted. This prevents stale writes from being
committed into a deleted layer after RSI_DELETE_LAYER completes.
Affected transactions receive EINVAL on their next operation or
commit attempt.

## Orphaned keys

An orphaned key is a GUID with no path entries in any layer. It
follows the Linux unlink model:

- Existing fds to the orphaned key continue to work. Reads, writes,
  and enumeration operate normally against the key's GUID.
- The key is alive but unnamed -- no new opens can reach it by path.
- When the last fd closes, LCS tells the source to drop the GUID
  via RSI_DROP_KEY.

RSI_DROP_KEY removes all data associated with the GUID: the key
record, all value entries across all layers, and any remaining path
entries that might reference it.

## RSI deletion operations

The deletion model maps to three RSI operations:

- **RSI_DELETE_ENTRY(parent_GUID, child_name, layer):** Remove a
  specific layer's path entry. The key's data remains, keyed by
  GUID. Used for explicit key deletion.

- **RSI_DROP_KEY(GUID):** Remove all data associated with the GUID.
  Called by LCS when an orphaned key's last fd closes.

- **RSI_DELETE_LAYER(layer_name):** Remove all path entries, value
  entries, and blanket tombstones tagged with the specified layer
  from the source's storage. Returns the set of orphaned GUIDs.
  Called by LCS when a layer's metadata key is deleted (see the
  Layer lifecycle mechanism in the Layers section).

The source does not know about fds. It sees two database operations:
remove a path table row, remove all data rows for a GUID.

## Crash recovery

Sources MUST clean up orphaned GUIDs on startup. An orphaned GUID
is a key record with no corresponding path entries in any layer.
These arise from keys that were orphaned but not yet dropped before
the previous shutdown.

On startup, a source queries its storage for GUIDs that exist in
the key table but have no path entries. It purges them. This is
standard referential integrity cleanup and MUST be performed before
completing registration with LCS.

## New key at same path

A layer can create a new key at a path where another layer's key
already exists. Each layer has its own path entry pointing to its
own GUID. Layer resolution determines which is visible.

Existing fds referencing a different GUID at the same path are
completely isolated -- different GUIDs, different data, different
value entries.

## Constraints

- A key with visible children MUST NOT be deleted. Visibility is
  evaluated globally (all enabled layers), not relative to the
  caller's private layer set. This ensures deletion semantics are
  deterministic regardless of caller credentials. The syscall
  returns ENOTEMPTY. Recursive deletion is a client-side tree walk,
  not a kernel primitive.

- Deleting a key does NOT delete its values. Values are associated
  with the GUID, not the path entry. They are removed when the GUID
  is dropped (last fd closes on an orphaned key).
