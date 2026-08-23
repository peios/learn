---
title: Sources
description: Where a build's inputs come from — version control, fetched artifacts, local trees and patches — with signature verification and the lock.
---

`[source]` says where the upstream tree comes from. At most one
*reproducible* source may be declared — a version-control source or a
fetched artifact — and declaring both is an error.

## Version control

| Key | Meaning |
|---|---|
| `url` | Required |
| `ref` | Templated, defaulting to the version placeholder |
| `versions` | A constraint capping which upstream tags are eligible |
| `tag_regex` | A pattern filtering tags during version enumeration |

## A fetched artifact

| Key | Meaning |
|---|---|
| `url` | Required, templated |
| `extract` | Whether to unpack the artifact |
| `root` | The subdirectory of the unpacked tree that is the source root |
| `versions` | A constraint cap |
| `file_regex` | A pattern applied to a directory listing to enumerate versions |
| `checksum` | A single hash, or a table mapping version to hash |

### Signature verification

A `[source.url.signature]` block makes upstream signature verification
mandatory for that source.

| Key | Meaning |
|---|---|
| `url` | Templated; defaults to the source URL with a signature suffix |
| `of` | `artifact` or `decompressed` — which bytes the signature covers |
| `key_files` | Required and non-empty: the pinned public keys |
| `fingerprints` | An allowlist of acceptable signing fingerprints |

This is an entirely separate trust system from package signing. It
verifies that the *upstream* tarball is the one upstream published,
using upstream's own keys, pinned per recipe. It has no relationship to
the Ed25519 signature the resulting package carries.

## A local tree

`[source.local].path` names a directory relative to the recipe root. It
is not a reproducible source and cannot be locked.

## Patches

`source.patches` names a single bare directory in the recipe root
containing a `series` file: a plain-text list of patches, applied in
order. It requires a reproducible source, since patching a local tree in
place would mutate the operator's own working copy.

## The lock

`pekit.lock` records what was actually fetched: for each source, the
version, the URL and content hash or the ref and commit, the signing key
that verified it, and when it was locked.

It is trust-on-first-use and tamper-evident afterwards: the first fetch
establishes the pin, and every later fetch is checked against it.

## Delegation

A recipe may `delegate` — declare that its build targets, environment,
wrapper, or package definitions come from the *fetched source tree*
rather than from the recipe. A delegating recipe is a thin pointer at a
project that carries its own packaging, and it is how a project whose
source tree already contains package definitions is distributed without
duplicating them.
