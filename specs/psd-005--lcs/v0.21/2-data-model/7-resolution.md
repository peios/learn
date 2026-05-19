---
title: Layer Resolution
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

The counter is represented internally as `next_sequence`: the next
sequence number LCS will allocate. Allocating a sequence number
increments `next_sequence`. Allocated sequence numbers are never
reused, even if the operation later fails, times out, or is aborted
as part of a transaction.

Transactional mutating operations are assigned sequence numbers when
the operation is accepted into the transaction, not at commit time.
This preserves the transaction's operation order for deterministic
layer tiebreaking and watch dispatch if the transaction commits.
If the transaction aborts, the allocated sequence numbers remain
unused gaps.

On startup, each source reports its highest persisted sequence
number in the registration handshake. LCS initialises the counter
to `max(all reported values) + 1`. This ensures new writes always
have higher sequence numbers than any persisted entry, even after
a restart.

When a source registers after `next_sequence` has already been
initialised, LCS advances `next_sequence` to
`max(next_sequence, source_max_sequence + 1)`. If adding one would
overflow uint64, registration fails with EOVERFLOW and the source is
not made active.

LCS rejects any source-returned layer-qualified entry whose sequence
number is greater than or equal to `next_sequence`. Such an entry is
malformed source data: sources store sequence numbers assigned by
LCS and cannot legitimately contain future sequence numbers.

Within a single resolution candidate set, duplicate sequence numbers
at the same precedence are malformed if they would otherwise be
compared to select a winner. LCS rejects the response as malformed
source data rather than making an arbitrary choice. Duplicate
sequence numbers in unrelated candidate sets are not compared and do
not by themselves affect resolution.

The sequence counter provides deterministic tiebreaking within a
precedence tier. Wall-clock time is tracked separately via the
key's last write time for human-facing metadata.

Sequence numbers are not hive generation numbers. A sequence number
orders layer-qualified entries for resolution and is persisted by
sources. The hive generation number exposed by REG_IOC_QUERY_KEY_INFO
is a volatile LCS-owned per-hive change epoch used for cache and watch
overflow recovery. Sources do not persist hive generation numbers.

Registry restore does not persist backup sequence numbers directly.
Restore reserves a fresh global sequence range and remaps backup
sequence numbers into that range so restored entries are newer than
pre-restore state while preserving the backup's internal relative
ordering. See §9.1.

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

## Unknown layer entries

Source entries tagged with a well-formed layer name that is not
present in the current layer table are valid latent entries. LCS
ignores them during resolution while the layer is absent. If a layer
with the same folded layer identity is later created, those entries
become eligible for normal resolution using the new layer metadata.

This supports restore, import, and boot ordering where source
storage may contain entries before their metadata has been loaded.
It also follows the core rule that sources persist entries while LCS
decides their meaning.

Normal LCS mutating operations do not create entries for missing
layers: layer-targeting ioctls still return ENOENT when the target
layer is absent from the layer table. Latent unknown-layer entries
therefore arise from existing source storage, restore/import ordering,
previous boots, or source behaviour. Since sources are trusted
components, well-formed latent entries are not malformed solely
because their layer is currently absent.

Entries with malformed layer names remain malformed source data and
are rejected according to the source validation rules.

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
