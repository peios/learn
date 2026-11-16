---
title: Scope and Roles
description: What this chapter specifies, a package, the artifact directory that stores it, the closures composed from it and the repositories that publish it, its roles, and what it leaves out.
---

This chapter specifies how Peios software is packaged, stored, composed and
published. A **package** is a manifest listing every path it installs, with
each file's content stored separately as a blob named by its hash. Packages
live in an **artifact directory**, are composed into **closures**, each the
contents of a `/usr`, and are published by **repositories**, artifact
directories that say what they publish and sign it.

`ppk(1)` implements this chapter. Where this chapter and ppk disagree, the
disagreement is a defect in one of them, to be resolved by changing one.

## Roles

| Role | Does |
|---|---|
| **Producer** | Packs a directory into a package (§5.18) |
| **Publisher** | Makes an artifact directory a repository and signs it (§5.36) |
| **Consumer** | Fetches, verifies, resolves, and composes packages (§5.26, §5.29) |

One program commonly plays every role. Each requirement says which role it
binds; §5.38 collects them by role.

## In scope

- Package names, capabilities, versions, constraints, and architectures
  (§5.3 to §5.8).
- The artifact directory, its blobs, manifests and refs (§5.10 to §5.12).
- What a package can install, and the form of its manifest (§5.13 to
  §5.23).
- Closures, their inventory, and their names (§5.24, §5.25, §5.27).
- Environment profiles and resolution (§5.28, §5.29).
- Repositories: their catalog, indexes and channels, their pointer file
  and its signature, and how a machine is configured to fetch from them
  (§5.30 to §5.36).

## Out of scope

- **How an installed system boots** from a closure. The names it uses for
  its closures are reserved here (§5.27); the rest is the installer's.
- **The kernel's verification of a file's signature.** A package carries a
  file's PIP signature (§5.16); PSPK book 3 specifies the signature and its
  check.
- **Network transport other than HTTP.** A repository is a directory, which
  a static web server can serve as it is over HTTP or HTTPS (§5.34). Other
  transports are reserved for a future version.
- **Registry seeds and other system policy** that a release carries. They
  are packaged as files and applied by other components.

## Relationship to other chapters

The root skeleton file a package can ship is PSPU book 11. Security
descriptors are PCDS's. File signatures are PSPK book 3's.
