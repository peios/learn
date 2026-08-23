---
title: Backup
description: Writing a subtree to a stream under SeBackupPrivilege with no per-key access check — the snapshot, the audit, and what is written.
---

`REG_IOC_BACKUP` exports the key on the fd and its entire subtree to
another fd.

It requires `SeBackupPrivilege` and performs **no per-key AccessCheck**
whatsoever. The privilege is the whole authorisation, which is why the
operation is audited unconditionally (§5.4.4). The output fd must be
writable, or `EBADF`.

## The snapshot

Before reading anything, LCS opens a **read-only** source transaction —
`RSI_BEGIN_TRANSACTION` with mode `RSI_TXN_READ_ONLY` — so that the
whole export is a point-in-time snapshot. Concurrent mutations do not
appear part-way through the stream.

That transaction is **released with `RSI_ABORT_TRANSACTION` and never
committed**. There is no commit call anywhere in the backup path; a
read-only transaction has nothing to commit.

A source that does not support read-only snapshots answers
`RSI_TXN_NOT_SUPPORTED` and the backup fails `ENOTSUP`. A source
already holding `MaxReadOnlyTransactionsPerSource` snapshots (default
16) yields `EBUSY` — which bounds snapshot-holding without treating
backups as write-lock holders, since they are not.

Backing up an orphaned key is `ENOENT`: it is no longer a reachable
subtree root (§5.2.9).

## Audit

`LCS_BACKUP_START` is emitted **before any subtree data is read**, and
if it cannot be emitted the backup returns `EIO` and does not start.
`LCS_BACKUP_COMPLETE` is emitted afterwards, carrying the result, and a
failure to emit it cannot change a result that has already happened.

## What is written

The stream is a header, the layer manifest, then each key in
depth-first pre-order with its path entries, values and blanket
tombstones, then the trailer. The exact shapes are in the PSPK chapter.

Two things about the exporter are worth stating here, because they
constrain a reader more tightly than the format does.

The exporter writes **no GUID-bearing path entries for the backup
root**. The root's section contains only its hidden entries. A reader
tolerates and skips them if some other writer produces them, but this
one does not emit them, because on restore the target key's existing
name is authoritative and they would be discarded anyway.

Hidden entries belong to the **parent's** section, not to a section of
their own — a hidden entry has no key to have a section for. A hidden
entry masking a name where no key exists in any layer is still valid;
it expresses "this layer hides this name" whether or not anything is
there to hide.

The layer manifest is written from the live layer table, and it is a
manifest: it records what the layers looked like at backup time so that
a restore can validate the stream against them. It is not a backup of
the layer definitions. A layer definition is backed up only when
`Machine\System\Registry\Layers\<Name>\` is itself inside the subtree
being exported, in which case it is ordinary key and value data like
anything else.
