---
title: Bootstrap Sequence
---

The registry is the configuration store for the entire system, but
the registry itself must be configured and populated. This section
defines LCS's behaviour during bootstrap -- how it transitions from
"kernel just booted" to "fully operational."

## The bootstrap problem

Three circular dependencies must be broken:

1. **peinit needs the registry to start services, but the registry
   source is a service.** peinit cannot read service definitions
   from the registry because the source providing those definitions
   hasn't started yet.

2. **LCS needs operational parameters from the registry, but the
   registry needs LCS.** LCS reads its configuration from keys that
   live in a source that LCS manages.

3. **First boot has no data.** On a fresh install, the source's
   database is empty.

## Bootstrap rules

### Rule 1: Compiled-in defaults

Every LCS operational parameter (see §11.4 for the full list of
19 parameters) has a compiled-in
default. LCS operates on
these defaults from the moment PKM loads. LCS MUST NOT enter a
"waiting for configuration" state. It is always operational.

### Rule 2: The base layer exists unconditionally

The base layer is hardcoded in LCS. It exists before any source
registers. No persisted metadata is required for the base layer
to be functional.

### Rule 3: Hot-swap, not restart

When a source registers and the registry becomes available, LCS
reads its operational parameters and layer metadata, validates
them, and hot-swaps the in-memory values. LCS does not restart
or re-initialise. In-flight operations use the values that were
active when they started. New operations use the updated values.

## LCS boot sequence

### Normal boot (source has existing data)

```
Kernel boots
  → PKM loaded (KACS + LCS initialised with compiled-in defaults)
  → LCS creates /dev/pkm_registry
  → Base layer exists in memory

Source registers (e.g., loregd started by peinit)
  → Opens /dev/pkm_registry
  → Registers hives with root GUIDs and max sequence number
  → LCS initialises global sequence counter to max + 1

LCS becomes operational for those hives
  → Reads Machine\System\Registry\* (operational parameters)
  → Validates and hot-swaps to registry values
  → Reads Machine\System\Registry\Layers\* (layer metadata)
  → Populates in-memory layer table
  → Arms subtree watch on Machine\System\Registry\
```

### First boot (empty source)

```
Same as normal boot through source registration

Source registers with empty database
  → Source detects empty database on first startup
  → Source generates random GUIDs for hive root keys
  → Source creates root key records with default SDs
    (Machine root: SYSTEM + Admins KEY_ALL_ACCESS,
     Authenticated Users KEY_READ, all container-inherit)
  → Source persists root GUIDs and registers with LCS
  → Hive roots exist but contain no subkeys

LCS reads Machine\System\Registry\* → ENOENT
  → Retains compiled-in defaults
  → Arms watch on Machine\ root

(peinit detects empty registry, restores seed backup -- this is
peinit's decision, not LCS's concern)

Seed restore populates Machine\ hive via REG_IOC_RESTORE
  → LCS subtree watch fires
  → Re-reads Machine\System\Registry\* (now exists)
  → Validates and hot-swaps to seed values
  → Re-reads layer metadata
  → Normal operation continues
```

## Bootstrap contract

The following invariants MUST hold during bootstrap and MUST NOT
be violated by any future change:

1. **LCS is always operational with compiled-in defaults.** From
   the moment PKM loads, LCS can accept syscalls. Before any
   source registers, all operations return ENOENT (no hives
   available). After a source registers, operations work against
   compiled-in defaults until configuration is loaded.

2. **The base layer requires no persisted state.** LCS hardcodes
   the base layer's existence, name, precedence, and enabled
   state. A source that registers with an empty database is fully
   functional -- the base layer exists in LCS's memory.

3. **Hot-swap is the only configuration transition.** LCS never
   blocks, restarts, or re-initialises when transitioning from
   compiled-in defaults to registry-backed configuration. The
   self-watch mechanism drives all transitions.

4. **Source dependencies are the source's concern.** LCS does not
   know or care what a source depends on. A source that requires
   the root filesystem, a SYSTEM token, or specific kernel
   features manages those dependencies itself. LCS's only
   requirement is that the source can open `/dev/pkm_registry`
   and speak RSI.
