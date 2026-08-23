---
title: Writing Into a Layer
description: Every mutation targeting a layer requires layer write access — the base layer before it exists, the precedence gate, and deleting a layer.
---

Every mutating operation that targets a layer — value writes, value
deletions, tombstones, key hides, blanket tombstones, key creation —
requires **layer write authorization**: `KEY_SET_VALUE` on the layer's
metadata key at `Machine\System\Registry\Layers\<LayerName>\`.

This is a second AccessCheck, against a different object, and it is in
addition to the fd's granted mask on the target key. Both must pass.

The descriptor on a layer's metadata key is therefore the answer to
"who may write into this layer". The base layer's inherits from the
`Machine` hive root — SYSTEM and Administrators with `KEY_ALL_ACCESS`.
Group Policy layers get restrictive descriptors from the GP client at
creation; role layers get theirs from the role installer.

That closes two escalation paths at once. An unprivileged process
cannot write into a GP layer, and one role's service cannot write into
another role's.

The layer metadata descriptors are cached alongside the layer table and
invalidated by the same self-watch (§5.3.3). A layer that is not in the
table is `ENOENT` for any operation naming it.

## The base layer before it exists

On first boot, before seed restore, `Layers\base\` does not exist. LCS
falls back to a compiled-in default descriptor granting
`KEY_ALL_ACCESS` to SYSTEM and Administrators, so base-layer writes
work from the start. It is replaced by the persisted descriptor the
moment seed restore creates the key.

## Layer lifecycle

| Operation | Requirement |
|---|---|
| Create a layer at precedence 0 | `KEY_CREATE_SUB_KEY` on `Layers\` |
| Create a layer above precedence 0 | `KEY_CREATE_SUB_KEY` on `Layers\` **and** `SeTcbPrivilege` |
| Write into a layer | `KEY_SET_VALUE` on the layer's metadata key |
| Modify layer metadata | `KEY_SET_VALUE` on the metadata key; raising precedence above 0 additionally requires `SeTcbPrivilege` |
| Delete a layer | `DELETE` on the metadata key's fd |

Everything except the precedence rule is controlled purely by the
descriptor on the metadata key.

## The precedence gate

`SeTcbPrivilege` is required specifically to establish or raise a
layer's precedence above 0. It is defence in depth: compromising the
descriptor on `Layers\` is not enough to create a Group Policy-tier
layer.

The check is synchronous and inline at `REG_IOC_SET_VALUE` time, and it
happens early — before sequence allocation, before transaction
enlistment, before the source is contacted. It runs when three things
hold: the target key GUID is in the set of known layer metadata keys,
the value name folds equal to `Precedence` under the same Unicode
folding used for every other value name, and the data is a positive
`REG_DWORD`. Failing the privilege check is `EPERM`.

The gate tests for a four-byte `REG_DWORD` specifically. A `Precedence`
written with some other type slips past it — and then fails at the
refresh, which rejects a non-`REG_DWORD` `Precedence` as malformed
metadata. The precedence never actually rises.

`REG_IOC_RESTORE` has its own equivalent gate, applied to the backup
stream's layer manifest before anything is written (§5.9.3).

## Deleting a layer

Deleting the metadata key fires a `SUBKEY_DELETED` on the internal
self-watch. LCS removes the layer from the table and broadcasts
`RSI_DELETE_LAYER` to every registered source, each of which purges
every entry tagged with that name and reports the GUIDs that lost their
last path entry.

Before the broadcast, LCS aborts every bound transaction whose mutation
log touched that layer (§5.2.9).

A `SUBKEY_DELETED` for `base` is ignored (§5.3.2).
