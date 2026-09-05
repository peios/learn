---
title: The Base Layer
description: The kernel-reserved layer that exists unconditionally before any source registers — its persisted metadata and the two ways it is matched.
---

The base layer, named `base`, is a kernel-reserved implicit layer. It
exists unconditionally, before any source registers and whether or not
any metadata has ever been persisted for it. [*layer.base.exists-unconditionally]

It is a static constant in the kernel: precedence 0, enabled. [*layer.base.is-precedence-zero-and-enabled] It is
never stored in the dynamic layer table. [*layer.base.not-in-the-dynamic-layer-table]

It is always emitted first in every layer snapshot, and is handed out
even when the dynamic table is empty. [*layer.base.emitted-first-in-every-snapshot] A source that registers with a
completely empty database is therefore immediately usable, because the
one layer that writes need is not in the database.

Four things cannot happen to it:

- it cannot be deleted; [*layer.base.cannot-be-deleted]
- it cannot be disabled; [*layer.base.cannot-be-disabled]
- its precedence cannot be changed; [*layer.base.precedence-cannot-be-changed]
- a layer table row for it cannot be published at all. [*layer.base.row-cannot-be-published]

Each of those is enforced in more than one place. Deletion is refused by
the layer table, by the resolution core, by the `RSI_DELETE_LAYER`
dispatch path, and by the transaction layer-abort path. Publication of a
`base` row is rejected outright, and the refresh path short-circuits for
`base` **before** it would read `Precedence` or `Enabled`, so persisted
values for those are never even consulted.

## Persisted metadata

`Machine\System\Registry\Layers\base\` may exist, and it usually does,
but it decorates the base layer rather than defining it. What LCS takes
from it is the metadata key's GUID and its cached Security Descriptor —
which is to say, who may write into the base layer (§5.3.4). [*layer.base.metadata-key-supplies-guid-and-descriptor]

Its `Precedence` and `Enabled` values are ignored. [*layer.base.persisted-precedence-and-enabled-ignored]

The internal self-watch also ignores a `SUBKEY_DELETED` for `base`: if a
higher-precedence HIDDEN entry masks the base layer's metadata key, that
is not a layer deletion and is not processed as one. [*layer.base.subkey-deleted-is-ignored] The base layer's
existence is hardcoded and layer mechanics cannot reach it.

## The default target

A write that names no layer targets the base layer. [*layer.base.is-the-default-write-target] That is the default
for manual administration and for system initialisation.

Before the base layer's metadata key exists — first boot, before seed
restore — LCS uses a compiled-in default descriptor granting SYSTEM and
Administrators `KEY_ALL_ACCESS`, so writes into the base layer are
possible from the very beginning. The compiled-in default is replaced by
the real descriptor as soon as seed restore creates the key (§5.3.4).

## `base` is matched like every other layer name [*layer.base.name-matched-by-case-folding]

The reserved name is recognised with Unicode Simple Case Folding, the
same algorithm and the same table used for every other layer-name
comparison.

There was a second, ASCII case-insensitive comparator beside it, used on
two call sites. For the literal string `base` the two agreed — a length
pre-check made a non-ASCII case pair fail before folding could matter —
so the divergence was latent rather than absent, and would have become
live the moment anything about the reserved name changed. It is gone;
both call sites now take the folding comparator and propagate its error
rather than collapsing it into a `bool`.
