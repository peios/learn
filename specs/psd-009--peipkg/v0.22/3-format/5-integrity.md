---
title: Integrity
---

A package's integrity is verified at two levels:

- The **package level**: the entire `.peipkg` file has a
  hash and a signature that prove the file as a whole has
  not been altered since it was signed.
- The **per-file level**: each payload file has an
  individual hash that proves the file's content has not
  been altered between archive creation and installation.

## Per-file integrity manifest

Each package's tar archive contains a per-file integrity
manifest at `.peipkg/files.json`. The integrity manifest is
a JSON document conforming to the schema in this section.

### Schema

```json
{
  "schema_version": 1,
  "algorithm": "sha256",
  "entries": [
    {
      "path": "<string>",
      "size": <integer>,
      "hash": "<hex string>"
    }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `schema_version` | integer | MUST be 1 in this specification. |
| `algorithm` | string | Hash algorithm. MUST be `sha256` in this specification. |
| `entries` | array | One entry per regular-file payload entry. |

### Entry schema

| Field | Type | Description |
|---|---|---|
| `path` | string | Payload-relative path, identical to the corresponding tar entry path. |
| `size` | integer | Size in bytes of the file's content. |
| `hash` | string | Lowercase hexadecimal hash of the file's content using the declared algorithm. |

The `entries` array MUST be sorted lexicographically by
`path`.

### Coverage

The integrity manifest MUST contain exactly one entry per
regular-file payload entry in the tar archive. It MUST NOT
contain entries for:

- Metadata entries under `.peipkg/`
- Directory entries
- Symlink entries

A regular-file payload entry without a corresponding entry
in the integrity manifest, or an entry in the integrity
manifest without a corresponding tar entry, is INVALID and
MUST cause the package to be rejected on parse.

> [!INFORMATIVE]
> Symlinks are integrity-checked via the tar entry's
> linkname directly; they have no content body to hash.
> Directories have no content. The integrity manifest
> covers only the files whose content is verifiable by hash.

## Package hash

The package hash is the hash of the entire `.peipkg` file
(the compressed tar archive) computed with the algorithm
declared in the repository index (§6.2). The default and
required-supported algorithm is SHA-256.

The package hash is recorded in:

- The repository index (§6.2), to verify the downloaded
  file matches what the repo advertises.
- The signature payload (§5.1), to bind the signature to
  this exact file.

The package hash is NOT recorded inside the package itself.
A package cannot contain its own hash.

## Verification flow

A consumer verifying a package MUST perform the following
steps in order:

1. Compute the SHA-256 of the downloaded `.peipkg` file.
2. Compare against the hash recorded in the repository
   index (§6.2). If they differ, the package is corrupted
   or substituted; abort.
3. Verify the inline signature (§5.3). If verification
   fails, the package's authenticity is unproven; abort.
4. Decompress and parse the tar archive.
5. Read `.peipkg/manifest.json` and verify it parses
   against the schema in §3.3.
6. Read `.peipkg/files.json` and verify it parses against
   the schema in §3.5.1.
7. For each payload entry: compute its content hash and
   compare against the corresponding entry in
   `.peipkg/files.json`. If any file's hash does not match,
   abort.
8. The package is verified.

A consumer MUST NOT install any payload before all eight
steps complete successfully. Partial installation in the
event of verification failure leaves the system in an
indeterminate state and is forbidden.

A consumer MUST NOT make any decompressed payload bytes
visible to other processes (including via staging
directories that are reachable from outside the package
manager's own process tree) before signature verification
(step 3) has succeeded. Streaming decompression and
hashing is permitted; observable filesystem effects are
not.

> [!INFORMATIVE]
> The "in order" requirement is logical, not temporal. A
> consumer MAY compute the hashes for steps 1, 3, and 7 in
> a single streaming pass over the package data:
> simultaneously feeding the compressed bytes through a
> SHA-256 hasher (for step 1) and a zstd decompressor;
> piping the decompressed bytes through a second SHA-256
> hasher up to the signature entry (for step 3); and
> hashing each file's content as it is encountered in the
> tar walk (for step 7). The constraint is that no payload
> is committed to its final install path, and no
> decompressed bytes are made visible outside the package
> manager's own private state, until every step has
> completed successfully.

## Decompression bounds

A consumer MUST enforce upper bounds on package
decompression to prevent resource-exhaustion attacks via
maliciously-constructed packages with extreme compression
ratios.

Two bounds apply:

1. The repository index entry's `size_compressed` and
   `size_installed` fields (§6.2.4) bound the legitimate
   sizes of the compressed and uncompressed forms. A
   consumer MUST verify, during streaming decompression,
   that:
   - the cumulative compressed bytes consumed do not
     exceed `size_compressed` by more than the lesser
     of 1% or 16 MiB;
   - the cumulative decompressed bytes produced do not
     exceed `size_installed` by more than the lesser of
     1% or 16 MiB. The allowance accommodates tar
     header overhead and metadata files.
2. Independent of index-declared sizes, a consumer MUST
   abort decompression if the cumulative decompressed
   output exceeds an absolute cap. The default absolute
   cap is 4 GiB; the cap MAY be raised by operator
   configuration but MUST NOT be raised silently.

Exceeding either bound MUST cause the package to be
rejected with no further processing and no payload
committed to disk.

> [!INFORMATIVE]
> Constructed zstd payloads can achieve compression ratios
> exceeding 10000:1, which would let a 10 MB malicious
> package decompress to terabytes. The cumulative-size
> check is therefore on every chunk of decompressed
> output, not just at end-of-stream. The 1% allowance for
> index-declared sizes accounts for tar block padding and
> the small metadata files (manifest, files.json,
> signature) whose total size is a few KB.

## Hash algorithm agility

This version of the specification supports SHA-256 only.

The `algorithm` field in `.peipkg/files.json` and the hash
identifier in the repository index reserve syntactic space
for future algorithms. A future version of this
specification MAY introduce additional algorithms; consumers
of v0.22 MUST reject any algorithm value other than
`sha256`.

> [!INFORMATIVE]
> BLAKE3 is a likely future addition for performance on
> large packages. The reservation in this version means a
> migration to BLAKE3 can be additive: producers continue
> to emit SHA-256 for v0.22 compatibility while a future
> version permits BLAKE3 as well.

## Tampering and partial trust

The two-level integrity model defends against different
threats:

- The package hash plus signature defends against malicious
  substitution of the package as a whole.
- The per-file integrity manifest defends against
  corruption or tampering during extraction, after the
  signature has been verified.

A consumer MUST verify both levels. Verifying only the
package signature without checking per-file hashes leaves
extraction errors and on-disk corruption undetectable;
verifying only per-file hashes without checking the
signature leaves the manifest itself untrusted.
