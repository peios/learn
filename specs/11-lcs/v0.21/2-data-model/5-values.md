---
title: Values
---

A value is a named, typed datum stored within a key. Values hold
the actual configuration data. A key can hold multiple values, each
with a distinct name. One unnamed value per key is permitted (the
default value, with the empty string as its name).

## Fields

| Field | Type | Description |
|---|---|---|
| Key GUID | GUID | The key this value belongs to. |
| Name | string | The value's name. Empty string for the default value. Case-preserving, compared case-insensitively. |
| Type | uint32 | A registry value type (see Value Types below). LCS stores the type tag but does not interpret the data, except REG_LINK which triggers symlink resolution. |
| Data | byte[] | The value's payload. Maximum size is configurable (default 1 MB). |
| Layer | string | The layer this entry belongs to. Every value write is tagged with a layer. |
| Sequence | uint64 | Monotonic sequence number assigned by LCS at write time. Used for within-tier tiebreaking when multiple layers at the same precedence write to the same value. |

## Per-layer storage

A single (key GUID, value name) pair can have multiple entries in the
source -- one per layer that has written to it. The source stores all
entries. LCS resolves the effective value at read time via the layer
resolution algorithm. This is the mechanism that enables layer
deletion to automatically revert configuration: delete the layer, its
entries disappear, the next-highest-precedence entry becomes
effective.

## Value tombstones

A layer entry can be a **tombstone** instead of a normal value -- a
marker that means "this value does not exist in this layer, and
lower-precedence layers are masked." Layer resolution treats a
tombstone as "value not found" without falling through to lower
layers.

Tombstones are required for registry.pol compatibility. The
`**Del.ValueName` directive in registry.pol deletes specific values.
Without tombstones, a higher-precedence layer can only override
values, not express "this value must not be configured." When the
tombstone's layer is removed, the lower-precedence value becomes
effective again.

In the source's storage, a tombstone is a layer entry with type
REG_TOMBSTONE instead of normal type + data. REG_TOMBSTONE is a
Peios-internal type, never exposed to callers reading values.
Callers see "value not found" (ENOENT) when a tombstone is the
effective entry.

## Blanket tombstones

A **blanket tombstone** is a per-layer marker on a key that masks
all values from lower-precedence layers for that key. Unlike
per-value tombstones (which mask a specific value name), a blanket
tombstone masks every value on the key regardless of name.

Blanket tombstones are required for registry.pol `**DelVals`
semantics. The `**DelVals` directive means "delete all values in
this key before applying new ones." In a layered model, this must
mask all lower-precedence values -- including values whose names
are not known at the time the blanket is written.

### Storage

A blanket tombstone is stored as a flag on the (key GUID, layer)
relationship. It occupies no per-value-name entry.

### Resolution

When LCS resolves a value on a key, the resolution algorithm checks
for blanket tombstones before evaluating per-value entries:

1. Collect all layer entries for the requested (key GUID, value
   name), plus any blanket tombstones on this key.
2. A blanket tombstone is treated as a tombstone candidate for
   every value name, competing at its (precedence, sequence) tuple.
   The candidate with the highest precedence wins; within the same
   precedence, the highest sequence number wins.
3. If the winning candidate is a blanket tombstone and no per-value
   entry has a higher (precedence, sequence) tuple, the value is
   masked. A per-value entry that wins the tiebreak overrides the
   blanket.

A layer can write a blanket tombstone and also write specific values
in the same layer. The specific values are visible; all other values
from lower-precedence layers are masked. This is exactly `**DelVals`
followed by new value writes.

### Enumeration

When enumerating values on a key with a blanket tombstone, LCS
returns only values from the blanket's layer or higher-precedence
layers. Lower-precedence values are invisible.

### Layer deletion

Removing a layer that holds a blanket tombstone removes the blanket.
All previously masked lower-precedence values become visible again.

## Value types

LCS supports the full Windows registry value type set for
registry.pol compatibility:

| Type | Code | Description |
|---|---|---|
| REG_NONE | 0 | No type. |
| REG_SZ | 1 | Null-terminated string. |
| REG_EXPAND_SZ | 2 | String with environment variable references. |
| REG_BINARY | 3 | Raw binary data. |
| REG_DWORD | 4 | 32-bit integer, little-endian. |
| REG_DWORD_BIG_ENDIAN | 5 | 32-bit integer, big-endian. |
| REG_LINK | 6 | Symbolic link target (Unicode string). Triggers symlink resolution when read as a key's default value on a symlink key. |
| REG_MULTI_SZ | 7 | Array of null-terminated strings, terminated by an additional null. |
| REG_QWORD | 11 | 64-bit integer, little-endian. |

LCS treats values as opaque typed blobs. It stores the type tag and
returns it on read, but does not validate or interpret the data
payload except for REG_LINK on symlink keys.

The following type is internal to LCS and MUST NOT be exposed to
userspace callers:

| Type | Code | Description |
|---|---|---|
| REG_TOMBSTONE | 0xFFFF | Tombstone marker. Masks lower-precedence entries during layer resolution. Callers reading a value whose effective entry is a tombstone receive ENOENT. |

## Naming rules

Value names follow the same case comparison rules as key names
(Unicode Simple Case Folding, case-preserving, case-insensitive).

Value names differ from key names in one respect: backslash and
forward slash ARE permitted in value names. Value names are not
hierarchical, so separators have no special meaning.

Only null (`\0`) is forbidden. Empty string is reserved for the
default value.

## Maximum value size

The maximum data size for a single value is configurable via the
self-configuration mechanism (default 1 MB). See the
Self-Configuration section for the full parameter table.
