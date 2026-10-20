---
title: Keys and Fingerprints
description: Ed25519 keys — their encoding, how a fingerprint is computed, the key roles, and what makes up a repository's trust set.
---

## Algorithm

Signatures use Ed25519 as defined in RFC 8032. A conforming
implementation MUST support Ed25519 signing and verification. Other
algorithms are reserved for future versions.

> [!NOTE]
> Ed25519 was chosen for a small public key (32 bytes) and signature (64
> bytes), deterministic output with no nonce-reuse risk, fast
> verification, resistance to most side channels, and broad library
> support.

## Public key encoding

A public key is the raw 32-byte Ed25519 public key value of RFC 8032
§5.1.5.

When published as a file, a public key MUST be encoded either as the raw
32 bytes, or as a PEM `PUBLIC KEY` block per RFC 7468 in the
SubjectPublicKeyInfo form. Tooling MUST accept both.

A published public key file MUST contain only the public key, in one of
those two encodings.

## Fingerprint

A public key's fingerprint is the lowercase hexadecimal SHA-256 of the
**raw 32-byte public key**:

```
fingerprint = lowercase_hex(sha256(public_key_bytes))
```

The fingerprint is 64 hexadecimal characters. It is computed over the
raw key bytes and never over a PEM or SubjectPublicKeyInfo encoding of
them.

The fingerprint is the canonical identifier of a public key throughout
this chapter: the signature envelope's `key_fingerprint` (§5.28) and the
repository descriptor's signing key declarations (§5.31) both use this
form.

A consumer that fetches a public key MUST verify the key's fingerprint
against the fingerprint that identified it before admitting it to a
trust set.

> [!NOTE]
> Fingerprints SHOULD be displayed to people in a form that makes a
> mismatch visually obvious — conventionally four-character groups
> separated by spaces or colons. The normative on-wire form remains the
> unbroken 64-character lowercase hex string.

## Key roles

Two roles are distinguished by usage, not by structure:

- **Signing keys** are used by a producer to sign packages, descriptors,
  and indexes.
- **Trusted keys** are configured into a consumer as keys whose
  signatures it accepts.

A single key MAY play both roles.

## The trust set

A consumer maintains a **trust set**: the public keys whose signatures it
accepts.

The trust set MUST be partitioned per repository. Each configured
repository contributes its declared signing keys to the trust set,
scoped to that repository's content.

A signature MUST be accepted only if its `key_fingerprint` matches a key
in the trust set **scoped to the repository the content was fetched
from**.

> [!NOTE]
> Cross-repository acceptance is forbidden. A package fetched from
> repository R and signed by a key trusted only for repository S MUST be
> rejected, even though both keys are in the consumer's overall
> configuration. Without this, a compromised low-trust repository could
> serve packages whose signatures verify against a high-trust key, which
> is an escalation from one context to the other.

## Private keys

Private key material is not the concern of this specification. Its
generation, storage, custody, and rotation are operational matters for
the key holder.

Hardware security modules, threshold signing schemes, and air-gapped
signing are all compatible with this format, so long as the resulting
signature conforms to the envelope of §5.28. This specification cares
about the bytes, not how they were produced.
