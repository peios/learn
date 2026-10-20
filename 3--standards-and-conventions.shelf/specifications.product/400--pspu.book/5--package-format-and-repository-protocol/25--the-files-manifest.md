---
title: The Files Manifest
description: Per-file integrity beneath the package-level hash — the schema, what it must cover, and the two threats the two levels answer.
---

A package's integrity is verified at two levels. At the **package
level**, the whole file has a hash and a signature proving it has not
been altered since signing. At the **per-file level**, each payload file
has an individual hash proving its content has not been altered between
archive creation and installation.

The per-file level lives in the files manifest at `.peipkg/files.json`.

## Schema

```json
{
  "schema_version": 1,
  "algorithm": "sha256",
  "entries": [
    { "path": "<string>", "size": <integer>, "hash": "<hex string>" }
  ]
}
```

| Field | Description |
|---|---|
| `schema_version` | MUST be 1 in this version. |
| `algorithm` | MUST be `sha256` in this version. |
| `entries` | One entry per regular-file payload entry. |

| Entry field | Description |
|---|---|
| `path` | Payload-relative path, identical to the corresponding tar entry path. |
| `size` | Size in bytes of the file's content. |
| `hash` | Lowercase hexadecimal hash of the file's content under the declared algorithm. |

The `entries` array MUST be sorted lexicographically by `path` and MUST
NOT contain duplicates.

## Coverage

The files manifest MUST contain **exactly one entry per regular-file
payload entry**, and MUST NOT contain an entry for a metadata entry
under `.peipkg/`, a directory entry, or a symlink entry.

A regular-file payload entry with no corresponding files-manifest entry
is invalid. A files-manifest entry with no corresponding tar entry is
invalid. Either MUST cause the package to be rejected on parse.

> [!NOTE]
> The correspondence is checked in both directions because each
> direction catches a different failure. A file with no entry is an
> unverifiable file smuggled into the payload; an entry with no file is a
> hash for something that was never shipped, which makes the manifest's
> own count untrustworthy.

Symlinks are integrity-checked through the tar entry's linkname
directly, and directories have no content. The files manifest covers
only what is verifiable by content hash.

## The package hash

The package hash is the hash of the entire `.peipkg` file in its
compressed on-wire form, computed with the algorithm declared in the
repository index (§5.33). The required algorithm in this version is
SHA-256.

It is recorded in the repository index, to verify that a downloaded file
matches what the repository advertises, and in the signature payload
(§5.28), to bind a signature to that exact file.

The package hash is **not** recorded inside the package: a package
cannot contain its own hash.

## Algorithm agility

This version supports SHA-256 only. The `algorithm` field here and the
hash identifier in the index reserve syntactic space for future
algorithms. A conforming implementation of this version MUST reject any
algorithm value other than `sha256`.

> [!NOTE]
> BLAKE3 is a likely future addition for performance on large packages.
> The reservation means such a migration can be additive: producers
> continue emitting SHA-256 for compatibility with this version while a
> future version permits BLAKE3 as well.

## Two levels, two threats

The two levels defend against different things, and a consumer MUST
verify both.

The package hash plus the signature defends against substitution of the
package as a whole. The files manifest defends against corruption or
tampering during extraction, after the signature has been verified.

Verifying only the signature leaves extraction errors and on-disk
corruption undetectable. Verifying only the per-file hashes leaves the
files manifest itself untrusted.
