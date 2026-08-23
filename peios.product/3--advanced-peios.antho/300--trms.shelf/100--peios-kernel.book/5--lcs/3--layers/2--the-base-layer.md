---
title: The Base Layer
description: The kernel-reserved layer that exists unconditionally before any source registers — its persisted metadata and the two ways it is matched.
---

The base layer, named `base`, is a kernel-reserved implicit layer. It
exists unconditionally, before any source registers and whether or not
any metadata has ever been persisted for it.

It is a static constant in the kernel: precedence 0, enabled. It is
never stored in the dynamic layer table, is always emitted first in
every layer snapshot, and is handed out even when the dynamic table is
empty. A source that registers with a completely empty database is
therefore immediately usable, because the one layer that writes need is
not in the database.

Four things cannot happen to it:

- it cannot be deleted;
- it cannot be disabled;
- its precedence cannot be changed;
- a layer table row for it cannot be published at all.

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
which is to say, who may write into the base layer (§5.3.4). Its
`Precedence` and `Enabled` values are ignored.

The internal self-watch also ignores a `SUBKEY_DELETED` for `base`: if a
higher-precedence HIDDEN entry masks the base layer's metadata key, that
is not a layer deletion and is not processed as one. The base layer's
existence is hardcoded and layer mechanics cannot reach it.

## The default target

A write that names no layer targets the base layer. That is the default
for manual administration and for system initialisation.

Before the base layer's metadata key exists — first boot, before seed
restore — LCS uses a compiled-in default descriptor granting SYSTEM and
Administrators `KEY_ALL_ACCESS`, so writes into the base layer are
possible from the very beginning. The compiled-in default is replaced by
the real descriptor as soon as seed restore creates the key.

## `base` is matched two ways

The check for whether a name is the base layer is implemented twice in
the kernel: once using Unicode Simple Case Folding like every other
name comparison, and once using ASCII case-insensitive comparison, on
two of its call sites. For the literal string `base` the two agree.
