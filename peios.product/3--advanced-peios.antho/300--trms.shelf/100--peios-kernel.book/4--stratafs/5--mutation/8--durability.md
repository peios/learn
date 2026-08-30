---
title: Durability and Accounting
description: stratafs holds no storage, so durability and accounting belong to the providers — except where a merged directory needs a rule of its own.
---

stratafs holds no storage, so durability is the providers' and the
accounting is theirs too. Two operations nonetheless need a rule,
because a merged directory has no single provider to forward to.

## Synchronising an object [*durability.fsync-follows-the-descriptor]

Synchronising a non-directory is forwarded to the object the descriptor
resolved to — the descriptor's own provider file — and reports what
that object's filesystem reports. No path re-resolution happens, so it
is never forwarded to whichever object currently provides the path.
Where the two differ, the data the caller wrote is on the object it
opened, and synchronising anything else would report success while
leaving that data unsynchronised.

Where a copy-up has occurred through this descriptor, the descriptor's
object is the copy, and it is the copy that is synchronised. The
retired pre-copy-up file (§4.5.7) is not.

## Synchronising a merged directory [*durability.dirsync-covers-every-stratum]

Synchronising a merged directory synchronises the corresponding
directory in **every** stratum of the mount that holds it at the time
of the call, and fails if any of them fails. The loop continues past a
failure, so every stratum is still attempted, and the first error is
what is returned.

The set is evaluated when the operation runs, not when the descriptor
was opened: the directory is re-resolved across all strata rather than
read from the participant set settled at open (§4.3.4). Both halves of
that matter:

- Evaluating at call time catches a directory the create stratum did
  not hold when the descriptor was opened and does now — which is
  exactly what happens when a file is created through that descriptor
  and §4.5.3 materialises its parent.
- Covering every stratum rather than the provider alone is required by
  the atomic-replace pattern of §4.5.5, whose rename is performed in
  the stratum that provided the *source*, which need not be the stratum
  providing the merged directory.

Durability is a question about what is on disk now, which is why this
is the one place a merged directory is treated as its current set of
real directories rather than as the thing a descriptor was opened
against.

## Freezing [*durability.freeze-eopnotsupp]

A stratafs mount has no storage to quiesce. Freezing returns
`EOPNOTSUPP` and propagates nothing to any stratum's filesystem; no
unfreeze, freeze-super or thaw-super operation is registered at all.
Freezing the filesystem a stratum lives on is done through that
filesystem, and affects the merged view as it affects any other reader
of that stratum.

## Accounting

Storage consumed by an object created through the mount, or copied up
into the create stratum, is consumed on the create stratum's filesystem
and accounted there. [*durability.storage-charged-to-create-stratum]

Which principal it is accounted to is not what the specification
describes. Disk quota keys on the POSIX owner, and copy-up does not
preserve it: the staged object is created with the calling task's
credentials, and the metadata copy transfers only the mode and the
modification time. [*durability.copy-up-copies-mode-and-mtime] A copy is therefore accounted to the caller who
caused it, not to the owner of the object it was copied from. [*durability.copy-up-accounted-to-the-caller]

What *is* preserved is the KACS security descriptor, including its
owner SID (§4.6.3), so the descriptor-level owner is the source's. [*durability.copy-up-preserves-owner-sid] The
two notions of owner diverge here, and only the descriptor one behaves
as §4.6.3 requires. This is tracked as a defect.

No code alters ownership to redirect accounting; the divergence is one
of omission. The audit record of §4.6.5 is where the causing caller is
recorded.
