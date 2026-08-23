---
title: The Boot Sequence
description: What happens from PKM initialisation to a registered source, on a normal boot and on a first boot, and the contract it establishes.
---

## Normal boot

```
Kernel boots
  → PKM initialises; LCS runs on compiled-in defaults
  → /dev/pkm_registry registered
  → the base layer exists in memory

A source registers — loregd, started by peinit
  → opens /dev/pkm_registry (SeTcbPrivilege checked at open)
  → REG_SRC_REGISTER: hive names, root GUIDs, max persisted sequence
  → LCS initialises or advances next_sequence to max + 1

Bootstrap refresh is queued
  → resolve Machine\System\Registry     → read and hot-swap parameters
  → resolve Machine\System\Registry\Layers → populate the layer table
  → arm internal subtree watches
```

The bootstrap refresh runs on a workqueue after `REG_SRC_REGISTER`
returns, so registration never blocks on configuration and a source
that registers can start answering immediately.

The refresh is triggered by the arrival of a **global hive named
`Machine`**. That name is matched case-insensitively in the kernel and
is one of the two hive names LCS knows about; the other is `Users`, the
target of `CurrentUser\` rewriting (§5.2.1). Neither is a routing
decision — routing is entirely dynamic — but the claim that the kernel
holds no hive names at all would not be true.

## First boot

An empty source has no `Machine\System\Registry` to read.

```
Source detects an empty database on first startup
  → generates root GUIDs for the hives it backs
  → creates root key records with their default SDs
  → persists them, then registers with LCS

LCS resolves Machine\System\Registry → does not exist
  → compiled-in defaults retained
  → subtree watch armed on the Machine\ hive root instead

peinit notices the registry is empty and restores the seed backup.
That is peinit's decision, not LCS's.

Seed restore populates Machine\ through REG_IOC_RESTORE
  → the fallback subtree watch fires
  → LCS re-runs the bootstrap refresh: resolves the specific GUIDs,
    re-arms targeted watches, validates and hot-swaps the seed values,
    and re-reads layer metadata
```

Hive root Security Descriptors are set by the source, not by LCS. LCS
holds no template for them and enforces whatever the source stores
(§5.4.3).

## Watch arming in practice

The spec-level description above says the fallback watch is armed
*instead of* the targeted ones. What the kernel actually arms is a
**mixed** set: targeted watches on whichever of the two roots exist,
*plus* the `Machine\` root fallback. The fallback is a superset rather
than a substitute, and it stays armed until a refresh finds both roots
present.

A third internal watch is armed by the same sequence, on
`Machine\System\KMES`, which is not LCS configuration at all — it is
how KMES picks up its own parameters from the registry LCS serves.

## The bootstrap contract

Four properties hold throughout and are relied on elsewhere:

1. **LCS is always operational with compiled-in defaults.** It accepts
   syscalls from the moment PKM initialises.
2. **The base layer requires no persisted state.**
3. **Hot-swap is the only configuration transition.** LCS never blocks,
   restarts, or re-initialises.
4. **Source dependencies are the source's concern.**
