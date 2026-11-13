---
title: Blobs
description: A file's content stored once, by its hash, in one form for each mode, and as a file of its own when it carries security metadata.
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
