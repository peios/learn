---
title: Key Management
---

This section defines the public key encoding, fingerprint
computation, and key publication conventions used by peipkg
signing.

## Algorithm

Signatures use Ed25519 as defined in RFC 8032.

A v0.22-conformant implementation MUST support Ed25519
signing and verification. Other algorithms are reserved for
future versions of this specification (§5.1.3).

> [!INFORMATIVE]
> Ed25519 was chosen for: small key size (32 bytes public,
> 32 bytes private), small signature size (64 bytes),
> deterministic signature output (no nonce reuse risk),
> fast verification, and resistance to most side-channel
> attacks. RFC 8032 is broadly implemented across
> cryptographic libraries.

## Public key encoding

A public key is the raw 32-byte Ed25519 public key value as
defined in RFC 8032 §5.1.5.

When a public key is published as a file, it MUST be
encoded as:

- The raw 32 bytes, OR
- A PEM-encoded `PUBLIC KEY` block per RFC 7468 (the
  SubjectPublicKeyInfo form).

A repository's published public key file (§6.1) MUST use
one of these two encodings, identified by file extension or
content sniffing. Tooling MUST accept both.

## Fingerprint

A public key's fingerprint is the lowercase hexadecimal
SHA-256 of the raw 32-byte public key:

```
fingerprint = lowercase_hex(sha256(public_key_bytes))
```

The fingerprint is 64 hexadecimal characters (256 bits).

The fingerprint is the canonical identifier of a public key
in this specification. The signature envelope's
`key_fingerprint` field (§5.1.3) and the repository
descriptor's signing key declaration (§6.1) both use this
form.

> [!INFORMATIVE]
> Fingerprints SHOULD be displayed to users in a form that
> permits visual comparison: typically split into four-
> character groups separated by spaces or colons. The
> normative on-wire form remains the unbroken 64-character
> lowercase hex string.

## Key roles

This specification distinguishes two key roles by usage,
not by structure:

- **Signing keys** are used by a producer (a build farm,
  the official Peios project, or a custom-repo operator) to
  sign packages.
- **Trusted keys** are configured into a consumer (a
  package manager) as keys whose signatures the consumer
  accepts.

A single key MAY play both roles. The structure of the key
is identical regardless of role; the role is determined by
how the key is used.

## Trust set

A package manager maintains a *trust set*: the collection
of public keys whose signatures the manager accepts.

The trust set is partitioned per repository: each
configured repository contributes its declared signing keys
to the trust set, scoped to that repository's packages.

A signature is accepted only if its `key_fingerprint`
matches a public key in the trust set scoped to the
repository the package was fetched from.

> [!INFORMATIVE]
> Cross-repository signature acceptance is forbidden. A
> package fetched from repository R signed by a key trusted
> only for repository S is rejected, even if both keys are
> in the package manager's overall trust set. This prevents
> a compromised custom repo from substituting maliciously
> signed packages from a more-trusted source.

## Key rotation

A repository MAY rotate its signing key by:

1. Generating a new key pair.
2. Adding the new public key to the repository's signing
   key list (§6.1) alongside the existing key.
3. Beginning to sign new packages with the new key.
4. After a transition period during which both keys are
   advertised, removing the old key from the signing key
   list.

During the transition, packages signed with either key are
acceptable to consumers. After the old key is removed, only
packages signed with the new key remain acceptable.

> [!INFORMATIVE]
> The transition period gives consumers time to fetch the
> updated repository descriptor and learn the new key
> before old-key signatures stop being honoured. The
> length of the transition period is operational policy,
> not specified normatively.

### Offline emergency rotation key

A repository SHOULD maintain at least one *offline*
active signing key in addition to its routine signing
key(s). The offline key's private material is stored
separately from build-farm infrastructure and is used
only for descriptor updates and emergency rotations.

The offline key defends against the chicken-and-egg
problem in compromise response: revoking a compromised
routine signing key requires publishing a new
descriptor, which itself must be signed. If the only
trusted key is the compromised one, the operator must
sign the revocation with the compromised key — giving
an attacker who holds the same key the ability to
substitute their own revocation that adds an
attacker-controlled key.

With an offline key, the operator can sign the
descriptor update revoking the compromised key without
relying on the compromised key itself. Consumers who
have the offline key in their trust set accept the
update; consumers who do not must perform out-of-band
trust-anchor refresh per §6.5.2.

> [!INFORMATIVE]
> The offline key is operational defence-in-depth. The
> spec recommends but does not mandate it because the
> implementation question (HSM, air-gapped machine,
> threshold custody) is operator-discretion. Future
> versions of this specification may make it
> mandatory.

## Compromised keys

A key SHOULD be considered compromised if its private
material may have been obtained by an unauthorised party.

A compromised key MUST be marked `revoked` in the
repository's signing key list immediately upon discovery
per the descriptor schema in §6.1.4. Consumers that have
fetched the updated descriptor MUST reject signatures
from the revoked key regardless of cryptographic
validity. Packages signed with the compromised key
SHOULD be re-signed with a fresh key, and the affected
package versions SHOULD be re-published with new
revisions.

The `revoked` status is the in-band revocation channel
this specification defines. It defends against
compromise at the descriptor-update granularity: a
consumer that successfully refreshes the descriptor
learns of revocation immediately. Consumers caching
older descriptors retain trust in the revoked key until
they re-sync, which is bounded by the maximum trusted
age (§6.5.4) and the descriptor signature, which is
itself produced by a still-active key.

> [!INFORMATIVE]
> A more sophisticated out-of-band revocation mechanism
> (signed revocation lists, key transparency logs) is
> reserved for a future version of this specification.
> The combination of `revoked` status (§6.1.4),
> maximum trusted age (§6.5.4), and signed descriptor
> updates closes the practical compromise-response
> window without requiring a separate revocation
> infrastructure in v0.22.

## Private key handling

Private key material is not the concern of this
specification. Best practices for private key generation,
storage, custody, and rotation are operational concerns of
the repository operator.

> [!INFORMATIVE]
> Hardware security modules, threshold signing schemes, and
> other key-protection mechanisms are compatible with
> peipkg signing as long as the resulting signature
> conforms to the on-wire envelope format. The
> specification cares only about the bytes, not how they
> were produced.
