---
title: Blobs
description: A file's content stored once, by its hash, in one form for each mode, as a file of its own when it carries security metadata, and compressed in a repository that says so.
---

A **blob** is the content of a file of a package, uncompressed, in a file
of its own named by the SHA-256 hash of the content. Content that several
packages, or several paths, share is stored once.

## Forms

A blob is stored in the form each entry that names it needs:

- `blobs/sha256/<hash>`, mode 0444, for a file that is not executable;
- `blobs/sha256/<hash>.exec`, mode 0555, for an executable file;
- `blobs/sha256/<hash>.<entry>`, for a file with security metadata
  (§5.16, §5.20): `<entry>` is the hash of the entry as the manifest
  writes it, after its path and ` = `. Such a blob carries the entry's
  descriptor and signature, so every hard link to it carries them too, and
  two files with the same content and different metadata are two blobs. Its
  mode is 0444, or 0555 if the entry is executable.

Content shipped both as executable and not is stored in both forms.

A file's PIP signature (§5.16) is itself a blob, named by its own hash.

## Verification

A consumer copying a blob MUST check that its content hashes to its name
before the blob is used, and a blob that doesn't MUST be refused.

## Compressed blobs

A repository whose pointer file has the line `blobs zstd` (§5.32) holds
every blob, in every form, as a zstd frame of its content (RFC 8878), under
the name its content gives it. Only blobs are compressed: tree nodes,
manifests, refs, the pointer file and its signature are not, and no
identity changes. Without the line, every blob is its content.

A store and every artifact directory that isn't such a repository hold
their blobs uncompressed, since a closure's files are hard links of them
(§5.24). A consumer copying a blob from a repository whose blobs are
compressed MUST decompress it, and MUST check that what it decompresses to
hashes to its name before the blob is named in the store. A blob that
doesn't, or that isn't a zstd frame, MUST be refused. A consumer MUST
refuse a blob that decompresses to more than 64 GiB, so that a small file
can't fill the store.

A repository whose blobs are compressed is usually an **export**: a copy
of a repository that stays uncompressed, written again from it after each
publication (§5.36).
