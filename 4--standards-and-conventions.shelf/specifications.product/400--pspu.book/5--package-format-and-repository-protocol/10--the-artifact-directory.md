---
title: The Artifact Directory
description: Where packages are stored, the layout of an artifact directory, its blobs, manifests, refs and closures, and why everything in it but its refs is named by its hash.
---

An **artifact directory** holds packages. A machine's own is its **store**,
`/system/artifacts`. A repository is an artifact directory that also
publishes what it holds (§5.30).

## Layout

| Path | Holds |
|---|---|
| `blobs/sha256/<hash>` | A file's content, not executable (§5.12) |
| `blobs/sha256/<hash>.exec` | The same content, executable |
| `blobs/sha256/<hash>.<entry>` | The content of a file with security metadata, carrying it |
| `manifests/sha256/<hash>` | A manifest, named by the hash of its bytes (§5.18) |
| `refs/<name>/<version>/<arch>` | The identity of that package (§5.11) |
| `closures/<hash>/` | A closure's tree (§5.24) |
| `closures/<hash>.manifest` | The closure's manifest |
| `closures/<name>` | A closure's name (§5.27) |

A repository adds its trees, `trees/sha256/<hash>`, its pointer file,
`repository`, and its signature, `repository.sig` (§5.30).

## What is named by its hash

Everything in an artifact directory but its refs, its closures' names and a
repository's pointer file is named by the hash of what it holds, and so
never changes once written. Writing one that already exists MUST leave it
as it is if its content is the same, and MUST fail if it isn't.

A file is written whole, in a temporary file beside where it goes, then
renamed into place, so that a reader never sees part of one.

## Modes

Blobs and manifests are read-only: mode 0444, or 0555 for an executable
blob. A blob is a hard link of every file a closure holds with its content
(§5.24), so a change to one would change every closure that has it.
