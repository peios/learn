---
title: Path Entries
description: Key existence and naming are layer-qualified while key identity is not — the per-layer path entry that separates them, and hiding.
---

Key existence and naming are layer-qualified; key identity is not. The
source stores a **path entry** per layer, which separates the two. The
overlay-filesystem analogy is exact: directory entries are per-layer,
inodes are shared.

| Field | Description |
|---|---|
| Parent GUID | The parent key. |
| Child name | The key's name under that parent — one component, not a path. |
| Layer | The layer this entry belongs to. |
| Target | The GUID of the key at this path in this layer, or HIDDEN. |
| Sequence | A monotonic number assigned by LCS at creation, used for tiebreaking within a precedence tier. |

On the wire a HIDDEN entry is a target type of 1 with an all-zero GUID
(§5.A). A source returning a non-zero GUID on a HIDDEN entry is
returning malformed data.

## Creating a key

Creating a key in a layer always assigns a fresh GUID and produces two
records: a path entry `(parent, name, layer) → GUID` with a new
sequence number, and a key record carrying that GUID.

LCS sends `RSI_CREATE_ENTRY` first and `RSI_CREATE_KEY` second. That
order matters for the race: if another caller got there first, the
entry creation returns `RSI_ALREADY_EXISTS` and LCS retries the whole
thing as an open, reporting `REG_OPENED_EXISTING`. Failure on the
*second* call, for a GUID LCS just minted, is not a race and fails
closed (§5.2.3).

If a different layer already has a key at that path, the new layer gets
its own distinct GUID. Each layer has its own key object, and
resolution decides which is visible.

**No operation creates a path entry pointing at an existing GUID.**
`reg_create_key` always mints a new one. The namespace is a tree, never
a graph.

## No GUID sharing across layers

The path table's shape would technically permit two entries referencing
one GUID, which would be a hard link. No API exposes it. Every key has
exactly one canonical parent and name, and LCS validates that a source
is not reporting otherwise.

Aliasing has an explicit, visible mechanism, and it is symlinks. Hard
links would make parent-GUID semantics, descriptor inheritance, subtree
enumeration and watch dispatch all ambiguous at once.

## Hiding

A layer can create a HIDDEN entry at a path, making the key invisible
regardless of what lower-precedence layers say. It is the path-level
equivalent of a value tombstone, and when the hiding layer is removed
the lower key reappears.

A HIDDEN entry gets a sequence number like any other entry, so a
conflict between a GUID entry in one layer and a HIDDEN entry in
another at the same precedence resolves deterministically: the higher
sequence number wins.

## Hide and replace

A single layer can hide an existing key and put a new one at the same
path, and no special mechanism is needed for it. The layer creates its
own path entry pointing at its own new GUID; lower-precedence entries
for the same `(parent, name)` are masked because this layer's entry
wins on precedence. Removing the layer removes both the new key and its
masking effect, and the lower key comes back.

This falls out of per-layer path entries and precedence ordering
without a line of code that knows about it.

## Hive roots

A hive root has no parent GUID and no child name, so there is no
`(parent, name, layer)` tuple to remove or mask. Deleting or hiding a
hive root fd is `EINVAL`, rejected before source dispatch, before
transaction enlistment, before sequence allocation and before any watch
event is generated.
