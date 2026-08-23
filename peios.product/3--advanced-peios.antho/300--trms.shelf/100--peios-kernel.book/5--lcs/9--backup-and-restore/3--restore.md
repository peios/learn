---
title: Restore
description: Restore is a replace rather than a merge — one transaction, the surviving target key, the order of operations, and the precedence gate.
---

`REG_IOC_RESTORE` **replaces** the key on the fd and its entire subtree
from a stream. It is not a merge: the target's contents and descendants
are torn down before the stream's contents are written.

It requires `SeRestorePrivilege` and, like backup, performs no per-key
AccessCheck and is audited unconditionally. The input fd must be
readable, or `EBADF`, and restoring onto an orphaned key is `ENOENT`.

Because restore rewrites every descriptor in the subtree,
`SeRestorePrivilege` effectively confers `WRITE_DAC` and `WRITE_OWNER`
over everything within reach of one (§5.8.1).

## One transaction

The entire restore — teardown and rebuild together — is wrapped in a
single read-write source transaction. A source that answers
`RSI_TXN_NOT_SUPPORTED` for `RSI_TXN_READ_WRITE` cannot be a restore
target: restore requires atomicity and there is no partial-restore
mode. Every failure path aborts the transaction, so a failed restore
rolls back the teardown as well.

## The target key survives

The stream's header names a root GUID, and that GUID is **remapped** to
the already-open target key everywhere it appears — in parent
references, in child references, in value key references — before
anything is validated or dispatched.

The target key **object** is not replaced. Its GUID, parent, name,
volatile flag and symlink flag remain what they were; they are never
taken from the stream. What the stream's root record supplies is the
mutable part: the Security Descriptor and the last write time, written
to the target with `RSI_WRITE_KEY` inside the transaction.

The root record's immutable flags must **match** the target's. A backup
of a volatile key restored onto a non-volatile one, or a symlink onto a
non-symlink, is `EINVAL`.

Descendants keep their backup GUIDs. Those are written into the target
verbatim.

## Order of operations

1. Validate the whole stream, including the trailer's record count and
   checksum, and retain every replayable record.
2. Read the layer manifest and apply the precedence gate (below).
3. Verify the root record and its immutable flags against the live
   target.
4. Tear down the target's contents and descendants — path entries,
   values, blanket tombstones, and descendant key records — inside the
   transaction.
5. Write the root's mutable fields, then replay its section's values
   and blanket tombstones.
6. For each non-root key in stream order: create it, write its last
   write time, then replay its path entries, values and blanket
   tombstones.
7. Commit.

The stream is read from the fd exactly once, sequentially. Nothing
seeks, so a pipe is a valid input.

Validating the whole stream first is stronger than the format requires:
a checksum failure aborts before any source mutation rather than after
some. The cost is memory rather than seeking — the replayable records
are retained in kernel memory across the teardown.

## The precedence gate

Before any key record is written, LCS checks the layer manifest. If any
declared layer has a precedence above 0, **or** any existing cached
layer table entry with the same folded identity does, and the caller
does not hold `SeTcbPrivilege`, the restore aborts with `EPERM` before
a single byte reaches the source.

And if the stream contains ordinary key and value records for
`Machine\System\Registry\Layers\<Name>\`, writes that create or raise
persisted metadata above precedence 0 hit the ordinary inline
`SeTcbPrivilege` check as well (§5.3.4).

Both exist so that `SeRestorePrivilege` cannot be used to smuggle a
Group Policy-tier layer past the defence in depth that guards
precedence.

## Layers in a restored stream

Manifest records create, update, delete, enable, disable and authorise
nothing. If restored entries reference a layer that is not in the
current table, and the stream does not also restore that layer's
metadata subtree as ordinary registry data, those entries become latent
unknown-layer entries and are ignored during resolution until real
metadata exists (§5.3.6). If the metadata subtree *is* included, it is
restored through the ordinary path, and those records — not the
manifest — are what define the layer.

## Sequence remapping

Backup sequence numbers preserve the backup's internal ordering, but a
restore is a new mutation and its entries must outrank everything
already present. So the numbers are remapped rather than written
through.

Before dispatching the first layer-qualified record, LCS takes the
global sequence-allocation gate and records the current next sequence
as the offset. Every restored record is then written with
`offset + backup_sequence`, which preserves relative order while
placing the whole set above pre-restore state.

The gate is held until the restore reaches a terminal state. Other
sequence-allocating mutations wait; reads are not blocked. A restore
with no layer-qualified records at all never takes it.

If a remapped value would overflow, the restore fails `EOVERFLOW` — and
it fails at validation, before teardown, rather than part-way through.
The valid remapped range stops just below `U64_MAX`, which is never
handed out (§5.3.7).

When the restore reaches any terminal state — commit, abort, failure or
cancellation — LCS advances the global counter past the highest number
it dispatched, and **does not roll that back**. Sequence numbers a
failed restore dispatched become unused gaps, exactly like those of any
other failed write.

## GUID collisions

A GUID that appears twice in one stream, other than the root, is
`EINVAL`, and so is a non-root GUID equal to the target root's.

A non-root GUID that already exists **outside** the subtree being
replaced is `EEXIST` — but it is discovered by the source rejecting the
create during replay, not by a check beforehand. LCS has no index of
which GUIDs exist elsewhere, so the collision surfaces mid-restore, and
the transaction rolls back.

The parent of every path entry, after remapping, must be either the
restore root or a key record already processed earlier in the stream.
That check *is* made up front, and it is what stops a crafted backup
injecting path entries into arbitrary parts of the existing namespace
outside the subtree being replaced.

## Watches

A restore is an arbitrary subtree replacement and LCS retains no exact
before-and-after diff for it. On a successful commit it publishes the
affected hive's generation increment and dispatches a no-name
`OVERFLOW` to the armed watches on that source (§5.6.3). A restore that
fails or aborts before commit emits nothing.
