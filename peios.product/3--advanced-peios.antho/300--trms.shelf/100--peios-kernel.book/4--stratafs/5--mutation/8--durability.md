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

Disk quota keys on the POSIX owner, and copy-up preserves it (§4.5.2):
the staged object is created with the calling task's credentials, and
the ownership is then set to the source's under the mount's own
credential. [*durability.copy-up-preserves-posix-owner] A copy is therefore accounted to the owner of the object
it was copied from, not to the caller who caused it. [*durability.copy-up-accounted-to-preserved-owner]

The KACS security descriptor, including its owner SID (§4.6.3), is
preserved alongside it. [*durability.copy-up-preserves-owner-sid] The two notions of owner agree, and both
name the object rather than whoever provoked the copy — which is what
§4.6.2 relies on when it permits a caller to cause a copy into a
directory they hold no rights over.

Ownership is what accounting follows; the caller who caused the copy is
recorded in the audit record of §4.6.5 instead.
