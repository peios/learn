---
title: Layer Resolution
order: 7
---

Layer resolution is the algorithm LCS uses to determine the
effective state of a path entry or value from multiple per-layer
entries. It is the core mechanism that makes the registry layered.

## Sequence counter

LCS maintains a single global monotonic sequence counter. Every
mutation that creates a layer-qualified entry (path entry creation,
value write, key hiding, blanket tombstone) is assigned the next
sequence number from this counter. The counter is never decremented
or reset.

On startup, each source reports its highest persisted sequence
number in the registration handshake. LCS initialises the counter
to `max(all reported values) + 1`. This ensures new writes always
have higher sequence numbers than any persisted entry, even after
a restart.

The sequence counter provides deterministic tiebreaking within a
precedence tier. Wall-clock time is tracked separately via the
key's last write time for human-facing metadata.

## Pseudocode conventions

The resolution algorithms use tuples `(precedence, sequence, item)`
as candidates. Selection uses `max()` ordered by precedence first,
then sequence. Tuple fields are accessed by index: `[0]` =
precedence, `[1]` = sequence, `[2]` = item (the entry or a
TOMBSTONE sentinel).

A layer is **active** for a given thread if it is enabled globally
or its name appears in the thread's private layer set.

```
is_active(layer, thread_credentials):
    return layer.enabled or layer.name in thread_credentials.private_layers
```

## Value resolution

Given a (key GUID, value name) pair, resolve the effective value:

```
resolve_value(key_guid, value_name, thread_credentials):
    // Step 1: Collect entries and blanket tombstones
    entries = source.query_values(key_guid, value_name)
    blankets = source.query_blanket_tombstones(key_guid)

    // Step 2: Build candidate list from per-value entries
    candidates = []
    for entry in entries:
        layer = layer_table.get(entry.layer)
        if layer is None:
            continue  // unknown layer, discard
        if not is_active(layer, thread_credentials):
            continue
        candidates.append((layer.precedence, entry.sequence, entry))

    // Step 3: Add blanket tombstones as candidates
    // A blanket tombstone acts as a tombstone for every value name
    // at its precedence/sequence.
    for bt in blankets:
        layer = layer_table.get(bt.layer)
        if layer is None:
            continue
        if not is_active(layer, thread_credentials):
            continue
        candidates.append((layer.precedence, bt.sequence, TOMBSTONE))

    // Step 4: Select winner
    if len(candidates) == 0:
        return NOT_FOUND

    // Highest precedence wins. Within same precedence, highest
    // sequence number wins.
    winner = max(candidates, key=lambda c: (c[0], c[1]))

    // Step 5: Evaluate winner
    if winner[2] is TOMBSTONE:
        return NOT_FOUND
    if winner[2].type == REG_TOMBSTONE:
        return NOT_FOUND
    return (winner[2].type, winner[2].data)
```

## Path entry resolution

Given a (parent GUID, child name) pair, resolve key visibility:

```
resolve_path(parent_guid, child_name, thread_credentials):
    entries = source.lookup(parent_guid, child_name)

    candidates = []
    for entry in entries:
        layer = layer_table.get(entry.layer)
        if layer is None:
            continue
        if not is_active(layer, thread_credentials):
            continue
        candidates.append((layer.precedence, entry.sequence, entry))

    if len(candidates) == 0:
        return NOT_FOUND

    winner = max(candidates, key=lambda c: (c[0], c[1]))

    if winner[2].target == HIDDEN:
        return NOT_FOUND  // hidden, lower layers masked
    return winner[2].target  // GUID of the visible key
```

## Value enumeration

Enumerate all effective values for a key:

```
enumerate_values(key_guid, thread_credentials):
    all_entries = source.query_all_values(key_guid)

    // Collect unique value names across all layers
    names = unique(entry.name for entry in all_entries)

    results = []
    for name in names:
        result = resolve_value(key_guid, name, thread_credentials)
        if result != NOT_FOUND:
            results.append((name, result[0], result[1]))

    return results
```

Callers see only effective values. Tombstoned values and values
masked by blanket tombstones are omitted. The caller never sees
per-layer raw data through normal operations.

## Subkey enumeration

Enumerate all visible child keys:

```
enumerate_subkeys(parent_guid, thread_credentials):
    all_children = source.enum_children(parent_guid)

    // Collect unique child names across all layers
    names = unique(entry.child_name for entry in all_children)

    results = []
    for name in names:
        guid = resolve_path(parent_guid, name, thread_credentials)
        if guid != NOT_FOUND:
            key_meta = source.read_key(guid)
            results.append((name, key_meta))

    return results
```

A subkey is visible if its effective path entry (after layer
resolution) maps to a GUID, not HIDDEN.
