---
title: Registration
description: Recording what the install will mean — why the manifest is stored, and how file ownership is written down.
---

Once a package's files are staged, peipkg records what the install will
mean:

- the package's identity — name, version, architecture, and root;
- the repository it came from;
- the install timestamp;
- every payload path it owns, with the type and content hash of each;
- its manifest, stored whole, so that later operations can consult the
  package's own declarations without the package file.

These rows are written inside the transaction's database commit and
become visible only when that commit succeeds.

## Why the manifest is stored

Several later operations need a package's own declarations rather than
an index entry's copy of them: reconciling claims after an unrelated
install, computing what a removal breaks, and re-deriving a role's
claim-path set. Keeping the manifest means those operations do not
depend on a repository still being configured, or still existing.

## Ownership

A file is owned by the package whose install created it. Ownership is
what makes uninstall, `peipkg owns`, and the collision constraint
possible, and it is recorded per path rather than per package prefix.

Directories are recorded as owned but are shared: several packages may
own the same directory, and the collision constraint applies only to
non-directory entries.
