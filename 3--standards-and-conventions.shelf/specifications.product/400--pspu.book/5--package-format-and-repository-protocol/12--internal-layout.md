---
title: Internal Layout
description: Metadata entries under the reserved prefix and payload entries beneath — which are required, in what order, and which entry types are permitted.
---

A package's tar entries divide into **metadata** entries under a
reserved prefix and **payload** entries — the files that will be
installed.

## The reserved prefix

Every metadata entry MUST appear under the path prefix `.peipkg/` at the
archive root. That prefix is reserved: a payload entry MUST NOT use any
path beginning with `.peipkg/`, and no payload entry may be named
literally `.peipkg`.

## Required entries

| Entry path | Purpose | Section |
|---|---|---|
| `.peipkg/manifest.json` | Authoritative package metadata | §5.18 |
| `.peipkg/files.json` | Per-file integrity manifest | §5.25 |
| `.peipkg/signature` | Inline package signature | §5.28 |

`.peipkg/manifest.json` and `.peipkg/files.json` MUST be present in
every package. `.peipkg/signature` MUST be present in every signed
package; a package without it is *unsigned* (§5.28).

## Entry order

Tar entries MUST appear in exactly this order:

1. `.peipkg/manifest.json`
2. `.peipkg/files.json`
3. Any optional metadata entries, sorted lexicographically by path
4. All payload entries, sorted lexicographically by path (§5.11 rule 1)
5. `.peipkg/signature`

The manifest comes first so that a streaming consumer can read a
package's identity and reject a mismatched one — wrong name, wrong
version, wrong architecture — before reading any payload.

The signature comes last because it signs everything preceding it
(§5.28). A consumer MUST reject a package in which any named entry
follows `.peipkg/signature`.

## Optional metadata entries

A package MAY carry additional entries under `.peipkg/`. The set this
specification recognises is fixed at the three above; an unrecognised
entry under `.peipkg/` MUST be ignored on parse and MUST NOT prevent
installation.

When present, an optional metadata entry MUST appear between
`.peipkg/files.json` and the first payload entry.

> [!NOTE]
> A future version may introduce build attestations, reproducibility
> manifests, or a software bill of materials as further metadata
> entries. A producer targeting that future version MAY emit them into a
> package conforming to this one; a consumer conforming to this version
> ignores them.

## Permitted entry types

A payload entry MUST be one of:

- a regular file (typeflag `0` or `\0`)
- a directory (typeflag `5`)
- a symbolic link (typeflag `2`)

Any other entry type MUST cause the package to be rejected. This
excludes hardlinks (typeflag `1`), character devices (`3`), block
devices (`4`), FIFOs (`6`), contiguous files (`7`), and every
vendor-specific type.

> [!NOTE]
> Hardlinks are excluded because they share an inode with their target,
> which would let a package install a payload entry aliasing an existing
> system file and so gain shared access to it. Kernel hardlink-creation
> permissions provide some defence, but excluding the entry type at the
> format level is simpler and removes the class entirely. Device, FIFO,
> and contiguous entries have no use in a package payload.
