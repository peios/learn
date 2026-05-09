---
title: Package Signature
---

A package signature binds a package's bytes to a signing
key. Verifying the signature establishes that the package
has not been altered since signing and that the signer had
access to the trusted private key.

## Signature entry

The package signature is stored as the final entry in the
tar archive at path `.peipkg/signature` (§3.2.3).

The entry's content is a UTF-8 JSON document conforming to
the schema in §5.1.3. All tar entry attributes — permission
bits, owner identity, mtime, magic, and the rest — follow
the determinism rules in §3.1.4 unmodified. The signature
entry is therefore mode `0777` like every other entry; the
0777 rule's "honest signalling" rationale (§3.4.6) applies
identically to metadata entries.

## Signed payload

The signature signs a SHA-256 hash computed over the
concatenation of all uncompressed tar bytes preceding the
`.peipkg/signature` entry, in archive order.

Specifically, the signed bytes are the concatenation of:

- The complete tar entry blocks (header + content +
  content-block padding to the next 512-byte boundary) for
  every entry that precedes `.peipkg/signature`, in archive
  order.

The signed bytes do NOT include:

- The tar entry header or content of `.peipkg/signature`
  itself.
- The two trailing zero blocks that conventionally
  terminate a tar archive.
- Any compression artifacts (signing operates on the
  uncompressed tar bytes).

> [!INFORMATIVE]
> Compressing the signed tar with zstd produces the on-wire
> `.peipkg` file. Compression is independent of signing:
> the same signed tar can be compressed with different zstd
> levels and verify identically once decompressed.

## Signature envelope

The content of `.peipkg/signature` is a JSON document with
the following schema:

```json
{
  "schema_version": 1,
  "algorithm": "ed25519",
  "key_fingerprint": "<hex string>",
  "signature": "<base64 string>"
}
```

| Field | Type | Description |
|---|---|---|
| `schema_version` | integer | MUST be 1 in this specification. |
| `algorithm` | string | Signature algorithm. MUST be `ed25519` in this specification. |
| `key_fingerprint` | string | Fingerprint of the public key (§5.2.3). Lowercase hex, 64 characters (the full SHA-256 hex). |
| `signature` | string | The signature value, base64-encoded per RFC 4648 §4 without padding. For Ed25519, the decoded signature is 64 bytes. |

A signature envelope MUST contain all four fields. Missing
or unrecognised algorithm or schema_version values cause
the package to be rejected.

The envelope MUST NOT contain extra fields. Future
specification versions may extend the schema with additional
fields; v0.22 implementations parsing a future envelope MUST
reject the package with a clear error indicating the schema
version mismatch rather than silently ignoring unknown
fields. (This is a deliberate exception to the
forward-compatibility rule for manifest fields (§3.3.3): for
security-critical signing data, strict parsing is
preferred over permissive ignoring.)

## Determinism

Given identical signed bytes and identical signing key, the
Ed25519 signature value is deterministic per RFC 8032 §5.1.6.

A producer that builds the same tar archive (with all
determinism rules per §3.1.4 satisfied) and signs with the
same key MUST produce a byte-identical `.peipkg/signature`
entry.

## Construction procedure

To sign a package, a producer MUST:

1. Construct all tar entries except `.peipkg/signature` per
   chapters 3 and 4.
2. Serialise these entries as an uncompressed tar byte
   stream in archive order.
3. Compute the SHA-256 hash of the resulting byte stream.
4. Sign the hash with the producer's Ed25519 private key per
   RFC 8032.
5. Construct the signature envelope JSON with the resulting
   signature value and key fingerprint.
6. Append the `.peipkg/signature` entry (header + JSON
   content + padding) to the tar byte stream.
7. Compress the complete tar byte stream with zstd to
   produce the `.peipkg` file.

## Unsigned packages

A package without a `.peipkg/signature` entry is *unsigned*.

The package format permits unsigned packages: a package
manager MAY install one if the source repository's trust
policy (§6.5) permits unsigned packages.

> [!INFORMATIVE]
> The official Peios repository requires signatures. Custom
> repositories may permit unsigned packages for development,
> homelab, or air-gapped scenarios. The package format
> itself is permissive; trust policy is enforced by the
> consumer based on per-repository configuration.

A package without a `.peipkg/signature` entry MUST otherwise
conform to all other format requirements in chapter 3. The
manifest, files manifest, payload, and integrity rules
apply identically to signed and unsigned packages.
