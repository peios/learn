---
title: Terminology
description: The terms this chapter defines, package, identity, artifact directory, closure, request, repository, index and channel, used with these meanings throughout.
---

**Package**
: A manifest (§5.18) and the blobs it names. A package is identified by its
  name, version and architecture, and its content by its identity.

**Package ID**
: `<name>@<version>?arch=<architecture>`, as
  `dev.peios.hello@1.0-1?arch=x86_64`.
  The `?arch=` part MAY be left out where an architecture is implied.

**Identity**
: `sha256:` followed by the lowercase hexadecimal SHA-256 hash of some
  bytes. A package's identity is its manifest's (§5.11).

**Blob**
: A file's content, stored once, and named by its hash (§5.12).

**Artifact directory**
: A directory holding packages: their blobs, manifests, and refs (§5.10). A
  machine's own is its **store**, `/system/artifacts`.

**Capability**
: A name a package provides or requires, such as a soname (§5.4).

**Closure**
: A set of packages composed into one directory tree, the contents of a
  `/usr` (§5.24).

**Inventory**
: The file at the top of a closure that records its packages and what wants
  each (§5.25).

**Request**
: What is asked for: a package by name, or a capability, at the versions
  that would do, and optionally from an index (§5.29).

**Resolution**
: Choosing a version of each package that requests need (§5.29).

**Profile**
: A file of requests, with what a composed root holds outside `/usr`
  (§5.28).

**Repository**
: An artifact directory that publishes what it holds, through a signed
  pointer file (§5.30).

**Catalog**
: Every version a repository has published (§5.30).

**Index**
: One version of each package, for each architecture, that a repository
  publishes together: `leading`, the newest, or a snapshot of a release
  (§5.30).

**Channel**
: A name that follows an index or another channel, such as `stable`
  (§5.30).
