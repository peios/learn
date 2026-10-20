---
title: Restoring
description: Restoring is a replace rather than a merge — root remapping, GUID rules, parent validation, sequence remapping, and how layers survive.
---

Restoring is a **replace**, not a merge. The target key's contents and
descendants are removed before the stream's contents are written.

The whole operation — teardown and rebuild together — MUST be atomic.
There is no partial-restore mode, and a store that cannot offer
atomicity cannot be a restore target.

## The target key survives

A restore is performed against a key that already exists. That key
**object** is not replaced: its GUID, its parent, its name, its
volatile flag and its symlink flag remain what they were and MUST NOT
be taken from the stream.

What the stream's root `KEY` record supplies is the mutable part — the
Security Descriptor and the last write time — which MUST be written to
the target inside the restore.

The root record's immutable flags MUST **match** the target's. A backup
of a volatile key restored onto a non-volatile one, or a symlink onto a
non-symlink, MUST be rejected.

## Root remapping

`HEADER.RootGUID` is stream-local. Every reference to it — a
`PATH_ENTRY`'s `ParentGUID` or `ChildGUID`, a `VALUE` or
`BLANKET_TOMBSTONE`'s `KeyGUID` — MUST be remapped to the target key's
existing GUID **before** any validation of parent references and before
any record is applied.

The backup root GUID MUST NOT be created as a new key record.

Descendant `KEY` records keep their backup GUIDs, which are written
into the target verbatim.

## GUID rules

- The stream MUST contain exactly one `KEY` record whose GUID equals
  `HEADER.RootGUID`, and it MUST be the first `KEY` record.
- A non-root GUID MUST NOT appear twice in the stream.
- A non-root GUID MUST NOT equal the restore target's GUID.
- A non-root GUID that already exists **outside** the subtree being
  replaced is a collision and the restore MUST fail. A reader is not
  required to detect this before beginning; it MAY surface during
  replay, in which case the atomicity requirement ensures nothing is
  left behind.

## Parent validation

Before a path entry is applied, its `ParentGUID` — after root remapping
— MUST be either the restore target's GUID or the GUID of a non-root
`KEY` record **already processed** earlier in the stream. A parent
outside the stream's remapped key set MUST cause the restore to fail.

This is what prevents a crafted backup from injecting path entries into
arbitrary parts of the existing namespace, outside the subtree being
replaced. It is not optional.

A HIDDEN `PATH_ENTRY` is held to a stricter rule: its remapped
`ParentGUID` MUST equal the GUID of the section it appears in, not
merely some already-processed key.

## Creating a key

A `KEY` record carries no name and no parent, so both come from the
section's path entries.

The **anchor** is the first GUID-bearing `PATH_ENTRY` in the section,
in stream order, whose remapped `ChildGUID` equals the `KEY` record's
GUID. Its remapped `ParentGUID` and its `ChildName` are the parent and
name the key is created with.

- If the section contains no GUID-bearing path entry targeting the
  `KEY` record's GUID, the restore MUST fail.
- If any GUID-bearing `PATH_ENTRY` in a non-root section targets a
  *different* GUID after remapping, the restore MUST fail.
- HIDDEN entries do not satisfy the anchor requirement. They are
  parent-owned records for the key being created and are replayed only
  after it exists.

The key's `LastWriteTime` MUST be written immediately after it is
created, before any of the section's other records are replayed.

Path entries for the **root** section are handled differently:
GUID-bearing ones are not restored, because the target key's existing
incoming path entries remain authoritative. HIDDEN entries in the root
section are parent-owned records for the restore root and MUST be
restored, after parent validation.

## Sequence remapping

The backup's sequence numbers preserve its internal layer-resolution
ordering. A restore is a new mutation, and its entries MUST become
newer than everything already present while keeping that internal
order. A reader MUST NOT write backup sequence numbers through
unchanged.

Remapping MUST preserve streamability: it MUST NOT require a seekable
input or a pre-scan pass. Before the first layer-qualified record is
applied, the reader records an offset — the next sequence number it
would allocate — and then, for every restored layer-qualified record:

```
new_sequence = restore_sequence_offset + backup_sequence
```

That needs no lookahead: the running maximum is computed during the
single pass.

The offset is held stable for the duration of the restore, so that no
other sequence-allocating mutation can interleave. Reads are not
blocked by it. A restore containing no layer-qualified record at all
need not reserve one.

If a remapped value would reach or exceed `U64_MAX`, the restore MUST
fail. The valid remapped range is `[offset, U64_MAX)`; `U64_MAX` itself
is never a valid sequence number.

When the restore reaches any terminal state — success, abort, failure
or cancellation — the global counter MUST be advanced past the highest
number the restore dispatched, and that advance MUST NOT be rolled
back. Numbers a failed restore dispatched become unused gaps, exactly
like those of any other failed write.

Dispatch order remains structural stream order. It is the remapped
numbers, not the order they were sent in, that preserve the backup's
internal layer resolution.

## Layers in a restored stream

`LAYER` manifest records define nothing (§5.3). If restored entries
reference a layer that is not in the live layer table, and the stream
does not also restore that layer's metadata subtree as ordinary
registry data, those entries become latent unknown-layer entries and
are ignored during resolution until real metadata exists. If the
metadata subtree **is** included, it is restored through the ordinary
path, and those records are what define the layer.

## Privilege

A restore replaces every Security Descriptor in the subtree it covers,
so the privilege to perform one effectively confers descriptor control
over everything within its reach.

Before any key record is written, a reader MUST check the layer
manifest: if any declared layer has a precedence above 0, **or** any
existing layer with the same folded identity does, the caller MUST hold
the privilege that guards high-precedence layers, or the restore MUST
be aborted before a single byte is written.

Records in the stream that create or raise persisted layer metadata
above precedence 0 are subject to the same check as an ordinary write
would be. Neither check is redundant: the first covers what the
manifest declares, the second covers what the stream actually writes.

## Validation before mutation

A reader MAY validate the entire stream — including the trailer's
record count and checksum — before applying any of it. Doing so is
stronger than this specification requires, and it means a corrupt
stream is rejected before anything is torn down rather than after. The
cost is memory rather than seeking, since the records must be retained
across the teardown.

A reader that instead validates as it goes MUST still guarantee that a
checksum failure leaves nothing applied, which the atomicity
requirement already demands.
