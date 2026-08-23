---
title: Verifying a Signature
description: The streaming verification procedure, how the end of the signed range is located, and every condition that fails it.
---

To verify a package's signature, a consumer MUST:

1. Decompress the `.peipkg` file to the uncompressed tar bytes.
2. Walk the tar archive in order, accumulating each entry's complete
   blocks — header, content, and content-block padding — until reaching
   the entry at path `.peipkg/signature`.
3. Stop at that entry. What has been accumulated is the signed byte
   range of §5.28.
4. Parse the content of `.peipkg/signature` as the signature envelope.
5. Validate the envelope's `schema_version` and `algorithm`. Reject if
   either is unrecognised, naming the version mismatch where that is the
   cause.
6. Look up the public key by `key_fingerprint` in the trust set scoped
   to the originating repository (§5.29). If no matching key is in that
   trust set, reject.
7. Determine whether the key is usable for verification given its status
   (§5.32). Reject a revoked key, and a transitioning key past its
   validity, **before** performing any cryptographic operation.
8. Compute the SHA-256 of the signed bytes.
9. Verify the signature against that hash with the looked-up key, per
   RFC 8032.

If step 9 succeeds the signature is valid. If it fails, reject the
package.

> [!NOTE]
> Step 7 before step 9 is deliberate. A revoked key's signatures are
> rejected *regardless of cryptographic validity*, so checking status
> first means a revoked key can never produce a "signature verified"
> result anywhere in the implementation, even transiently.

## Streaming

The accumulation in step 2 is conceptual. An implementation MAY hash the
signed bytes incrementally as it walks, without retaining the stream;
steps 8 and 9 then operate on the running hash state.

Streaming MUST NOT be conflated with early commitment. A consumer
hashing incrementally MUST still defer every externally observable
filesystem effect until step 9 has succeeded (§5.26).

## Locating the end of the signed range

A verifier computing the signed range by subtracting a fixed header size
from a stream offset MUST account for an extended header block preceding
the signature entry. §5.11 makes such a header unnecessary for a
short-named entry, but a verifier that assumes it away will
mis-locate the range for any archive that carries one, and report a
signature failure for what is really a framing difference.

## Failure conditions

A consumer MUST reject a package as unverified when any of these holds:

1. The package contains no `.peipkg/signature` entry **and** the trust
   policy for its originating repository requires signed packages.
2. The `.peipkg/signature` entry is not the last named entry in the
   archive.
3. The envelope does not parse, or carries an unknown or duplicate
   field.
4. The envelope's `schema_version` is not 1.
5. The envelope's `algorithm` is not recognised.
6. The envelope's `key_fingerprint` matches no key in the trust set
   scoped to the originating repository.
7. The matching key's status does not permit verification.
8. The cryptographic verification fails.

A rejected package MUST NOT be installed, and the consumer MUST report
which condition triggered the rejection.

> [!NOTE]
> Condition 2 is not redundant with §5.12's ordering rule; it is the
> same rule stated where its consequence is visible. Everything after
> the signature entry is unsigned, so a consumer that tolerates a
> trailing entry has accepted attacker-chosen bytes inside a package
> whose signature verifies.

## A package with no originating repository

A consumer MAY accept a package supplied directly rather than fetched
from a configured repository — a file handed to it on the command line.
Such a package has no originating repository, and therefore no trust set
to verify against.

A consumer that accepts one MUST treat it as unverified: it MUST NOT
report the package as signature-verified, and it MUST surface to the
operator that the package's authenticity was not established.

## What verification proves

A verified signature establishes **integrity** — the archive bytes
preceding the signature entry have not been altered since signing — and
**authenticity** — the signer held the private key corresponding to a
trusted public key at the time of signing.

It does not establish that the signed bytes encode meaningful content: a
consumer MUST still validate the manifest, the files manifest, and the
per-file integrity (§5.26). It does not establish that the signer
intended the package for any particular system. And it does not
establish that the content is free of bugs or malice. Signing certifies
provenance, not safety.

## Replay and substitution

Signature verification alone does not prevent replay — an attacker
substituting an older, validly signed package for a newer one. Defence
against substitution comes from the repository index (§5.33), which is
itself signed, declares the current authoritative version of each
package, and records each package's hash.

A consumer MUST consult the index and verify the package's hash against
it before accepting the package, even when the signature verifies.

> [!NOTE]
> An old signed package whose signature still validates against a
> still-trusted key is otherwise indistinguishable from the current one.
> The index's per-package hash binds "what is current" to "this exact
> file", which is what closes the gap.
