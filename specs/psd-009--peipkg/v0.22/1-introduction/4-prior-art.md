---
title: Prior Art
---

peipkg draws on established package management conventions
from multiple ecosystems. The container format is closest to
Arch's `pkg.tar.zst`; the version model is closest to Debian;
the repository protocol is closest to pacman's repo database.
None of these models is adopted wholesale -- each was chosen
for the specific concerns it solves well.

## Arch Linux

Arch's package format (`pkg.tar.zst`) is the structural
inspiration for the peipkg container (§3.1). Both use a
tarball compressed with Zstandard, with metadata files at
known paths inside the archive and deterministic file
ordering for reproducibility.

peipkg diverges from Arch's format in three ways:

- Arch uses ad-hoc key=value text files (`.PKGINFO`,
  `.MTREE`) for metadata; peipkg uses JSON.
- Arch's package signature is detached (a separate `.sig`
  file alongside the package); peipkg signatures are inline
  (a signature file inside the archive, signing everything
  before it).
- Arch repositories are rolling-only with no first-class
  archive of historical versions; peipkg requires retention
  of every version ever shipped (§6.3).

## Debian

Debian's version scheme
(`[epoch:]upstream_version-debian_revision`) is the structural
model for peipkg versioning (§2.2). The distinction between
epoch, upstream version, and distro revision captures the
constraints of repackaging upstream software without a
vendor relationship to upstream.

peipkg diverges from Debian in version comparison rules.
Debian's algorithm has accumulated edge cases over thirty
years; peipkg adopts SemVer-style pre-release ordering rules
(§2.2) within the upstream version component to keep
comparison predictable.

## pacman repository database

pacman's repository database structure -- a single index
file plus per-package files in a predictable directory
layout -- is the structural model for the peipkg repository
protocol (§6). The protocol is fully static-HTTP-fetchable
and requires no server-side computation.

peipkg's index format is JSON rather than a tar of text
files. The two-tier active/archive split (§6.2, §6.3) and
indefinite version retention (§6.3) are peipkg additions
not present in pacman.

## Considered alternatives

OCI registries and npm-style per-package endpoints were
considered as repository models. Both were rejected:

- OCI registries require a server-side protocol
  implementation, which conflicts with the static-HTTP
  hosting goal.
- npm-style per-package endpoints are necessary at scales
  exceeding a few thousand packages but require many HTTP
  requests per resolution. peipkg's expected scale (a few
  hundred to a few thousand packages) does not justify the
  cost.
