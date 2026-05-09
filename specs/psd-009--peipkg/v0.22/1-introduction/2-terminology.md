---
title: Terminology
---

This specification introduces terms specific to package
management. Terms defined in other PSDs are used here with the
same meaning and are not redefined.

- **Package**: A signed binary distribution artifact. The unit
  of build, distribution, and installation. A package contains
  one or more files, metadata describing its identity and
  dependencies, and a signature.

- **peipkg**: This specification, the package format it defines,
  and the package manager tool that consumes the format. Where
  ambiguous, the spec uses "the format", "the protocol", or
  "the tool" to disambiguate.

- **Manifest**: A JSON document inside each package that
  declares its identity, dependencies, side-effect
  requirements, and payload integrity. The manifest is the
  authoritative metadata for a package.

- **Repository (repo)**: A collection of packages addressable
  as a unit. A repo is identified by its descriptor URL.

- **Repo descriptor**: A small JSON document at a well-known
  path within a repository describing the repo's identity,
  signing key, and pointers to its indexes.

- **Index**: A signed JSON document listing the packages
  available in a repository. Each repository has an active
  index and an archive index.

- **Active index**: The index listing the current version of
  each package. The default index for routine operations.

- **Archive index**: The index listing every version of every
  package ever shipped by a repository. Used for downgrade,
  version pinning, and forensic queries.

- **Side-effect declaration**: A flag in the manifest
  indicating that a standard Linux maintenance operation
  (ldconfig, depmod, man-db) is to be invoked after install.
  The complete set of declarable side-effects is enumerated
  normatively (§4.3).

- **Custom repository**: A repository hosted by a party other
  than the official Peios project. Custom repositories use
  the same protocol and trust model as the official
  repository.

- **Build farm**: The infrastructure that produces packages.
  Operational concerns are out of scope for this specification
  (see appendix A).

- **Epoch, upstream version, peios revision**: The three
  components of a package version string. Defined in §2.2.
