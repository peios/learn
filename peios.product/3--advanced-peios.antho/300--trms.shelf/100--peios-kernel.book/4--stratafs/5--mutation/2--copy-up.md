---
title: Copy-Up
description: Replicating an object from its provider into the create stratum — parents, what is replicated, staging and atomicity.
---

Copy-up replicates an object from its provider stratum into the create
stratum, at the same path relative to the mount root, so that a
modification can be applied without modifying the provider. [*copy-up.replicates-into-create-stratum]

Every step runs inside a KACS copy-up context, which exempts the
mechanics from caller authorisation without granting anything. §3.9.7
describes that context in full; §4.6.3 covers the stratafs side of the
bargain.

## Parents

Where the create stratum does not hold the directories containing the
object's path, they are created first, walking the relative path
component by component from the create-stratum root downwards. Each is
created as an empty directory with the mode of the corresponding
**merged provider** directory, and with that directory's security
descriptor, installed by KACS during the create phase rather than
inherited. [*copy-up.materialises-missing-parents]

Contents are not copied. The directories exist to hold the copied
object; the entries they hold in lower strata continue to be reached by
merging.

Where the create stratum holds one of those components as something
other than a directory, the copy-up fails with `ENOTDIR` and the
operation requiring it fails. The blocking entry is not removed or
replaced — there is no `unlink`, `rmdir` or `rename` anywhere on the
parent-materialisation path. [*copy-up.parent-conflict-enotdir]

Materialised parents receive a mode and a descriptor, and nothing else:
no extended attributes and no timestamp preservation. [*copy-up.parents-mode-and-descriptor-only]

## What is replicated

| Provider type | Result in the create stratum |
|---|---|
| Regular file | A regular file with the same contents and mode [*copy-up.result.regular-file] |
| Symbolic link | A symbolic link with the same target [*copy-up.result.symlink] |
| Directory | An empty directory with the same mode; contents are not copied [*copy-up.result.directory] |

A device node, FIFO, or socket is never copied up. Anything that is not
a regular file, directory or symlink is refused with `EROFS` before a
copy-up begins. [*copy-up.non-copyable-refused]

The security descriptor is carried by KACS rather than replicated as an
attribute (§4.6.3). Every other extended attribute is copied, with
three exclusions: the canonical descriptor attribute, anything in the
`system.stratafs.` namespace, and the staging marker attribute. Each
is copied with `XATTR_CREATE`, and `security.capability` goes through a
dedicated KACS entry point rather than a raw write. [*copy-up.xattrs-copied-with-exclusions]

No attribute is silently discarded. Any per-attribute failure aborts
the copy-up, as does a listing that fails or exceeds `XATTR_LIST_MAX`;
in every case the error reported is `EIO`, whatever the underlying one
was. [*copy-up.xattr-failure-aborts-with-eio]

Modification timestamps are preserved for regular files and for
directories, and **not** for symbolic links, which receive the current
time. [*copy-up.mtime-preserved-except-symlinks] That is a divergence from the specification's `SHOULD` and is
tracked as a defect. Access and change times are not preserved for any
type. [*copy-up.atime-ctime-not-preserved]

**Ownership is not preserved.** The staged object is created with the
calling task's credentials, and the metadata copy transfers only the
mode and the modification time — there is no uid or gid transfer
anywhere. The KACS security descriptor, including its owner SID, *is*
preserved, so the descriptor-level owner is the source's; the POSIX
owner is the caller's. [*copy-up.posix-ownership-not-preserved] Since disk quota keys on the POSIX owner, a copy
is accounted to the caller who caused it rather than to the owner of
the object it was copied from, which is the opposite of what §4.5.8
describes. This is tracked as a defect.

Hard links are not preserved: an object with several links in its
stratum is copied up as a single independent object, and the other
links continue to refer to the original. [*copy-up.hard-links-not-preserved]

Contents are copied through a 64 KiB buffer, one read and one write per
iteration, with the inner write loop retrying short writes. Where the
copy-up was provoked by a path rather than a descriptor, the source is
reopened for each chunk; the staged file is reopened for each chunk
either way.

## The source must still be the provider

Before beginning a copy-up on behalf of a descriptor, the object the
descriptor refers to is verified still to be the provider of that name,
comparing both the path and the provider inode. Where it is not, the
copy-up is not performed and the operation fails with `ESTALE`. [*copy-up.source-must-still-be-provider]

The verification is repeated immediately before publication, under the
create directory's lock, and publication itself uses an operation that
fails if the target name already exists: linking an anonymous object
into place, or a `RENAME_NOREPLACE`. Both additionally test the target
dentry explicitly, and an `EEXIST` from either is normalised to
`ESTALE`. [*copy-up.publication-refuses-existing-name]

