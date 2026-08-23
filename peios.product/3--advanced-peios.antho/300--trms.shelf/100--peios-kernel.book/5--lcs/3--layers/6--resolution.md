---
title: Resolution
description: Turning several per-layer entries into one effective answer — the rule, why unknown layers are latent rather than wrong, and enumeration.
---

Layer resolution turns several per-layer entries into one effective
answer. It is the mechanism that makes the registry layered, and it is
the same algorithm for path entries and for values — one resolves
existence claims, the other resolves data.

## The rule

Every candidate is a tuple `(precedence, sequence, entry)`. The winner
is the maximum, ordered by precedence first and sequence second.

Building the candidate list:

1. For each entry the source returned, look up its layer in the current
   layer table. An entry naming a layer that is not in the table is
   **skipped**, not rejected.
2. Discard entries from layers that are not active for this thread — a
   layer is active if it is globally enabled or its name is in the
   thread's private layer set (§5.3.5).
3. For values, add every blanket tombstone on the key as a tombstone
   candidate for the requested name, at its own precedence and
   sequence (§5.2.7).
4. If there are no candidates, the answer is not-found.
5. Take the maximum. A winning HIDDEN path entry, a winning
   `REG_TOMBSTONE` value entry, and a winning blanket all mean
   not-found.

That is the whole algorithm. Everything the layer system does —
override, revert, mask, hide, hide-and-replace — is a consequence of
it.

## Unknown layers are latent, not wrong

An entry tagged with a well-formed layer name that is not currently in
the table is a valid **latent** entry. It is ignored while the layer is
absent, and if a layer with the same folded identity is later created,
that entry becomes eligible for resolution under the new metadata.

This is what makes restore, import and boot ordering work: source
storage can legitimately hold entries before their metadata has been
loaded. It also follows the core rule — sources persist entries, LCS
decides their meaning.

Normal operations do not create such entries. A layer-targeting ioctl
naming a layer that is not in the table returns `ENOENT`. Latent
entries come from existing storage, from a restore or import, from a
previous boot, or from source behaviour. Since sources are trusted,
a well-formed latent entry is not malformed merely because its layer is
absent right now.

An entry whose layer *name* is malformed is a different matter, and is
rejected as malformed source data.

## Enumeration

Enumerating values collects the unique names across all layers and
resolves each one, returning only those whose answer is not not-found.
Enumerating subkeys collects the unique child names and resolves each,
returning those that map to a GUID rather than HIDDEN.

"Unique" means folded-unique. Two entries whose names differ only in
case are one name, which is the only reading consistent with names
being case-insensitive.

A caller sees effective state only. Tombstoned values, blanket-masked
values and hidden keys are simply absent. Per-layer raw data is never
visible through a normal operation.

## Enumeration is index-based, and that has a cost

`REG_IOC_ENUM_VALUES` and `REG_IOC_ENUM_SUBKEYS` return one entry at an
index. Each call re-resolves the full set and returns the entry at that
position, so walking `0..N-1` performs N full resolutions — O(n²) work
overall.

For a key with a handful of values that does not matter.
`REG_IOC_QUERY_VALUES_BATCH` exists for when it does: one call, the
whole effective value set, one resolution.

Enumeration order is not defined, and the index-to-entry mapping can
change between calls if the effective set changes. Indices must not be
cached across mutations. The batch call is also the way to get a
consistent snapshot.

## Neither party can lie about ordering

Two rules stop a source manipulating the outcome.

A source-returned entry whose sequence number is greater than or equal
to the next sequence LCS would allocate is **malformed data**. Sources
store the numbers LCS assigns them; they cannot legitimately hold a
future one. Without this, a compromised source could fabricate a
sequence number and win every tie in its own hive. Every entry in a
response is validated this way, whatever layer it names.

Duplicate sequence numbers at the same precedence, where they would
actually have to be compared to pick a winner, are also malformed. LCS
rejects the response rather than making an arbitrary choice. Duplicates
that never get compared are not an error.

Both produce `EIO` and an `LCS_SOURCE_VALIDATION_FAILURE` audit event
(§5.4.4).
