---
title: The Bootstrap Problem
description: The registry has to configure itself — the three circular dependencies, and the three rules that break them.
---

The registry is the configuration store for the whole system, and it
has to configure itself. Three circular dependencies have to be broken
before it can serve anyone.

**peinit needs the registry to start services, but the registry source
is a service.** Service definitions live in the registry, and the
process that would serve them has not started.

**LCS needs operational parameters from the registry, but the registry
needs LCS.** Timeouts, caps and limits live under
`Machine\System\Registry\`, in a hive LCS itself routes.

**A fresh install has no data at all.** The source's database is empty;
there is nothing to read.

Three rules break all three.

## Rule 1: compiled-in defaults

Every operational parameter has a compiled-in default, and LCS runs on
those defaults from the moment PKM initialises. There is no "waiting
for configuration" state, no flag, and no wait queue: the limits
structure is statically initialised at load, the source char device is
registered without consulting configuration, and the first attempt to
read configuration happens on a workqueue after a source has already
registered.

Before any source registers, the routing table is empty, so every
operation that names a hive returns `ENOENT`. That is the only sense in
which LCS is not yet useful, and it is not a distinct state — it is
just an empty table.

## Rule 2: the base layer exists unconditionally

The base layer is a static constant in the kernel: name `base`,
precedence 0, enabled. It is handed out whenever the dynamic layer
table is empty and is always written first into every layer snapshot.

A source that registers with an entirely empty database is fully
functional, because the one layer that writes need is not in the
database. Persisted metadata under
`Machine\System\Registry\Layers\base\` may exist and may decorate the
base layer, but it is not required and cannot contradict it (§5.3.2).

## Rule 3: hot-swap, not restart

When configuration becomes available, LCS reads it, validates it, and
swaps the values in place. It does not restart, re-initialise, or
block. The whole transition from compiled-in defaults to registry-backed
configuration is driven by the internal self-watch (§5.10.4).

## Source dependencies are the source's problem

LCS neither knows nor cares what a source depends on. A source that
needs the root filesystem, a SYSTEM token, or a particular kernel
feature arranges that for itself. LCS's only requirement is that the
process can open `/dev/pkm_registry` and speak RSI.
