---
title: Path Entries
order: 4
---

Key existence and naming are layer-qualified. The source stores path
entries per-layer, separating naming (which is layered) from identity
(which is not). This is analogous to an overlay filesystem: directory
entries are per-layer, inodes are shared.

## Fields

| Field | Type | Description |
|---|---|---|
| Parent GUID | GUID | The GUID of the parent key. |
| Child name | string | The name of this key under its parent. Single component, not a full path. |
| Layer | string | The layer that created this path entry. |
| Target | GUID or HIDDEN | The GUID of the key at this path in this layer, or HIDDEN (a tombstone that masks lower-precedence layers). |
| Sequence | uint64 | Monotonic sequence number assigned by LCS at creation. Used for within-tier tiebreaking: when multiple layers at the same precedence have entries for the same (parent, child name), the highest sequence number wins. |

## Path resolution

When LCS resolves a path component, the source returns all path
entries for that (parent GUID, child name) across all layers. LCS
applies layer resolution:

1. Discard entries from inactive layers. A layer is active if it
   is enabled globally or its name appears in the calling thread's
   private layer set.
2. Look up each entry's layer precedence from the cached layer table.
3. Select the entry with the highest precedence. If multiple entries
   share the highest precedence, select the one with the highest
   sequence number.
4. If the selected entry is HIDDEN, the path does not exist -- lower
   layers are masked.
5. If the selected entry maps to a GUID, that key is visible.

This is the same resolution algorithm used for values, applied to
existence claims rather than data.

## Key creation

Creating a key in a layer always assigns a fresh GUID and produces
two records:

1. A path entry: `(parent GUID, name, layer) → GUID` with a new
   sequence number.
2. A key record via RSI_CREATE_KEY with the fresh GUID.

If a different layer already has a key at the same path, the new
layer gets its own distinct GUID. Each layer has its own key object.
Layer resolution determines which is visible.

There is no operation that creates a path entry pointing to an
existing GUID. reg_create_key always assigns a new GUID. The
namespace is always a tree, never a graph.

## No GUID sharing across layers

The path table's structure technically permits multiple entries
referencing the same GUID, which would create hard-link-like
semantics. This is deliberately not exposed by any API. Every key
has exactly one canonical parent and name. This avoids ambiguity in
parent GUID semantics, SD inheritance, subtree enumeration, and
watch dispatch. If aliasing is needed, symlinks are the explicit,
visible mechanism.

## Key hiding

A layer can create a HIDDEN entry at a path, making the key
invisible regardless of lower-precedence entries. HIDDEN is the
path-level equivalent of a value tombstone. When the hiding layer
is removed, the lower-precedence key reappears.

The HIDDEN entry is assigned a sequence number like any other path
entry. This provides deterministic behaviour when a layer at the
same precedence has both a GUID entry and another layer has a HIDDEN
entry -- the higher sequence number wins.

## Hide and replace

A single layer can both hide an existing key and create a new one
at the same path. The layer creates a path entry
`(parent, name, layer) → new-GUID`. Lower-precedence layers' path
entries for the same (parent, name) are masked by the higher
precedence of this layer's entry. When the layer is removed, both
the new key and its masking effect disappear, and the
lower-precedence key reappears.

No special mechanism is needed. This falls out of per-layer path
entries and precedence resolution naturally.

## Layer deletion

When a layer is deleted, all its path entries are removed. Any GUID
that is no longer referenced by any path entry across any layer is
orphaned. Orphaned keys follow the deletion model described in the
Deletion section.
