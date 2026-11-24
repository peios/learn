---
title: Algorithms
description: The key algorithms a key file can hold, and the SubjectPublicKeyInfo and PKCS #8 encodings each uses.
---

| `algorithm` | Key | Public key | Private key |
|---:|---|---|---|
| `1` | ECDSA over NIST P-256 | `id-ecPublicKey`, curve `secp256r1` (RFC 5480) | ECPrivateKey (RFC 5915) |
| `2` | ECDSA over NIST P-384 | `id-ecPublicKey`, curve `secp384r1` (RFC 5480) | ECPrivateKey (RFC 5915) |
| `3` | RSA, 2048-bit modulus | `rsaEncryption` (RFC 8017) | RSAPrivateKey (RFC 8017) |
| `4` | RSA, 3072-bit modulus | `rsaEncryption` (RFC 8017) | RSAPrivateKey (RFC 8017) |
| `5` | RSA, 4096-bit modulus | `rsaEncryption` (RFC 8017) | RSAPrivateKey (RFC 8017) |

`public_key` is the key's DER `SubjectPublicKeyInfo` (RFC 5280), with
the algorithm identifier the table names. An elliptic-curve public key
is the uncompressed point. A writer MUST write the canonical DER
encoding, so that one key always has one encoding.

The private key is a version 1 PKCS #8 `PrivateKeyInfo` (RFC 5208)
carrying the key's own private-key structure from the table, with the
same algorithm identifier as `public_key`.

An RSA key's `algorithm` is fixed by the length of its modulus: an RSA
key of any other size can't be held in a version 1 key file.

> [!NOTE]
> A new algorithm takes the next free value. A version 1 reader refuses
> a value it doesn't know, so adding one never changes how an existing
> key file is read.