That is decisive for the case that matters. A competing copy-up
publishes into the same create-stratum directory, where the
filesystem's own atomicity applies, so exactly one of two racing
copy-ups succeeds and the other fails `ESTALE`. [*copy-up.one-racing-copy-up-wins]

It cannot extend further, and nothing tries to. Strata may be on
different filesystems, and stratafs can neither lock them together nor
inspect them at one instant. A change in some *other* stratum after the
second verification — a direct writer creating the name in a
higher-precedence stratum, say — is an ordinary concurrent structural
change, visible to the next resolution, and is neither an error nor
detected.

This is not a rare case. Every descriptor other than the one that
caused a copy-up still refers to the original object, so a second
descriptor opened before the copy-up meets this rule the first time it
writes. A caller therefore has to be prepared for a write to fail
`ESTALE` on a descriptor that was valid when it was opened and has done
nothing wrong. §4.8 records it.

## Staging and atomicity

A copy-up is never observable in a partial state. All content,
attribute and metadata work happens on an object that is not reachable
through the mount, and publication is a single step. [*copy-up.never-partially-observable]

Two arrangements are used, chosen by type:

- A **regular file** is staged as an anonymous object on the create
  stratum's filesystem — a kernel tmpfile — and linked into place when
  complete. No reader can reach it.
- A **directory or symlink** is staged under a name in the create
  stratum, since neither has an anonymous form, and published by a
  no-replace rename.

A staged name is `.stratafs-stage-` followed by the mount cookie and a
per-stage identifier, in a 64-byte buffer, with up to eight retries on
collision. It is excluded from resolution and from enumeration for the
mount that owns it, and removed if the copy-up fails. [*copy-up.staged-entries-hidden] The exclusion is
local: a second stratafs mount sharing the create stratum, and every
direct reader of that directory, sees an ordinary entry containing a
partial copy. [*copy-up.staging-hidden-only-locally]

### Identifying staging entries

A staged name alone is not proof of ownership, so each staged object
also carries a marker in the extended attribute
`security.peios.stratafs_staging`. The marker is a 24-byte
little-endian structure: a magic of `0x53544731` — ASCII `STG1` — a
version, its own size, a per-boot cookie, and the cookie of the mount
that created it. [*copy-up.staging-marker-format]

Recovery of an orphan is therefore precise. A staged entry whose marker
is valid and whose owning mount is not live is removed; one belonging to
a live mount is left alone, and so is one whose marker is missing,
short, or carries the wrong magic, version or size. [*copy-up.orphan-recovery-checks-marker] That matters
because two mounts may share a create stratum, and an unqualified
cleanup would have each new mount destroy the other's copy-up in
flight.

The scan runs in batches of 128 names, with resume, and is triggered
from five places: mounting, opening a directory, looking up a name
beginning with the staging prefix, copying up into a directory, and the
emptiness test of §4.5.4 where it finds a directory empty but saw
staging entries in it.

The fifth exists because the other four only reach directories somebody
visits. An orphan in a directory that is never opened, looked up, or
copied into would otherwise never be removed, and the emptiness test —
which filters staging entries — would report its parent empty and let
an `rmdir` proceed that then failed at the provider. Recovering on that
path costs nothing until someone actually meets the case, and reaches
directories that a recursive walk of the create stratum at mount would
have to visit every one of to find.

The marker is removed after publication. A failure to remove it is only
warned about, leaving the marker on the published copy until a later
lookup cleans it. [*copy-up.marker-removed-after-publication]

Where a copy-up fails for any reason, the create stratum is left with
no new entry at the target path and the operation fails. [*copy-up.failure-leaves-no-entry] Nothing falls
back to a weaker replication: an object whose descriptor or extended
attributes could not be preserved is never published. A published copy
whose descriptor handoff then fails is rolled back. [*copy-up.rolled-back-on-handoff-failure]

## Concurrent modification

The provider may be modified while it is being copied, by a writer that
does not know stratafs exists.

Copy-up reads the provider as any reader would, with no locking of the
source and no snapshot, and offers no stronger consistency than an
ordinary read of that object. Where the provider is modified during the
copy, the copy may contain bytes from more than one state of the
source, exactly as a concurrent `read` of the same object may. [*copy-up.no-source-snapshot]

Nothing detects that and restarts — there is no retry loop, no
generation check. Equally, nothing blocks waiting for a quiescent
source, and nothing fails a copy-up merely because the source is being
written.

What *is* guaranteed is that the published object never appears in a
partial state, because staging and publication are properties of the
create stratum's filesystem, which stratafs does control.

Once published, the copy is independent of its source. Subsequent
modifications to the object it was copied from are not reflected in it,
and are not visible through the mount for as long as the copy provides
the name. [*copy-up.independent-once-published]
