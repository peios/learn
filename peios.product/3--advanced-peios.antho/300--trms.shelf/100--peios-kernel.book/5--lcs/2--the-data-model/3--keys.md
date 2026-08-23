---
title: Keys
description: A key is a container of subkeys and values — its identity, its properties, volatile keys, and the rules for naming one.
---

A key is a node in the hierarchy: a container holding subkeys and
values. The filesystem analogy is an inode. A key carries identity and
properties; naming lives in path entries (§5.2.5).

| Field | Mutable | Layered | Description |
|---|---|---|---|
| GUID | No | No | Identity, assigned by LCS at creation, persisted by the source. |
| Name | No | No | The key's own name component. Informational; the authoritative name is in the path entry. |
| Parent GUID | No | No | The parent key. Nil for a hive root. |
| Security Descriptor | Yes | No | Computed from the parent at creation; changed at runtime with `WRITE_DAC` / `WRITE_OWNER`. |
| Last write time | Yes | No | Updated when a value is written or deleted or the descriptor changes. |
| Volatile | No | No | The source stores this key in non-persistent storage only. |
| Symlink | No | No | This key is a symbolic link (§5.2.4). |

**No key property is layer-qualified.** Properties belong to the object.
Changing a key's structural type through a layer is not a matter of
setting a flag; the layer hides the original key and creates a new one
at the same path, which is the ordinary overlay pattern.

## Identity

A key's identity is its GUID, not its path. Two keys occupying the same
path at different times are different objects with different GUIDs. A
path is a name that maps to an identity; the identity outlives the
name.

GUIDs are assigned by LCS — never by a source — and pushed to the
source at creation, where they become the primary key of its storage.
Once a path has been resolved to a GUID at open time, every subsequent
RSI operation uses the GUID directly.

The generator is the kernel's UUIDv4: random bytes from the kernel
CSPRNG with the RFC 4122 version and variant bits set. Freshness is the
collision resistance of UUIDv4 plus a check against the keys LCS
currently tracks, with a bounded retry. There is **no persistent
retired-GUID catalogue**, and no code anywhere that would maintain one.
A GUID dropped by orphan cleanup is not remembered.

If a source answers `RSI_CREATE_KEY` for a freshly generated GUID with
`RSI_ALREADY_EXISTS`, that is not a race to retry — the kernel believes
the GUID is unused and the source disagrees. LCS treats it as source
inconsistency and fails closed with `EIO`. It is never retried as an
open and `EEXIST` never reaches userspace from `reg_create_key`.

A GUID appears at exactly one canonical location. LCS validates that
and rejects a source that reports otherwise.

## Volatile keys

Volatile is a flag LCS carries and forwards. Storing a volatile key in
non-persistent storage is the source's obligation; nothing in the
kernel enforces it.

What the kernel does enforce is the containment rule: **a non-volatile
key may not be created under a volatile parent** (`EINVAL`). The
converse is allowed — a volatile key under a persistent parent is
ordinary.

## Naming

Three bytes are forbidden in a key name component: backslash and
forward slash, both of which are separators, and the null byte. Every
other valid UTF-8 sequence is permitted, spaces and arbitrary Unicode
included.

Empty components are forbidden, which rules out a leading separator and
consecutive separators (`Machine\\System`). A trailing separator
(`Machine\System\`) is likewise invalid.

Length limits are byte counts: `MaxPathComponentLength` per component,
`MaxTotalPathLength` for the whole path, `MaxKeyDepth` for nesting.

Forward slash normalisation is achieved by treating `/` as a separator
wherever a separator is recognised, rather than by rewriting the string
— so a materialised component never contains either separator, and the
canonical form is per-component rather than a canonicalised string.
