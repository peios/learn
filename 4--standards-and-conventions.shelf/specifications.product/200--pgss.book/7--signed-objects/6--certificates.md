---
title: Certificates
description: The layout of a certificate, the two roles a certificate can
  have, what its issuer field names in each, and the rules on its subject
  name and key.
---

A certificate binds a key to a name and a set of warrants. Top-levels
and intermediaries share one layout.

| Field | Type | Description |
|---|---|---|
| header | 6 bytes | `kind` is `0x01` (§7.4) |
| `role` | `u8` | `0x01` for a top-level, `0x02` for an intermediary |
| `issuer` | `u8[64]` | The issuer (§7.3) |
| `name_len` | `u8` | Length of `name`, from 1 through 255 |
| `name` | `u8[name_len]` | The subject's name |
| `key_type` | `u8` | The type of `key` (§7.4) |
| `key` | By `key_type` | The subject's public key |
| `warrant_count` | `u8` | The number of warrants |
| `warrants` | Variable | That many warrants (§7.5) |
| `signature` | By the issuer's key type | Signature over every preceding byte |

The `role` enumeration is closed (§7.15).

## Name

A certificate's `name` describes its holder to a person, as
`Example Corporation Signing 1`. It holds bytes in the range `0x20`
through `0x7E`. No rule of this chapter compares it with anything, and a
consumer MUST NOT make a decision on it.

> [!NOTE]
> The name is chosen by whoever made the certificate. What a signer can
> sign as is decided by its `Name` warrant, which its issuer bounded,
> and never by what its certificate calls itself.

## Issuer and signature

For an intermediary, `issuer` is the object hash of the issuing
certificate, and the signature verifies under that certificate's key.

For a top-level, `issuer` is one of two things:

- **The key hash of a root.** The signature verifies under that root.
- **The key hash of the certificate's own key.** The certificate is
  **self-signed**, and the signature verifies under its own key.

A top-level whose `issuer` is neither a root the verifier holds nor its
own key hash was signed by a key the verifier does not have. A verifier
cannot check that signature, and treats the certificate as §7.14
describes.
