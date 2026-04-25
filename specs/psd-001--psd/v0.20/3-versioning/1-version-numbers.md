---
title: Version Numbers
---

## SemVer synchronisation

PSD versions MUST use Semantic Versioning (`MAJOR.MINOR.PATCH`), synchronised with the Peios software version. When a specification is updated, it MUST take the version number of the software release that the change ships with.

The patch component MUST be omitted when it is zero. `v0.22` is correct; `v0.22.0` is not.

> [!INFORMATIVE]
> This synchronisation means specification versions are sparse and irregular. KACS might go v0.20 → v0.22 → v0.56.1 because all the versions in between belonged to other subsystems or software changes. This is expected -- the version number tells you when in the release timeline the specification was updated, not how many revisions it has had.

## Complete editions

Each version of a specification MUST be a complete, self-contained edition. Versions are not diffs or patches on previous versions. A reader MUST be able to understand the specification from a single version directory without consulting other versions.

## Revision count

Each specification has a revision count equal to the number of version directories under its specification directory. The revision count MUST NOT be stored explicitly -- it is derived from the filesystem.

> [!INFORMATIVE]
> Trail renders the revision count in the specification header. Example: `PSD-004 — KACS v0.56.1 (revision 3)`. The SemVer tells you when in the release timeline the specification was last updated. The revision count tells you how many times it has been updated. Together they answer both "is this current?" and "is this mature?".
