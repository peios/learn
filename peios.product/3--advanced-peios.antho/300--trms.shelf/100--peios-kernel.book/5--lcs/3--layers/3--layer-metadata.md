---
title: Layer Metadata
description: Layer metadata lives in the registry it configures — the circularity that creates, why publication is atomic, and when the refresh runs.
---

Layer metadata lives in the registry, under
`Machine\System\Registry\Layers\<LayerName>\`. [*layer.metadata.lives-under-the-layers-key] Each layer's key holds
three values:

| Value | Type | Default if missing |
|---|---|---|
| `Precedence` | `REG_DWORD` | 0 [*layer.metadata.precedence-is-dword-default-0] |
| `Enabled` | `REG_DWORD`, 0 or 1 | true [*layer.metadata.enabled-is-dword-default-true] |
| `Owner` | `REG_BINARY`, a SID | the creating token's SID for a new layer [*layer.metadata.owner-is-binary-sid] |

Three things are malformed metadata, and are rejected rather than
coerced:

- a value of the wrong type; [*layer.metadata.wrong-type-is-malformed]
- a `REG_DWORD` that is not exactly four bytes; [*layer.metadata.dword-must-be-exactly-four-bytes]
- an `Enabled` greater than 1. [*layer.metadata.enabled-above-one-is-malformed]

`Owner` selection has a fallback chain: the metadata value; failing
that, the creator's SID for a newly created layer; failing that, the
previous known-good owner; failing that, the owner SID from the
metadata key's own descriptor. [*layer.metadata.owner-fallback-chain]

If none of those is available the layer cannot be published. [*layer.metadata.unresolvable-owner-blocks-publication] Every one
of these is informational and none grants access.

There is no "create layer" or "delete layer" syscall. Creating a key
under `Layers\` creates a layer; deleting that key deletes it. [*layer.metadata.key-creation-and-deletion-are-the-lifecycle]
Creation should be done inside a transaction so that all three values
are present when the refresh runs.

## Circularity

Layer metadata is stored in the registry, which is itself layered.
That is circular, and it is safe, because resolution never re-enters
itself.

LCS always resolves using its **currently published** layer table —
including when resolving layer metadata values. [*layer.metadata.resolved-with-the-published-table] When a write to the
metadata subtree commits, the refresh reads the affected metadata using
the current table and then publishes an updated one.

The table is never re-resolved mid-operation; each operation takes one
snapshot and uses it throughout. [*layer.metadata.one-snapshot-per-operation]

So a high-precedence layer can override another layer's precedence, and
that is useful and intended. It simply takes effect at the next
publication rather than recursively. [*layer.metadata.override-takes-effect-at-next-publication]

## Publication is atomic

A layer is not merely a name and a precedence. The published unit is
three things together: the layer table entry, the metadata key's GUID,
and the cached Security Descriptor of that key. [*layer.metadata.published-unit-is-three-things]

All three are written under one lock, and a snapshot reader that finds
them incomplete returns `EIO` rather than a half-populated layer. [*layer.metadata.incomplete-publication-is-eio]

A layer that has no metadata key GUID and no authorisation descriptor
is not visible in the table at all. [*layer.metadata.layer-without-guid-or-descriptor-is-invisible] There is no window in which a layer
exists but nobody can be authorised against it.

Creating the metadata key is ordinary key creation, so LCS computes its
descriptor from parent inheritance through KACS before the source
persists it. [*layer.metadata.descriptor-computed-by-inheritance-before-persist] On the normal path the key therefore has a descriptor
before the layer can be published.

## When the refresh runs

Changes under `Layers\` mark the affected layer names dirty. After the
mutating operation commits, and **before the syscall returns to
userspace**, LCS runs a bounded refresh for those names: it reads the
committed metadata key, its values and its descriptor, and publishes
the new entry atomically. [*layer.metadata.refresh-runs-before-the-syscall-returns]

For a transaction the refresh runs once, after the source commit
succeeds and before `REG_IOC_COMMIT` returns. [*layer.metadata.transaction-refresh-runs-once-before-commit-returns]

The internal self-watch is what notices the subtree changed, but the
watch callback is not the atomicity boundary and must never publish a
partial entry. LCS does not perform source round trips while holding
the watch-map or layer-table publication locks. [*layer.metadata.no-source-round-trips-under-publication-locks]

## When the metadata descriptor will not parse

If the metadata key's descriptor cannot be read or parsed during a
refresh, the source has returned malformed data. LCS emits an audit
event, does not publish or update that layer's entry, and keeps the
previous known-good one. [*layer.metadata.unparseable-descriptor-keeps-previous-entry]

If the refresh was required to complete the operation in hand —
creating a layer, say, or exposing one — the syscall fails with `EIO`. [*layer.metadata.required-refresh-failure-is-eio]
