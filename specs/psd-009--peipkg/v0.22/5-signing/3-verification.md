---
title: Verification
---

This section defines the procedure a consumer MUST follow
to verify a signed package and the meaning of a successful
verification.

## When verification happens

A consumer MUST verify a package's signature before
extracting any payload to disk. Verification is part of the
overall verification flow defined in §3.5.3:

1. Compute SHA-256 of the downloaded `.peipkg` file.
2. Compare against the index-recorded hash.
3. Verify the signature (this section).
4. Decompress and parse the archive.
5. Validate the manifest, files manifest, and integrity
   manifest.
6. Verify per-file hashes during extraction.

A consumer MUST NOT extract a package's payload if any of
these steps fails. A consumer MUST NOT mark a package as
installed in its database if signature verification fails.

## Verification procedure

To verify a package's signature, a consumer MUST:

1. Decompress the `.peipkg` file (zstd → uncompressed tar
   bytes).
2. Walk the tar archive in order, accumulating the byte
   stream of each entry's complete blocks (header +
   content + content-block padding) in a buffer until
   reaching the entry at path `.peipkg/signature`.
3. Stop at the `.peipkg/signature` entry. The buffer now
   contains the signed bytes (§5.1.2).
4. Parse the content of the `.peipkg/signature` entry as
   the signature envelope JSON (§5.1.3).
5. Validate the envelope's `schema_version` and
   `algorithm` fields. Reject if either is unrecognised.
6. Look up the public key by `key_fingerprint` in the
   trust set scoped to the originating repository (§5.2.5).
   If no matching key is in the trust set, reject.
7. Compute the SHA-256 of the buffered signed bytes.
8. Verify the signature against the SHA-256 hash using
   the looked-up public key per RFC 8032.
9. If verification succeeds, the signature is valid. If it
   fails, reject the package.

> [!INFORMATIVE]
> The walk in step 2 ensures the consumer reads exactly the
> bytes the producer signed. The signed bytes are everything
> in the tar archive up to (but not including) the
> signature entry; everything after the signature entry
> (the signature entry itself and trailing zero blocks)
> is not signed.

> [!INFORMATIVE]
> The "buffer" in step 2 is conceptual. An implementation
> MAY hash the signed bytes incrementally as they are
> walked, without retaining the whole stream in memory.
> Steps 7 and 8 then operate on the running hash state
> directly.
>
> Streaming MUST NOT be conflated with early commitment.
> A consumer that hashes incrementally MUST still defer
> any externally-observable filesystem effect (writes to
> any location reachable from outside the package
> manager's private state) until step 9 has succeeded
> per §3.5.3.

## Failure conditions

The following conditions MUST cause a consumer to reject a
package as unverified:

1. The package contains no `.peipkg/signature` entry, AND
   the consumer's trust policy for the originating
   repository requires signed packages.
2. The `.peipkg/signature` entry is not the last named
   entry in the tar archive.
3. The signature envelope JSON does not parse.
4. The signature envelope's `schema_version` is not 1.
5. The signature envelope's `algorithm` is not recognised
   by the consumer.
6. The signature envelope's `key_fingerprint` does not
   match any public key in the trust set scoped to the
   originating repository.
7. The cryptographic verification of the signature against
   the signed bytes fails.

A rejected package MUST NOT be installed. The consumer
MUST report which condition triggered the rejection.

## What verification proves

A successfully verified package signature establishes:

- **Integrity**: the bytes of the tar archive (preceding
  the signature entry) have not been altered since
  signing.
- **Authenticity**: the signer had access to the private
  key corresponding to the trusted public key at the time
  of signing.

Verification does NOT establish:

- That the signed bytes encode meaningful content. The
  consumer MUST still parse and validate the manifest,
  files manifest, and per-file integrity (§3.5).
- That the signing party intended the package's contents
  to be installed in any particular system. Trust in the
  signing party is the operator's responsibility, expressed
  by including the key in the trust set.
- That the package's content is free of bugs, malicious
  behavior, or compatibility issues with the target
  system. Signing certifies provenance, not safety.

## Verification and integrity

Successful signature verification implies that the entire
signed payload is intact. This includes the manifest, the
files manifest, and the payload entries.

Subsequent per-file integrity checks (§3.5.3) defend
against errors during extraction, on-disk tampering, or
storage corruption between extraction and use. Without
per-file verification, signature verification alone
cannot detect post-extraction corruption.

The two verification levels (signature + per-file hashes)
together provide end-to-end integrity from signing to
installed state.

## Replay and substitution

Signature verification by itself does not prevent replay
attacks (an attacker substituting an older, validly-signed
package for a newer one). Defence against substitution is
provided by:

- The repository index (§6.2), which is itself signed and
  declares the current authoritative version of each
  package.
- The hash of each package recorded in the index, which
  binds a specific signed package file to that index
  entry.

A consumer MUST consult the repository index and verify
the package's hash against the index before accepting the
package, even if its signature verifies (§3.5.3).

> [!INFORMATIVE]
> An old signed package whose signature still validates
> against a still-trusted key would otherwise be
> indistinguishable from the current package. The index's
> per-package hash binds "what's current" to "this exact
> file", closing the substitution gap.
