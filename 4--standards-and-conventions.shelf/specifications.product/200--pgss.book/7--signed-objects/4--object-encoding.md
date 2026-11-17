---
title: Object Encoding
description: The 6-byte header every object begins with, how an object is
  hashed and signed with SHA-512 and ML-DSA, the two key types, and the
  rule that the issuer's key decides the algorithm.
---

Every object is a sequence of fields in a fixed order with no padding.
No field is optional. Where a field's size varies, a length precedes it.

## The header

Every object begins with these 6 bytes.

| Field | Type | Value |
|---|---|---|
| `magic` | `u8[3]` | `50 53 4f`, the ASCII bytes `PSO` |
| `kind` | `u8` | What the object is (§7.B) |
| `version` | `u8` | The format version. This chapter specifies `0x01`. |
| `reserved` | `u8` | `0x00` |

A verifier MUST treat an object whose `magic`, `version`, or `reserved`
differs from these values as malformed, and MUST treat an object as
malformed if its `kind` is not the kind the context calls for.

## Malformed objects

An object is **malformed** if it does not decode exactly as its layout
gives: a field out of its permitted range, a length that runs past the
end of the object, a reserved bit that is set, or any byte after the
last field. A verifier MUST NOT repair, truncate, or reinterpret a
malformed object.

## Hashes

Every hash in this chapter is SHA-512 (FIPS 180-4), 64 bytes, carried as
raw bytes.

The **object hash** of an object is the hash of all of its bytes, from
the first byte of the header through the last byte of its signature.

The **key hash** of a key is the hash of its key type byte followed by
the key's bytes.

Where a hash names a file in the trust store or in a directory of
certificates, the name is the hash in lowercase hexadecimal, 128
characters.

## Keys

A key is a key type and the raw public key that the type implies.

| Key type | Algorithm | Public key | Signature |
|---|---|---|---|
| `0x01` | ML-DSA-65 | 1952 bytes | 3309 bytes |
| `0x02` | ML-DSA-87 | 2592 bytes | 4627 bytes |

The enumeration is closed (§7.15). A public key is the raw encoding of
FIPS 204, with no wrapper.

## Signatures

A signature is the last field of the object it signs, and covers every
byte of the object before it, the header included.

```text
ML-DSA.Sign(private_key, bytes_before_signature, ctx = "")
```

This is pure ML-DSA, FIPS 204 Algorithm 2, with an empty context string.
An authority MUST NOT use the pre-hashing variant and MUST NOT set a
context.

**The issuer's key decides the algorithm.** A signed object does not
name the algorithm of its own signature. A verifier takes the algorithm,
and so the length of the signature field, from the key type of the
issuer the object names. A verifier MUST NOT take either from anything
in the object being verified.

> [!NOTE]
> The header is inside the signed bytes, and it carries the object's
> kind. A signature made over a leaf therefore cannot be presented as a
> signature over a certificate or a revocation: the bytes differ at
> offset 3. This is what separates the uses of one key, and it is why
> the context string can be left empty.
