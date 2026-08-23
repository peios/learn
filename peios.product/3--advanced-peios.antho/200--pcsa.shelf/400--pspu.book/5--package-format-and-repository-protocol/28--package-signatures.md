---
title: Package Signatures
description: What a signature binds, which bytes are signed, the envelope carrying it, and how an unsigned package is treated.
---

A package signature binds a package's bytes to a signing key. Verifying
it establishes that the package has not been altered since signing, and
that the signer held the trusted private key.

## The signature entry

The signature is the final entry in the tar archive, at
`.peipkg/signature` (§5.12). Its content is a UTF-8 JSON document. Every
tar attribute of the entry — mode, owner, mtime, magic — follows the
determinism rules of §5.11 unmodified, so the entry is mode `0777` like
every other, and §5.16's rationale applies to it identically.

## The signed bytes

The signature is over a SHA-256 hash computed across the concatenation
of every complete tar entry block — header, content, and content-block
padding to the next 512-byte boundary — for every entry **preceding**
`.peipkg/signature`, in archive order.

The signed bytes do **not** include:

- the tar entry header or content of `.peipkg/signature` itself;
- the two trailing zero blocks that terminate a tar archive;
- any compression artifact — signing operates on the uncompressed tar
  bytes.

> [!NOTE]
> Compressing the signed tar produces the on-wire file. Compression is
> independent of signing: the same signed tar compressed at different
> levels verifies identically once decompressed. This is what makes
> §5.10's inability to fix compression parameters harmless for
> authenticity.

## The envelope

```json
{
  "schema_version": 1,
  "algorithm": "ed25519",
  "key_fingerprint": "<hex string>",
  "signature": "<base64 string>"
}
```

| Field | Description |
|---|---|
| `schema_version` | MUST be 1 in this version. |
| `algorithm` | MUST be `ed25519` in this version. |
| `key_fingerprint` | Fingerprint of the public key (§5.29). Lowercase hex, 64 characters. |
| `signature` | The signature value, base64 per RFC 4648 §4 without padding. For Ed25519 the decoded value is 64 bytes. |

An envelope MUST contain all four fields. A missing field, or an
unrecognised `algorithm` or `schema_version`, MUST cause the package to
be rejected.

## Strict parsing

The envelope MUST NOT contain any field beyond the four above, and MUST
NOT contain a duplicate key. An implementation of this version parsing
an envelope from a future version MUST reject the package with an error
**naming the schema version mismatch**, rather than silently ignoring
the unknown fields.

This is a deliberate exception to §5.9's forward-compatibility rule. For
security-critical signing data, strict parsing is preferred to
permissive ignoring.

> [!NOTE]
> The error must name the version, not the field. An implementation that
> reports "unknown field `x`" when the real condition is "this envelope
> is from a newer specification version" sends the operator looking for
> a malformed package instead of an outdated tool.

## Signing procedure

To sign a package, a producer:

1. Constructs every tar entry except `.peipkg/signature`.
2. Serialises them as an uncompressed tar byte stream in archive order.
3. Computes the SHA-256 of that stream.
4. Signs the resulting 32-byte hash with its Ed25519 private key, per
   RFC 8032.
5. Constructs the envelope with the signature value and key fingerprint.
6. Appends the `.peipkg/signature` entry — header, JSON content, and
   padding — to the tar byte stream.
7. Compresses the complete stream to produce the `.peipkg` file.

Note that the Ed25519 message is the 32-byte SHA-256 digest, not the tar
stream itself. A verifier MUST do the same.

> [!NOTE]
> The digest indirection is deliberate and applies to every signature in
> this chapter, package and detached alike: one signature construction
> covers a small JSON index and a multi-gigabyte package, and the large
> case is verifiable in a single streaming pass without buffering.

## Determinism

Given identical signed bytes and an identical key, the Ed25519 signature
is deterministic per RFC 8032 §5.1.6. A producer that builds the same
tar archive and signs it with the same key MUST produce a byte-identical
signature entry.

## Unsigned packages

A package without a `.peipkg/signature` entry is **unsigned**.

The format permits unsigned packages. A consumer MAY install one if the
originating repository's trust policy permits it (§5.37).

An unsigned package MUST conform to every other requirement of this
chapter. The manifest, the files manifest, the payload rules, and the
integrity rules apply identically to signed and unsigned packages.

> [!NOTE]
> The official repository requires signatures. Other repositories may
> permit unsigned packages for development, homelab, or air-gapped use.
> The format is permissive; the policy is enforced by the consumer,
> per repository.
