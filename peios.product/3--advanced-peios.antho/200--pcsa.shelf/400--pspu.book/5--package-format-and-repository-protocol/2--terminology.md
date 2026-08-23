---
title: Terminology
description: The terms this chapter defines — package, manifest, root, repository — used with these meanings throughout.
---

- **Package** — a binary distribution artifact: one or more files,
  metadata describing its identity and relationships, and, when signed,
  a signature. The unit of build, distribution, and installation.

- **Manifest** — the JSON document at `.peipkg/manifest.json` inside a
  package that declares its identity, relationships, side-effect
  requirements, and build provenance. The manifest is authoritative for
  a package's metadata (§5.18).

- **Files manifest** — the JSON document at `.peipkg/files.json`
  carrying one content hash per regular payload file (§5.25).

- **Payload** — the tar entries of a package that are not metadata: the
  files, directories, and symlinks it installs.

- **Repository** — a collection of packages addressable as a unit,
  identified by its base URL.

- **Repository descriptor** — the small JSON document at a well-known
  path within a repository declaring its identity, signing keys, and the
  locations of its indexes (§5.31).

- **Index** — a signed JSON document listing packages available from a
  repository. Every repository publishes two: an **active index**
  (§5.33) listing the current version of each package, and an **archive
  index** (§5.35) listing every version ever shipped.

- **Virtual name** — a capability name, rather than a package name, that
  a package may require or provide (§5.4).

- **Role** — a virtual name that several installed packages may contend
  to own on the filesystem, with at most one *holding* it (§5.23).

- **Claim** — the binding of a contended filesystem name (a *claim
  path*) to a file supplied by the package that holds a role (a
  *target*).

- **Holder** — the single installed package that currently owns a role.
  A role with no holder is *unheld*.

- **Side-effect declaration** — a manifest flag naming a standard
  maintenance operation to be invoked after install, drawn from a closed
  set (§5.24).

- **Installation root** — a self-contained filesystem tree into which
  packages are installed. The default root is the system root; a system
  may define others (§5.19).

- **Epoch**, **upstream version**, **peios revision** — the three
  components of a version string (§5.5).

- **Trust anchor** — a key fingerprint supplied to a consumer
  out-of-band, against which a repository's descriptor signature is
  first verified (§5.37).
