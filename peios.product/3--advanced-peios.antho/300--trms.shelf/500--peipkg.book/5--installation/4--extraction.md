---
title: Extraction
description: Payload entries processed in archive order into staged paths, with nothing at a final location yet — modes, descriptors and hashing.
---

Payload entries are processed in archive order. Nothing appears at a
final install path during this phase.

## Staging

Each regular file is written to a **staged sibling** of its destination:
a temporary name in the destination's own directory, carrying the
transaction identifier. Where a destination's basename is long enough
that adding the marker would exceed the filesystem's name limit, the
basename is truncated to fit.

Staging in the destination's own directory is what makes the commit-time
rename intra-directory, and therefore atomic and immune to failing
because the staging area is on another filesystem.

Directories are created as they are encountered, and every directory the
transaction creates is recorded so that a rollback can remove it again.
Symlinks are created with the linkname the tar entry carried, which was
validated at parse time and so is known safe by the time extraction
reaches it.

## Modes

Extraction ignores the tar entry's permission bits. Every file is
created mode `0755`, and every directory mode `0755`.

This follows from the format: a package's modes are all `0777` and carry
no information (PSPU §5.16), so the consumer has to choose something.
What it chooses is uniform and executable.

## Security descriptors

peipkg creates entries without supplying an explicit security
descriptor, so the kernel computes one by inheritance from the parent
directory at creation time.

Manifest-declared overrides are carried in the manifest and validated
for base64 decodability, decoded length, and sort order. They are not
checked against the payload — an override naming a path the package does
not ship, or naming a symlink, or decoding to bytes that are not a
security descriptor, is accepted — and they are not applied. No
descriptor peipkg supplies is ever an override.

The operator-facing policy of PSPU §5.20 — surfacing each override,
diffing it against inheritance, requiring confirmation for a non-official
repository — has nothing to act on as a result.

## Hashing

Per-file content hashes are verified during the verification pass, over
the same immutable in-memory bytes that extraction then reads. The
package is fully hash-checked before a single staged file is written.

Extraction itself re-checks nothing. The guarantee that what lands on
disk is what was hashed rests on both passes reading the same buffer,
which every current caller arranges by handing extraction a reader over
already-verified bytes in memory.
