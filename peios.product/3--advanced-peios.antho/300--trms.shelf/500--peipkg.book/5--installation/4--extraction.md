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

That is the default and it is what the overwhelming majority of entries
get. Inheritance is expressed by the *absence* of a descriptor, not by
peipkg computing one.

### Overrides

A package may declare a descriptor for a specific entry, through the
manifest's `sd_overrides` (PSPU §3.3.5). Every override is checked
before anything is installed — the descriptor decodes from base64,
stays inside the size limit, and parses; the list is sorted and free of
duplicates; and each path names a real payload entry that is not a
symlink. §5.20 requires all of that to happen up front, because
deferring it to the moment a descriptor is applied turns a malformed
package into a partially completed install.

Overrides are applied last, after the payload is written and after any
signature attributes are stamped. A descriptor can withhold `WRITE_DAC`
from the installing process, so nothing may still be waiting to be
written when one takes effect.

Where the descriptor lands depends on the entry:

| Entry | Stamped on |
|---|---|
| Regular file | its staged sibling, before the commit rename |
| Directory | its final path, after the payload beneath it exists |

Stamping a file before the rename means it becomes visible already
carrying its descriptor, rather than briefly wearing an inherited one.
A directory has no staged sibling — it is created at its final path —
so it is stamped in place once its children are there.

If the kernel rejects a descriptor, most often because it names a
principal the system does not know, the install fails and rolls back.
It is never warned past.

### The override policy

The kernel checks that a declared descriptor is well-formed. Nothing
checks that the package's producer had any authority over the principals
it grants access to, and §5.20 makes that the consumer's question.

peipkg answers it per repository, from `allow_sd_overrides` in the
repository's configuration. A package carrying overrides from a
repository that does not permit them is **refused** — not installed with
the overrides quietly dropped, which §5.20 forbids by name. A package
declaring no overrides is unaffected: the policy gates declaring
descriptors, not installing.

Every override applied is listed in the install report.

> [!NOTE]
> This is a deliberate subset of §5.20. The spec also asks for each
> override to be shown to the operator with a diff against what
> inheritance would have produced, and for a per-repository allowlist of
> the principals an override may name. Both require peipkg to compute
> KACS inheritance itself in order to render the diff. Until a
> repository exists that is neither wholly trusted nor wholly refused,
> the per-repository switch enforces the binding rule and leaves the
> graduated middle unbuilt rather than half-built.

## Hashing

Per-file content hashes are verified during the verification pass, over
the same immutable in-memory bytes that extraction then reads. The
package is fully hash-checked before a single staged file is written.

Extraction itself re-checks nothing. The guarantee that what lands on
disk is what was hashed rests on both passes reading the same buffer,
which every current caller arranges by handing extraction a reader over
already-verified bytes in memory.
